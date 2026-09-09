"""Bounded same-byte captures for EP19 bookkeeping decisions.

Every file capture is made through one descriptor with stat/read/stat and a
final path identity check.  Hashes, parsing input and projections all consume
the returned ``raw`` bytes; callers must never refill an older capture.
"""
from __future__ import annotations

from pathlib import Path
import base64
import hashlib
import json
import os
import stat
import time

FIELDS = ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid", "st_size",
          "st_mtime_ns", "st_ctime_ns", "st_nlink")
MAX_STABLE_ATTEMPTS = 3
MAX_STABLE_SECONDS = 5.0
READ_CHUNK = 1024 * 1024


class CaptureError(RuntimeError):
    pass


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
    failures = []
    for attempt in range(1, attempts + 1):
        if time.monotonic() - started > max_seconds:
            break
        fd = None
        try:
            before = os.lstat(path)
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
                raise CaptureError("NOT_REGULAR_OR_SYMLINK")
            if before.st_nlink != 1:
                raise CaptureError("LINK_COUNT_NOT_ONE")
            if max_bytes is not None and before.st_size > max_bytes:
                raise CaptureError("CAPTURE_BYTE_LIMIT_EXCEEDED")
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
            if metadata(before) != metadata(os.fstat(fd)):
                raise CaptureError("PATH_BINDING_CHANGED")
            if hook:
                hook("opened", path, attempt)
            chunks = []
            total = 0
            while True:
                chunk = os.read(fd, READ_CHUNK)
                if not chunk:
                    break
                total += len(chunk)
                if max_bytes is not None and total > max_bytes:
                    raise CaptureError("CAPTURE_BYTE_LIMIT_EXCEEDED")
                chunks.append(chunk)
                if hook:
                    hook("read", path, attempt)
            raw = b"".join(chunks)
            after_fd = os.fstat(fd)
            after_path = os.lstat(path)
            if metadata(before) != metadata(after_fd) or metadata(before) != metadata(after_path):
                raise CaptureError("CAPTURE_UNSTABLE")
            if len(raw) != before.st_size:
                raise CaptureError("CAPTURE_SIZE_MISMATCH")
            if time.monotonic() - started > max_seconds:
                raise CaptureError("CAPTURE_TIME_LIMIT_EXCEEDED")
            meta = metadata(before)
            raw_hash = sha256(raw)
            source_id = _source_id(path, raw_hash, meta)
            capture_id = sha256((source_id + ":" + str(time.time_ns())).encode())
            return {"path": str(path), "raw": raw, "sha256": raw_hash,
                    "metadata": meta, "source_id": source_id,
                    "capture_id": capture_id, "attempt": attempt,
                    "stable_protocol": "same-fd-stat-read-stat-plus-path-stat"}
        except (OSError, CaptureError) as exc:
            failures.append(f"{type(exc).__name__}:{exc}")
            if isinstance(exc, CaptureError) and str(exc) in {
                    "NOT_REGULAR_OR_SYMLINK", "LINK_COUNT_NOT_ONE",
                    "CAPTURE_BYTE_LIMIT_EXCEEDED"}:
                break
        finally:
            if fd is not None:
                os.close(fd)
    raise CaptureError("STABLE_CAPTURE_FAILED " + " | ".join(failures))


def capture_directory(path):
    path = canonical(path)
    before = os.lstat(path)
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
        raise CaptureError("DIRECTORY_NOT_REGULAR_BINDING")
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        if _identity(before) != _identity(os.fstat(fd)):
            raise CaptureError("DIRECTORY_PATH_BINDING_CHANGED")
        names = sorted(os.listdir(fd))
        if sorted(os.listdir(fd)) != names:
            raise CaptureError("DIRECTORY_ENTRY_CAPTURE_UNSTABLE")
        after_fd = os.fstat(fd)
        after_path = os.lstat(path)
        if metadata(before) != metadata(after_fd) or metadata(before) != metadata(after_path):
            raise CaptureError("DIRECTORY_CAPTURE_UNSTABLE")
    finally:
        os.close(fd)
    meta = metadata(before)
    source = json.dumps({"path": str(path), "entries": names, "metadata": meta},
                        sort_keys=True, separators=(",", ":")).encode()
    return {"path": str(path), "entries": names, "metadata": meta,
            "source_id": sha256(source),
            "capture_id": sha256(source + str(time.time_ns()).encode())}


def capture_manifest(package, *, max_items=4096, deadline=None):
    package = canonical(package)
    if package.is_symlink() or not package.is_dir():
        raise CaptureError("PACKAGE_NOT_DIRECTORY")
    rows = []
    for directory, dirs, files in os.walk(package, followlinks=False):
        dirs.sort()
        files.sort()
        for name in dirs:
            if (Path(directory) / name).is_symlink():
                raise CaptureError("PACKAGE_SYMLINK_DIRECTORY")
        for name in files:
            path = (Path(directory) / name).absolute()
            if path.is_symlink():
                raise CaptureError("PACKAGE_SYMLINK_FILE")
            remaining = MAX_STABLE_SECONDS if deadline is None else deadline - time.monotonic()
            if remaining <= 0:
                raise CaptureError("CAPTURE_TIME_LIMIT_EXCEEDED")
            row = capture_file(path, max_seconds=min(MAX_STABLE_SECONDS, remaining))
            rows.append({"path": str(path), "sha256": row["sha256"]})
            if len(rows) > max_items:
                raise CaptureError("MANIFEST_ITEM_LIMIT_EXCEEDED")
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
