"""Exact event classifier and boundary reducer for approved bookkeeping V3."""
from __future__ import annotations

from pathlib import Path
import ctypes
import os
import select
import struct
import time

import bookkeeping_v3 as bk
import capture
import causal

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
    temps = [event for event in rows if event["category"] == "PENDING_USAGE_TEMP_EVENT"]
    usage_targets = [event for event in rows
                     if event["category"] == "PENDING_USAGE_EVENT" and event["mask"] == IN_MOVED_TO]
    for event in temps:
        if event.get("temp_metadata_reason"):
            reasons.append(event["temp_metadata_reason"])
    for event in usage_targets:
        paired = (event.get("cookie", 0) != 0 and
                  any(other["mask"] == IN_MOVED_FROM and
                      other.get("cookie") == event["cookie"] for other in temps))
        if not paired:
            reasons.append("USAGE_TARGET_RENAME_FROM_UNREGISTERED_SOURCE")
    for event in temps:
        if event["mask"] == IN_MOVED_FROM:
            paired = (event.get("cookie", 0) != 0 and
                      any(other.get("cookie") == event["cookie"] for other in usage_targets))
            if not paired:
                reasons.append("USAGE_TEMP_RENAME_OUTSIDE_TARGET")
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
        self.policy = dict(policy)
        seed_deadline = time.monotonic() + bk.LIMITS["capture_total_seconds_per_boundary_max"]
        self.acquisition_deadline = seed_deadline
        if "usage_baseline" not in self.policy:
            usage_stat = capture.guarded_call(seed_deadline, os.lstat, self.policy["paths"]["usage"])
            self.policy["usage_baseline"] = {"metadata": capture.metadata(usage_stat)}
        if "root_baseline" not in self.policy:
            root_stat = capture.guarded_call(seed_deadline, os.lstat, self.policy["root"])
            self.policy["root_baseline"] = {"metadata": capture.metadata(root_stat)}
        self.libc = ctypes.CDLL(None, use_errno=True)
        self.fd = capture.guarded_call(seed_deadline, self.libc.inotify_init1,
                                       os.O_NONBLOCK | os.O_CLOEXEC)
        if self.fd < 0:
            raise OSError(ctypes.get_errno(), "inotify_init1")
        self.watches = {}
        self.events = []
        self.errors = []
        self.closed = False
        self.shutdown_wds = set()
        try:
            roots = {Path(policy["root"])}
            from preservation import directory_inventory
            for binding in policy["eligible_map"].values():
                package = Path(binding["package"])
                directories, unused = directory_inventory(
                    package, deadline=seed_deadline, max_entries=bk.LIMITS["manifest_items_max"])
                roots.update(directories)
            for root in sorted(roots):
                self._add(root)
        except BaseException as primary:
            try:
                self.close()
            except BaseException as cleanup:
                causal.raise_composed("BOUNDARY_OBSERVER_CONSTRUCTOR_AND_CLEANUP_FAILURE",
                    primary,[("cleanup","BOUNDARY_OBSERVER_FD_CLOSE",cleanup)],
                    dimensions={"observer_preservation_failure":True},
                    primary_stage="BOUNDARY_OBSERVER_CONSTRUCTION")
            raise

    def bind_policy(self, policy):
        """Rebind the seed observer to the exact policy consumed by RunAdapter."""
        for key in ("root", "paths"):
            if self.policy.get(key) != policy.get(key):
                raise RuntimeError("OBSERVER_POLICY_BINDING_MISMATCH " + key)
        seeded = {name: row.get("package") for name, row in self.policy.get("eligible_map", {}).items()}
        rebound = {name: row.get("package") for name, row in policy.get("eligible_map", {}).items()}
        if seeded != rebound or any(not isinstance(row.get("manifest"), list)
                                    for row in policy.get("eligible_map", {}).values()):
            raise RuntimeError("OBSERVER_POLICY_BINDING_MISMATCH eligible_map_projection")
        if not all(key in policy for key in ("usage_baseline", "root_baseline")):
            raise RuntimeError("OBSERVER_POLICY_BASELINE_MISSING")
        self.policy = policy
        return self

    def _add(self, path):
        current = capture.guarded_call(self.acquisition_deadline, os.lstat, path)
        if __import__("stat").S_ISLNK(current.st_mode) or not __import__("stat").S_ISDIR(current.st_mode):
            raise RuntimeError("WATCH_ROOT_INVALID")
        wd = capture.guarded_call(self.acquisition_deadline, self.libc.inotify_add_watch,
                                  self.fd, os.fsencode(path), WATCH_MASK)
        if wd < 0:
            raise OSError(ctypes.get_errno(), "inotify_add_watch", str(path))
        self.watches[wd] = path

    def drain(self, wait_seconds=0, *, deadline=None):
        deadline = deadline or time.monotonic() + bk.LIMITS["capture_total_seconds_per_boundary_max"]
        try:
            if wait_seconds and not capture.guarded_call(
                    deadline, select.select, [self.fd], [], [], wait_seconds)[0]:
                return
        except capture.CaptureError:
            self.errors.append("EVENT_ACQUISITION_TIME_LIMIT_EXCEEDED")
            return
        while True:
            if time.monotonic() >= deadline:
                self.errors.append("EVENT_ACQUISITION_TIME_LIMIT_EXCEEDED")
                return
            try:
                data = capture.guarded_call(deadline, os.read, self.fd, 1024 * 1024)
            except BlockingIOError:
                return
            except capture.CaptureError:
                self.errors.append("EVENT_ACQUISITION_TIME_LIMIT_EXCEEDED")
                return
            if not data:
                self.errors.append("WATCH_EOF")
                return
            offset = 0
            while offset < len(data):
                if time.monotonic() >= deadline:
                    self.errors.append("EVENT_ACQUISITION_TIME_LIMIT_EXCEEDED")
                    return
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
                if mask & IN_IGNORED and wd in self.shutdown_wds:
                    self.shutdown_wds.discard(wd)
                    self.watches.pop(wd, None)
                    continue
                if mask & (IN_IGNORED | IN_UNMOUNT):
                    self.errors.append("WATCH_LOSS")
                if wd not in self.watches:
                    self.errors.append("UNKNOWN_WATCH")
                    continue
                path = self.watches[wd] / name if name else self.watches[wd]
                event = {"path": str(path), "mask": mask & ~IN_ISDIR,
                         "cookie": cookie, "observed_ns": time.monotonic_ns(),
                         "writer": "NOT_ESTABLISHED"}
                if path.parent == Path(self.policy["root"]) and bk.TEMP_RE.fullmatch(path.name):
                    if (mask & ~IN_ISDIR) in (IN_CREATE, IN_MODIFY, IN_ATTRIB, IN_CLOSE_WRITE):
                        try:
                            current = capture.guarded_call(deadline, os.lstat, path)
                            baseline_usage = self.policy["usage_baseline"]["metadata"]
                            baseline_root = self.policy["root_baseline"]["metadata"]
                            if (not __import__("stat").S_ISREG(current.st_mode) or
                                    __import__("stat").S_ISLNK(current.st_mode) or current.st_nlink != 1):
                                event["temp_metadata_reason"] = "USAGE_TEMP_LINK_OR_TYPE"
                            elif current.st_dev != baseline_root["st_dev"]:
                                event["temp_metadata_reason"] = "USAGE_TEMP_FILESYSTEM_BOUNDARY"
                            elif (current.st_uid != baseline_usage["st_uid"] or
                                  current.st_gid != baseline_usage["st_gid"] or
                                  __import__("stat").S_IMODE(current.st_mode) != 0o600):
                                event["temp_metadata_reason"] = "USAGE_TEMP_OWNER_GROUP_MODE"
                            else:
                                event["temp_metadata_validated"] = True
                        except FileNotFoundError:
                            event["temp_metadata_reason"] = "USAGE_TEMP_METADATA_UNAVAILABLE"
                        except OSError as exc:
                            event["temp_metadata_reason"] = "USAGE_TEMP_CAPTURE_ERROR:" + type(exc).__name__
                        except capture.CaptureError:
                            self.errors.append("EVENT_ACQUISITION_TIME_LIMIT_EXCEEDED")
                            return
                if len(self.events) >= bk.LIMITS["pending_events_max"]:
                    if "PENDING_EVENT_LIMIT_EXCEEDED_DURING_ACQUISITION" not in self.errors:
                        self.errors.append("PENDING_EVENT_LIMIT_EXCEEDED_DURING_ACQUISITION")
                    return
                self.events.append(event)

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

    def stop_and_drain(self, endpoint_ns):
        """End coverage after endpoint_ns, then consume every event queued before watch removal."""
        if self.closed:
            return endpoint_ns
        deadline = time.monotonic() + bk.LIMITS["capture_total_seconds_per_boundary_max"]
        self.shutdown_wds = set(self.watches)
        for wd in sorted(self.shutdown_wds):
            try:
                rc = capture.guarded_call(deadline, self.libc.inotify_rm_watch, self.fd, wd)
                if rc < 0:
                    raise OSError(ctypes.get_errno(), "inotify_rm_watch")
            except Exception as exc:
                self.errors.append("WATCH_SHUTDOWN_FAILED:" + type(exc).__name__)
                break
        while self.shutdown_wds and time.monotonic() < deadline:
            try:
                ready = capture.guarded_call(deadline, select.select, [self.fd], [], [], .01)[0]
            except capture.CaptureError:
                break
            if ready:
                self.drain(deadline=deadline)
        if self.shutdown_wds:
            self.errors.append("WATCH_SHUTDOWN_QUEUE_NOT_DRAINED")
        self.close()
        return endpoint_ns

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
