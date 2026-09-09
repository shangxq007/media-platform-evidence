"""Crash-conscious publication with explicit owned-resource composition."""
from pathlib import Path
from contextlib import contextmanager
import os
import stat
import causal


def _rows(error, role, stage):
    return causal.rows(error, role, stage, "durable-publication")


def _composed(label, primary, failures, *, evidence=True):
    """Raise one stable graph without hiding a primary or any release failure."""
    dimensions = {"evidence_persistence_failure": True} if evidence else {}
    causal.raise_composed(label, primary, failures, dimensions=dimensions,
                          primary_stage="BODY_OR_NATIVE")


def _attempt(failures, role, stage, function, *args):
    try:
        return function(*args)
    except BaseException as error:
        failures.append((role, stage, error))
        return None


def fsync_directory(path):
    fd = None; primary = None; failures = []
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
        os.fsync(fd)
    except BaseException as error:
        primary = error
    if fd is not None:
        _attempt(failures, "directory-fd-close", "DIRECTORY_FD_CLOSE", os.close, fd)
    _composed("DIRECTORY_FSYNC_AND_CLOSE_FAILURE", primary, failures)


def ensure_directory(path, mode=0o700):
    path = Path(path).absolute(); missing = []; cursor = path
    while not cursor.exists():
        missing.append(cursor); cursor = cursor.parent
    if cursor.is_symlink() or not cursor.is_dir():
        raise RuntimeError("DURABLE_DIRECTORY_ANCESTOR_INVALID")
    for directory in reversed(missing):
        os.mkdir(directory, mode)
        fsync_directory(directory.parent); fsync_directory(directory)
    if path.is_symlink() or not path.is_dir():
        raise RuntimeError("DURABLE_DIRECTORY_INVALID")
    return path


def exclusive_directory(path, mode=0o700):
    path = Path(path).absolute(); ensure_directory(path.parent, mode); os.mkdir(path, mode)
    failures = []
    _attempt(failures, "publishing-parent-fsync", "PUBLISHING_PARENT_FSYNC", fsync_directory, path.parent)
    _attempt(failures, "published-directory-fsync", "PUBLISHED_DIRECTORY_FSYNC", fsync_directory, path)
    _composed("DIRECTORY_PUBLICATION_FAILURE", None, failures)
    return path


def fsync_directory_chain(path, anchor):
    """Synchronize an existing task-local directory publication chain."""
    path = Path(path).absolute(); anchor = Path(anchor).absolute()
    if path != anchor and anchor not in path.parents:
        raise RuntimeError("DURABLE_DIRECTORY_CHAIN_OUTSIDE_ANCHOR")
    chain = [path]
    while chain[-1] != anchor: chain.append(chain[-1].parent)
    failures = []
    for directory in reversed(chain):
        if directory.is_symlink() or not directory.is_dir():
            failures.append(("directory-chain", "DIRECTORY_CHAIN_IDENTITY",
                             RuntimeError("DURABLE_DIRECTORY_CHAIN_INVALID " + str(directory))))
            continue
        _attempt(failures, "directory-chain-fsync", "DIRECTORY_CHAIN_FSYNC", fsync_directory, directory)
    _composed("DIRECTORY_CHAIN_PUBLICATION_FAILURE", None, failures)
    return path


def exclusive_bytes(path, payload, mode=0o400, directory_mode=0o700):
    path = Path(path).absolute(); ensure_directory(path.parent, directory_mode)
    fd = None; primary = None; failures = []
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
        view = memoryview(payload)
        while view:
            count = os.write(fd, view)
            if count <= 0: raise OSError("ZERO_DURABLE_WRITE")
            view = view[count:]
        os.fsync(fd)
    except BaseException as error:
        primary = error
    if fd is not None:
        _attempt(failures, "file-fd-close", "FILE_FD_CLOSE", os.close, fd)
    _attempt(failures, "publishing-parent-fsync", "PUBLISHING_PARENT_FSYNC", fsync_directory, path.parent)
    _composed("EXCLUSIVE_BYTES_BODY_AND_PUBLICATION_FAILURE", primary, failures)
    return path


def sync_existing_file(path):
    """Durably publish an existing regular file produced by a bound child."""
    path = Path(path).absolute(); fd = None; primary = None; failures = []
    try:
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        value = os.fstat(fd)
        if not stat.S_ISREG(value.st_mode) or value.st_nlink != 1:
            raise RuntimeError("DURABLE_EXISTING_FILE_INVALID")
        os.fsync(fd)
    except BaseException as error:
        primary = error
    if fd is not None:
        _attempt(failures, "existing-file-fd-close", "EXISTING_FILE_FD_CLOSE", os.close, fd)
    _attempt(failures, "publishing-parent-fsync", "PUBLISHING_PARENT_FSYNC", fsync_directory, path.parent)
    _composed("EXISTING_FILE_BODY_AND_PUBLICATION_FAILURE", primary, failures)
    return path


@contextmanager
def exclusive_stream(path, mode=0o400, directory_mode=0o700):
    """Attempt every owned stream/fd release and preserve all causal dimensions."""
    path = Path(path).absolute(); ensure_directory(path.parent, directory_mode)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    stream = None; primary = None; failures = []
    try:
        stream = os.fdopen(fd, "wb", closefd=False)
    except BaseException as error:
        primary = error
    if primary is None:
        try:
            yield stream
        except BaseException as error:
            primary = error
    if stream is not None:
        _attempt(failures, "stream-flush", "STREAM_FLUSH", stream.flush)
        _attempt(failures, "file-fsync", "FILE_FSYNC", os.fsync, fd)
        _attempt(failures, "stream-close", "STREAM_CLOSE", stream.close)
    _attempt(failures, "raw-fd-close", "RAW_FD_CLOSE", os.close, fd)
    _attempt(failures, "publishing-parent-fsync", "PUBLISHING_PARENT_FSYNC", fsync_directory, path.parent)
    _composed("EXCLUSIVE_STREAM_BODY_AND_CLEANUP_FAILURE", primary, failures)
