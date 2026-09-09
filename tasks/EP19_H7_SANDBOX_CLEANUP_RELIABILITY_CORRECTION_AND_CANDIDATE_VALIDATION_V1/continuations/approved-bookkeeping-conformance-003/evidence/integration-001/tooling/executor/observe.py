"""Exact event classifier and boundary reducer for approved bookkeeping V3."""
from __future__ import annotations

from pathlib import Path
import ctypes
import os
import select
import struct
import time

import bookkeeping_v3 as bk

IN_MODIFY = 0x00000002
IN_ATTRIB = 0x00000004
IN_CLOSE_WRITE = 0x00000008
IN_MOVED_FROM = 0x00000040
IN_MOVED_TO = 0x00000080
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200
IN_DELETE_SELF = 0x00000400
IN_MOVE_SELF = 0x00000800
IN_UNMOUNT = 0x00002000
IN_Q_OVERFLOW = 0x00004000
IN_IGNORED = 0x00008000
IN_ISDIR = 0x40000000
WATCH_MASK = (IN_MODIFY | IN_ATTRIB | IN_CLOSE_WRITE | IN_MOVED_FROM | IN_MOVED_TO |
              IN_CREATE | IN_DELETE | IN_DELETE_SELF | IN_MOVE_SELF)


def classify_event(policy, path, mask, cookie=0):
    path = str(Path(path))
    paths = policy["paths"]
    if path == paths["lock"]:
        return ("PENDING_EXACT_EMPTY_USAGE_LOCK_CLOSE_WRITE" if mask == IN_CLOSE_WRITE and cookie == 0
                else "REJECT_LOCK_EVENT")
    if path == paths["ledger"]:
        return ("PENDING_LEDGER_EVENT" if mask in (IN_MODIFY, IN_CLOSE_WRITE) and cookie == 0
                else "REJECT_LEDGER_EVENT")
    if path == paths["usage"]:
        if cookie != 0 and mask not in (IN_MOVED_TO,):
            return "REJECT_USAGE_EVENT"
        return ("PENDING_USAGE_EVENT" if mask in (IN_MODIFY, IN_CLOSE_WRITE, IN_MOVED_TO)
                else "REJECT_USAGE_EVENT")
    candidate = Path(path)
    root = Path(policy["root"])
    if candidate.parent == root and bk.TEMP_RE.fullmatch(candidate.name):
        return ("PENDING_USAGE_TEMP_EVENT" if mask in (IN_MODIFY, IN_ATTRIB, IN_CLOSE_WRITE, IN_CREATE, IN_DELETE, IN_MOVED_FROM)
                else "REJECT_USAGE_TEMP_EVENT")
    for binding in policy["eligible_map"].values():
        if candidate == Path(binding["package"]) or candidate.is_relative_to(Path(binding["package"])):
            return "REJECT_STRICT_PACKAGE_EVENT"
    if candidate == root or candidate.is_relative_to(root):
        return "REJECT_UNAPPROVED_SKILLS_EVENT"
    return "REJECT_OUTSIDE_BOUND_EVENT"


def classify(policy, events):
    result = []
    for raw in events:
        event = dict(raw)
        event.setdefault("cookie", 0)
        event["category"] = classify_event(policy, event["path"], event["mask"], event["cookie"])
        event.setdefault("writer", "NOT_ESTABLISHED")
        result.append(event)
    return result


def reduce_events(policy, events, *, ledger_growth, usage_variation=False,
                  require_usage_event=True, coverage_errors=(), semantic_reasons=()):
    """Resolve every event at one command/gate boundary; no pending crosses it."""
    if len(events) > bk.LIMITS["pending_events_max"]:
        return {"result": "REJECT", "events": classify(policy, events),
                "reasons": ["PENDING_EVENT_LIMIT_EXCEEDED"], "unresolved": len(events)}
    rows = classify(policy, events)
    reasons = list(coverage_errors) + list(semantic_reasons)
    for event in rows:
        if event["category"].startswith("REJECT"):
            reasons.append(event["category"])
    ledger = [event for event in rows if event["category"] == "PENDING_LEDGER_EVENT"]
    lock = [event for event in rows if event["category"] == "PENDING_EXACT_EMPTY_USAGE_LOCK_CLOSE_WRITE"]
    usage = [event for event in rows if event["category"] in ("PENDING_USAGE_EVENT", "PENDING_USAGE_TEMP_EVENT")]
    if usage_variation and require_usage_event and not usage:
        reasons.append("USAGE_VARIATION_WITHOUT_COVERED_EVENT")
    if ledger_growth:
        if not any(event["mask"] == IN_MODIFY for event in ledger):
            reasons.append("LEDGER_GROWTH_WITHOUT_MODIFY_EVENT")
        if not any(event["mask"] == IN_CLOSE_WRITE for event in ledger):
            reasons.append("LEDGER_GROWTH_WITHOUT_CLOSE_WRITE_EVENT")
    elif any(event["mask"] == IN_MODIFY for event in ledger):
        reasons.append("LEDGER_MODIFY_WITHOUT_GROWTH")
    for event in ledger:
        event["category"] = ("ACCEPTED_LEDGER_PENDING_RESOLVED" if not reasons
                             else "REJECT_LEDGER_PENDING_UNRESOLVED")
    for event in lock:
        event["category"] = ("ACCEPTED_EXACT_EMPTY_LOCK_CLOSE_WRITE" if not reasons
                             else "REJECT_LOCK_PENDING_UNRESOLVED")
    for event in usage:
        event["category"] = ("ACCEPTED_USAGE_V2_EVENT" if not reasons
                             else "REJECT_USAGE_PENDING_UNRESOLVED")
    unresolved = sum(1 for event in rows if event["category"].startswith("PENDING"))
    if unresolved:
        reasons.append("UNRESOLVED_PENDING_EVENTS")
    return {"result": "PASS" if not reasons else "REJECT", "events": rows,
            "reasons": sorted(set(reasons)), "unresolved": unresolved}


class BoundaryObserver:
    """Task-private Linux inotify stream. It never attributes or signals a process."""
    def __init__(self, policy):
        self.policy = policy
        self.libc = ctypes.CDLL(None, use_errno=True)
        self.fd = self.libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
        if self.fd < 0:
            raise OSError(ctypes.get_errno(), "inotify_init1")
        self.watches = {}
        self.events = []
        self.errors = []
        self.closed = False
        roots = {Path(policy["root"])}
        for binding in policy["eligible_map"].values():
            package = Path(binding["package"])
            for directory, dirs, unused in os.walk(package, followlinks=False):
                dirs.sort()
                roots.add(Path(directory))
        try:
            for root in sorted(roots):
                self._add(root)
        except BaseException:
            self.close()
            raise

    def _add(self, path):
        if path.is_symlink() or not path.is_dir():
            raise RuntimeError("WATCH_ROOT_INVALID")
        wd = self.libc.inotify_add_watch(self.fd, os.fsencode(path), WATCH_MASK)
        if wd < 0:
            raise OSError(ctypes.get_errno(), "inotify_add_watch", str(path))
        self.watches[wd] = path

    def drain(self, wait_seconds=0):
        if wait_seconds and not select.select([self.fd], [], [], wait_seconds)[0]:
            return
        while True:
            try:
                data = os.read(self.fd, 1024 * 1024)
            except BlockingIOError:
                return
            if not data:
                self.errors.append("WATCH_EOF")
                return
            offset = 0
            while offset < len(data):
                if offset + 16 > len(data):
                    self.errors.append("MALFORMED_EVENT")
                    return
                wd, mask, cookie, length = struct.unpack_from("iIII", data, offset)
                offset += 16
                if offset + length > len(data):
                    self.errors.append("MALFORMED_EVENT")
                    return
                name = os.fsdecode(data[offset:offset + length].split(b"\0", 1)[0])
                offset += length
                if mask & IN_Q_OVERFLOW:
                    self.errors.append("QUEUE_OVERFLOW")
                    continue
                if mask & (IN_IGNORED | IN_UNMOUNT):
                    self.errors.append("WATCH_LOSS")
                if wd not in self.watches:
                    self.errors.append("UNKNOWN_WATCH")
                    continue
                path = self.watches[wd] / name if name else self.watches[wd]
                self.events.append({"path": str(path), "mask": mask & ~IN_ISDIR,
                                    "cookie": cookie, "observed_ns": time.monotonic_ns(),
                                    "writer": "NOT_ESTABLISHED"})

    def boundary_events(self):
        self.drain(.05)
        events = self.events
        self.events = []
        errors = self.errors
        self.errors = []
        return events, errors

    def close(self):
        if not self.closed:
            os.close(self.fd)
            self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
