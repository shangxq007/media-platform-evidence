"""Bounded same-byte captures for EP19 bookkeeping decisions.

Every file capture is made through one descriptor with stat/read/stat and a
final path identity check.  Hashes, parsing input and projections all consume
the returned ``raw`` bytes; callers must never refill an older capture.
"""
from __future__ import annotations

from pathlib import Path
from contextlib import contextmanager
import base64
import hashlib
import json
import os
import stat
import time
import signal
import threading
import causal

FIELDS = ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid", "st_size",
          "st_mtime_ns", "st_ctime_ns", "st_nlink")
MAX_STABLE_ATTEMPTS = 3
MAX_STABLE_SECONDS = 5.0
READ_CHUNK = 1024 * 1024


class CaptureError(RuntimeError):
    pass


def _raise_resource(label, primary, cleanup, stage):
    failures = [] if cleanup is None else [("cleanup", stage + "_CLEANUP", cleanup)]
    causal.raise_composed(label, primary, failures,
                          dimensions={"observer_preservation_failure": True},
                          primary_stage=stage)


@contextmanager
def _deadline_guard(seconds):
    """Interrupt a blocking acquisition syscall on the main Unix thread."""
    if seconds <= 0:
        raise CaptureError("CAPTURE_TIME_LIMIT_EXCEEDED")
    if threading.current_thread() is not threading.main_thread() or not hasattr(signal, "setitimer"):
        raise CaptureError("CONTROLLED_ACQUISITION_UNAVAILABLE")
    entered = time.monotonic()
    prior_handler = signal.getsignal(signal.SIGALRM)
    prior_timer = signal.getitimer(signal.ITIMER_REAL)
    def expired(signum, frame):
        raise CaptureError("CAPTURE_TIME_LIMIT_EXCEEDED_DURING_ACQUISITION")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, prior_handler)
        if prior_timer[0] > 0:
            remaining = prior_timer[0] - (time.monotonic() - entered)
            signal.setitimer(signal.ITIMER_REAL, max(remaining, 1e-6), prior_timer[1])


def _remaining(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise CaptureError("CAPTURE_TIME_LIMIT_EXCEEDED")
    return remaining


def guarded_call(deadline, function, *args, **kwargs):
    """Run one acquisition syscall under the shared absolute deadline."""
    with _deadline_guard(_remaining(deadline)):
        return function(*args, **kwargs)


def _bounded_names(fd, *, deadline, max_entries):
    """Incremental readdir: reject before retaining entry max_entries + 1."""
    if isinstance(max_entries, bool) or not isinstance(max_entries, int) or max_entries < 1:
        raise CaptureError("DIRECTORY_ENTRY_LIMIT_INVALID")
    iterator = guarded_call(deadline, os.scandir, fd)
    names = []
    primary = None
    try:
        while True:
            try:
                entry = guarded_call(deadline, next, iterator)
            except StopIteration:
                break
            if len(names) >= max_entries:
                raise CaptureError("DIRECTORY_ENTRY_LIMIT_EXCEEDED")
            names.append(entry.name)
    except BaseException as error:
        primary = error
    cleanup = None
    try: iterator.close()
    except BaseException as error: cleanup = error
    _raise_resource("DIRECTORY_ITERATION_AND_CLOSE_FAILURE", primary, cleanup, "DIRECTORY_ITERATION")
    names.sort()
    return names


def metadata(value):
    return {name: getattr(value, name) for name in FIELDS}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(path):
    value = Path(path)
    if not value.is_absolute() or ".." in value.parts or str(value) != os.path.normpath(str(value)):
        raise CaptureError("NONCANONICAL_PATH")
    return value


def _identity(value):
    return value.st_dev, value.st_ino, value.st_mode


def _source_id(path, raw_hash, meta):
    value = json.dumps({"path": str(path), "sha256": raw_hash, "metadata": meta},
                       sort_keys=True, separators=(",", ":")).encode()
    return sha256(value)


def capture_file(path, *, max_bytes=None, attempts=MAX_STABLE_ATTEMPTS,
                 max_seconds=MAX_STABLE_SECONDS, hook=None):
    """Return one real stable byte source, bounded to three reads/five seconds."""
    path = canonical(path)
    if isinstance(attempts, bool) or not isinstance(attempts, int) or not 1 <= attempts <= MAX_STABLE_ATTEMPTS:
        raise CaptureError("STABLE_CAPTURE_ATTEMPT_LIMIT_INVALID")
    if max_seconds <= 0 or max_seconds > MAX_STABLE_SECONDS:
        raise CaptureError("STABLE_CAPTURE_TIME_LIMIT_INVALID")
    started = time.monotonic()
    deadline = started + max_seconds
    failures = []
    for attempt in range(1, attempts + 1):
        if time.monotonic() - started > max_seconds:
            break
        fd = None; candidate = None; attempt_error = None; terminal = False
        retryable = False
        try:
            before = guarded_call(deadline, os.lstat, path)
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
                raise CaptureError("NOT_REGULAR_OR_SYMLINK")
            if before.st_nlink != 1:
                raise CaptureError("LINK_COUNT_NOT_ONE")
            if max_bytes is not None and before.st_size > max_bytes:
                raise CaptureError("CAPTURE_BYTE_LIMIT_EXCEEDED")
            fd = guarded_call(deadline, os.open, path,
                              os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
            if metadata(before) != metadata(guarded_call(deadline, os.fstat, fd)):
                raise CaptureError("PATH_BINDING_CHANGED")
            if hook:
                hook("opened", path, attempt)
            chunks = []
            total = 0
            while True:
                chunk = guarded_call(deadline, os.read, fd, READ_CHUNK)
                if not chunk:
                    break
                total += len(chunk)
                if max_bytes is not None and total > max_bytes:
                    raise CaptureError("CAPTURE_BYTE_LIMIT_EXCEEDED")
                chunks.append(chunk)
                if hook:
                    guarded_call(deadline, hook, "read", path, attempt)
            raw = b"".join(chunks)
            after_fd = guarded_call(deadline, os.fstat, fd)
            after_path = guarded_call(deadline, os.lstat, path)
            if metadata(before) != metadata(after_fd) or metadata(before) != metadata(after_path):
                raise CaptureError("CAPTURE_UNSTABLE")
            if len(raw) != before.st_size:
                raise CaptureError("CAPTURE_SIZE_MISMATCH")
            _remaining(deadline)
            meta = metadata(before)
            raw_hash = sha256(raw)
            source_id = _source_id(path, raw_hash, meta)
            capture_id = sha256((source_id + ":" + str(time.time_ns())).encode())
            candidate = {"path": str(path), "raw": raw, "sha256": raw_hash,
                         "metadata": meta, "source_id": source_id,
                         "capture_id": capture_id, "attempt": attempt,
                         "stable_protocol": "same-fd-stat-read-stat-plus-path-stat"}
        except BaseException as exc:
            attempt_error = exc
            retryable = isinstance(exc, (OSError, CaptureError))
            if retryable:
                failures.append(f"{type(exc).__name__}:{exc}")
                if isinstance(exc, CaptureError) and str(exc) in {
                        "NOT_REGULAR_OR_SYMLINK", "LINK_COUNT_NOT_ONE",
                        "CAPTURE_BYTE_LIMIT_EXCEEDED"}:
                    terminal = True
        finally:
            cleanup = None
            if fd is not None:
                try: os.close(fd)
                except BaseException as error: cleanup = error
        if cleanup is not None:
            _raise_resource("FILE_CAPTURE_AND_FD_CLOSE_FAILURE", attempt_error, cleanup, "FILE_CAPTURE")
        if attempt_error is not None and not retryable:
            raise attempt_error
        if candidate is not None: return candidate
        if terminal: break
    raise CaptureError("STABLE_CAPTURE_FAILED " + " | ".join(failures))


def capture_directory(path, *, deadline=None, max_entries=4096):
    path = canonical(path)
    deadline = time.monotonic() + MAX_STABLE_SECONDS if deadline is None else deadline
    before = guarded_call(deadline, os.lstat, path)
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
        raise CaptureError("DIRECTORY_NOT_REGULAR_BINDING")
    fd = guarded_call(deadline, os.open, path,
                      os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    primary = None
    try:
        if _identity(before) != _identity(guarded_call(deadline, os.fstat, fd)):
            raise CaptureError("DIRECTORY_PATH_BINDING_CHANGED")
        names = _bounded_names(fd, deadline=deadline, max_entries=max_entries)
        repeated = _bounded_names(fd, deadline=deadline, max_entries=max_entries)
        if repeated != names:
            raise CaptureError("DIRECTORY_ENTRY_CAPTURE_UNSTABLE")
        after_fd = guarded_call(deadline, os.fstat, fd)
        after_path = guarded_call(deadline, os.lstat, path)
        if metadata(before) != metadata(after_fd) or metadata(before) != metadata(after_path):
            raise CaptureError("DIRECTORY_CAPTURE_UNSTABLE")
    except BaseException as error:
        primary = error
    cleanup = None
    try: os.close(fd)
    except BaseException as error: cleanup = error
    _raise_resource("DIRECTORY_CAPTURE_AND_FD_CLOSE_FAILURE", primary, cleanup, "DIRECTORY_CAPTURE")
    meta = metadata(before)
    source = json.dumps({"path": str(path), "entries": names, "metadata": meta},
                        sort_keys=True, separators=(",", ":")).encode()
    return {"path": str(path), "entries": names, "metadata": meta,
            "source_id": sha256(source),
            "capture_id": sha256(source + str(time.time_ns()).encode())}


def capture_manifest(package, *, max_items=4096, deadline=None):
    package = canonical(package)
    deadline = time.monotonic() + MAX_STABLE_SECONDS if deadline is None else deadline
    package_stat = guarded_call(deadline, os.lstat, package)
    invalid = stat.S_ISLNK(package_stat.st_mode) or not stat.S_ISDIR(package_stat.st_mode)
    if invalid:
        raise CaptureError("PACKAGE_NOT_DIRECTORY")
    rows = []
    pending = [package]
    directories_seen = 0
    while pending:
        directory = pending.pop()
        directories_seen += 1
        if directories_seen > max_items:
            raise CaptureError("MANIFEST_DIRECTORY_LIMIT_EXCEEDED")
        names = capture_directory(directory, deadline=deadline, max_entries=max_items)["entries"]
        children = []
        for name in names:
            path = (directory / name).absolute()
            current = guarded_call(deadline, os.lstat, path)
            if stat.S_ISLNK(current.st_mode):
                raise CaptureError("PACKAGE_SYMLINK_ENTRY")
            if stat.S_ISDIR(current.st_mode):
                children.append(path)
            elif stat.S_ISREG(current.st_mode):
                if len(rows) >= max_items:
                    raise CaptureError("MANIFEST_ITEM_LIMIT_EXCEEDED")
                row = capture_file(path, attempts=1, max_seconds=min(MAX_STABLE_SECONDS,
                                                                       _remaining(deadline)))
                rows.append({"path": str(path), "sha256": row["sha256"]})
            else:
                raise CaptureError("PACKAGE_SPECIAL_ENTRY")
        pending.extend(reversed(children))
    rows.sort(key=lambda item: item["path"])
    if not rows or str(package / "SKILL.md") not in {item["path"] for item in rows}:
        raise CaptureError("PACKAGE_MANIFEST_EMPTY_OR_SKILL_MISSING")
    return rows


def private_projection(row):
    return {**{key: value for key, value in row.items() if key != "raw"},
            "raw_base64": base64.b64encode(row["raw"]).decode("ascii")}


def public_projection(row):
    return {key: row[key] for key in ("path", "sha256", "metadata", "source_id",
                                      "capture_id", "attempt", "stable_protocol")}
