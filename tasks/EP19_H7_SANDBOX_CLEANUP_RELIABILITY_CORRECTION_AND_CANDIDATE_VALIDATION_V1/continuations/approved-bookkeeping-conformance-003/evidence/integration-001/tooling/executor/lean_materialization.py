"""Strict, link-aware Lean distribution materialization.

The formal collector intentionally rejects links.  This module validates every
source entry without following links during enumeration, resolves each link
chain explicitly inside the selected root, and writes independent regular
files into the run-local cache.  It never changes the collector policy.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import os
import stat
import time


CHUNK = 1024 * 1024


class MaterializationError(RuntimeError):
    pass


def _inside(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _canonical_root(root: Path) -> Path:
    root = Path(root).absolute()
    if root != Path(os.path.normpath(str(root))):
        raise MaterializationError("NONCANONICAL_ROOT")
    st = os.lstat(root)
    if not stat.S_ISDIR(st.st_mode) or stat.S_ISLNK(st.st_mode):
        raise MaterializationError("ROOT_NOT_REAL_DIRECTORY")
    try:
        resolved = root.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise MaterializationError("ROOT_ANCESTOR_RESOLUTION_FAILED") from exc
    if resolved != root:
        raise MaterializationError("ROOT_OR_ANCESTOR_SYMLINK " + str(root))
    return root


def _sha256_regular(path: Path) -> tuple[str, int, os.stat_result]:
    before = os.lstat(path)
    if not stat.S_ISREG(before.st_mode):
        raise MaterializationError("NOT_REGULAR_FILE " + str(path))
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        opened = os.fstat(fd)
        if (before.st_dev, before.st_ino, before.st_mode, before.st_size) != (
            opened.st_dev, opened.st_ino, opened.st_mode, opened.st_size
        ):
            raise MaterializationError("FILE_REPLACED_BEFORE_READ " + str(path))
        digest = hashlib.sha256()
        length = 0
        while True:
            block = os.read(fd, CHUNK)
            if not block:
                break
            digest.update(block)
            length += len(block)
        after = os.fstat(fd)
        bound = os.lstat(path)
        wanted = (before.st_dev, before.st_ino, before.st_mode, before.st_size,
                  before.st_mtime_ns, before.st_ctime_ns)
        if wanted != (after.st_dev, after.st_ino, after.st_mode, after.st_size,
                      after.st_mtime_ns, after.st_ctime_ns):
            raise MaterializationError("FILE_CHANGED_DURING_READ " + str(path))
        if wanted != (bound.st_dev, bound.st_ino, bound.st_mode, bound.st_size,
                      bound.st_mtime_ns, bound.st_ctime_ns):
            raise MaterializationError("FILE_BINDING_CHANGED " + str(path))
        if length != before.st_size:
            raise MaterializationError("FILE_LENGTH_MISMATCH " + str(path))
        return digest.hexdigest(), length, before
    finally:
        os.close(fd)


def resolve_link_chain(root: Path, link: Path) -> tuple[Path, list[dict]]:
    """Resolve all components explicitly; reject cycle, missing, escape, special."""
    root = _canonical_root(root)
    current = Path(os.path.normpath(str(Path(link).absolute())))
    if not _inside(root, current):
        raise MaterializationError("LINK_START_OUTSIDE_ROOT")
    seen: set[tuple[int, int]] = set()
    chain: list[dict] = []
    while True:
        relative = current.relative_to(root)
        cursor = root
        parts = list(relative.parts)
        restarted = False
        for index, component in enumerate(parts):
            cursor = cursor / component
            try:
                row = os.lstat(cursor)
            except FileNotFoundError as exc:
                raise MaterializationError("LINK_TARGET_MISSING " + str(cursor)) from exc
            if stat.S_ISLNK(row.st_mode):
                identity = (row.st_dev, row.st_ino)
                if identity in seen:
                    raise MaterializationError("LINK_CYCLE " + str(cursor))
                seen.add(identity)
                target = os.readlink(cursor)
                candidate = Path(target) if os.path.isabs(target) else cursor.parent / target
                if index + 1 < len(parts):
                    candidate = candidate.joinpath(*parts[index + 1:])
                candidate = Path(os.path.normpath(str(candidate)))
                chain.append({
                    "link": str(cursor.relative_to(root)),
                    "target": target,
                    "next": str(candidate),
                    "dev": row.st_dev,
                    "ino": row.st_ino,
                })
                if not _inside(root, candidate):
                    raise MaterializationError("LINK_ESCAPES_ROOT " + str(cursor))
                current = candidate
                restarted = True
                break
            if index < len(parts) - 1 and not stat.S_ISDIR(row.st_mode):
                raise MaterializationError("LINK_INTERMEDIATE_NOT_DIRECTORY " + str(cursor))
        if restarted:
            continue
        final = os.lstat(current)
        if not stat.S_ISREG(final.st_mode):
            raise MaterializationError("LINK_TARGET_NOT_REGULAR " + str(current))
        return current, chain


def _mode(row: os.stat_result) -> str:
    return format(stat.S_IMODE(row.st_mode), "04o")


def inspect_tree(root: Path, *, allow_file_links: bool) -> dict:
    root = _canonical_root(root)
    directories: list[dict] = []
    files: list[dict] = []
    links: list[dict] = []
    specials: list[dict] = []
    inode_owners: dict[tuple[int, int], str] = {}
    aliases: list[list[str]] = []

    def own(path: Path, row: os.stat_result) -> None:
        key = (row.st_dev, row.st_ino)
        rel = "." if path == root else str(path.relative_to(root))
        if key in inode_owners:
            aliases.append([inode_owners[key], rel])
        else:
            inode_owners[key] = rel

    def visit(directory: Path) -> None:
        before = os.lstat(directory)
        if not stat.S_ISDIR(before.st_mode) or stat.S_ISLNK(before.st_mode):
            raise MaterializationError("ENUMERATION_DIRECTORY_REPLACED " + str(directory))
        own(directory, before)
        directories.append({
            "path": "." if directory == root else str(directory.relative_to(root)),
            "kind": "directory", "mode": _mode(before), "uid": before.st_uid,
            "gid": before.st_gid, "nlink": before.st_nlink,
            "dev": before.st_dev, "ino": before.st_ino,
        })
        with os.scandir(directory) as stream:
            entries = sorted(list(stream), key=lambda item: os.fsencode(item.name))
        for entry in entries:
            path = directory / entry.name
            if not _inside(root, path):
                raise MaterializationError("ENUMERATION_ESCAPE " + str(path))
            row = entry.stat(follow_symlinks=False)
            if stat.S_ISDIR(row.st_mode):
                visit(path)
            elif stat.S_ISREG(row.st_mode):
                digest, length, checked = _sha256_regular(path)
                own(path, checked)
                files.append({
                    "path": str(path.relative_to(root)), "kind": "file",
                    "size": length, "sha256": digest, "mode": _mode(checked),
                    "uid": checked.st_uid, "gid": checked.st_gid,
                    "nlink": checked.st_nlink, "dev": checked.st_dev,
                    "ino": checked.st_ino, "source_path": str(path),
                    "link_chain": [],
                })
            elif stat.S_ISLNK(row.st_mode):
                target, chain = resolve_link_chain(root, path)
                digest, length, checked = _sha256_regular(target)
                links.append({"path": str(path.relative_to(root)), "target": os.readlink(path),
                              "resolved": str(target.relative_to(root)), "chain": chain,
                              "sha256": digest})
                if not allow_file_links:
                    continue
                files.append({
                    "path": str(path.relative_to(root)), "kind": "file",
                    "size": length, "sha256": digest, "mode": _mode(checked),
                    "uid": checked.st_uid, "gid": checked.st_gid,
                    "nlink": 1, "dev": checked.st_dev, "ino": checked.st_ino,
                    "source_path": str(target), "link_chain": chain,
                })
            else:
                specials.append({"path": str(path.relative_to(root)),
                                 "mode": format(row.st_mode, "o")})
        after = os.lstat(directory)
        if (before.st_dev, before.st_ino, before.st_mode) != (
            after.st_dev, after.st_ino, after.st_mode
        ):
            raise MaterializationError("DIRECTORY_CHANGED_DURING_ENUMERATION " + str(directory))

    visit(root)
    if specials:
        raise MaterializationError("SPECIAL_ENTRIES " + json.dumps(specials))
    if links and not allow_file_links:
        raise MaterializationError("DISALLOWED_SYMLINKS " + json.dumps(links))
    if aliases:
        raise MaterializationError("SHARED_INODE_ALIASES " + json.dumps(aliases))
    external_hardlinks = [row["path"] for row in files if not row["link_chain"] and row["nlink"] != 1]
    if external_hardlinks:
        raise MaterializationError("NONINDEPENDENT_REGULAR_FILE " + repr(external_hardlinks[:10]))
    return {
        "root": str(root), "root_included_in_directory_count": True,
        "files": sorted(files, key=lambda row: os.fsencode(row["path"])),
        "directories": sorted(directories, key=lambda row: os.fsencode(row["path"])),
        "links": sorted(links, key=lambda row: os.fsencode(row["path"])),
        "specials": specials, "file_count": len(files),
        "directory_count_including_root": len(directories),
        "symlink_count": len(links), "special_count": 0,
        "shared_inode_alias_count": 0,
    }


def _historical_projection(path: Path) -> tuple[dict[str, str], dict[str, str | None], str]:
    raw = Path(path).read_bytes()
    document = json.loads(raw)
    rows = document.get("mapping")
    if not isinstance(rows, list) or len(rows) != 4617:
        raise MaterializationError("HISTORICAL_MANIFEST_COUNT_NOT_4617")
    hashes = {row["path"]: row["destination_sha256"] for row in rows}
    link_targets = {row["path"]: row.get("original_symlink") for row in rows}
    if len(hashes) != len(rows):
        raise MaterializationError("HISTORICAL_MANIFEST_DUPLICATE_PATH")
    if any(row.get("source_sha256") != row.get("destination_sha256") for row in rows):
        raise MaterializationError("HISTORICAL_SOURCE_DESTINATION_HASH_MISMATCH")
    return hashes, link_targets, hashlib.sha256(raw).hexdigest()


def verify_historical_membership(tree: dict, historical: Path) -> dict:
    hashes, link_targets, manifest_sha = _historical_projection(historical)
    actual = {row["path"]: row["sha256"] for row in tree["files"]}
    if set(actual) != set(hashes):
        raise MaterializationError("HISTORICAL_MEMBERSHIP_MISMATCH")
    wrong = [path for path in hashes if hashes[path] != actual[path]]
    if wrong:
        raise MaterializationError("HISTORICAL_HASH_MISMATCH " + repr(wrong[:10]))
    return {
        "result": "PASS", "historical_manifest_sha256": manifest_sha,
        "counting_method": "mapping rows / regular-file logical paths only; root and directories excluded",
        "historical_file_count": len(hashes),
        "historical_link_rows": sum(value is not None for value in link_targets.values()),
    }


def compare_raw_source(raw: dict, historical: Path) -> dict:
    result = verify_historical_membership(raw, historical)
    _, expected_links, _ = _historical_projection(historical)
    actual_links = {row["path"]: row["target"] for row in raw["links"]}
    expected = {path: target for path, target in expected_links.items() if target is not None}
    if actual_links != expected:
        raise MaterializationError("RAW_LINK_MAP_MISMATCH")
    result.update({
        "all_current_links_enumerated": True,
        "all_link_chains_explicitly_resolved": True,
        "link_count": len(actual_links), "link_map": raw["links"],
    })
    return result


def _projection(tree: dict) -> dict[str, dict]:
    keep = ("kind", "size", "sha256", "mode", "uid", "gid")
    return {row["path"]: {key: row[key] for key in keep} for row in tree["files"]}


def _directory_projection(tree: dict) -> dict[str, dict]:
    keep = ("kind", "mode", "uid", "gid")
    return {row["path"]: {key: row[key] for key in keep} for row in tree["directories"]}


def materialize(source: Path, destination: Path, historical: Path,
                raw_corroboration: Path | None = None) -> dict:
    source = _canonical_root(source)
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise MaterializationError("DESTINATION_ALREADY_EXISTS")
    if destination != Path(os.path.normpath(str(destination))):
        raise MaterializationError("NONCANONICAL_DESTINATION")
    # A preferred historical source has no links.  A raw fallback is accepted
    # only through the same exhaustive enumeration and explicit chain resolver.
    source_tree = inspect_tree(source, allow_file_links=True)
    history = verify_historical_membership(source_tree, historical)
    raw_result = None
    if raw_corroboration is not None:
        raw_tree = inspect_tree(raw_corroboration, allow_file_links=True)
        raw_result = compare_raw_source(raw_tree, historical)
        if _projection(raw_tree) != _projection(source_tree):
            raise MaterializationError("RAW_AND_PREFERRED_FILE_METADATA_MISMATCH")
        if _directory_projection(raw_tree) != _directory_projection(source_tree):
            raise MaterializationError("RAW_AND_PREFERRED_DIRECTORY_METADATA_MISMATCH")

    start = time.time()
    destination.parent.mkdir(parents=True, exist_ok=True)
    root_row = next(row for row in source_tree["directories"] if row["path"] == ".")
    os.mkdir(destination, int(root_row["mode"], 8))
    os.chmod(destination, int(root_row["mode"], 8), follow_symlinks=False)
    for row in sorted((r for r in source_tree["directories"] if r["path"] != "."),
                      key=lambda item: (len(Path(item["path"]).parts), os.fsencode(item["path"]))):
        target = destination / row["path"]
        os.mkdir(target, int(row["mode"], 8))
        os.chmod(target, int(row["mode"], 8), follow_symlinks=False)
    for row in source_tree["files"]:
        target = destination / row["path"]
        source_fd = os.open(row["source_path"], os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        target_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                            int(row["mode"], 8))
        try:
            while True:
                block = os.read(source_fd, CHUNK)
                if not block:
                    break
                offset = 0
                while offset < len(block):
                    offset += os.write(target_fd, block[offset:])
            os.fchmod(target_fd, int(row["mode"], 8))
        finally:
            os.close(target_fd)
            os.close(source_fd)

    destination_tree = inspect_tree(destination, allow_file_links=False)
    if _projection(destination_tree) != _projection(source_tree):
        raise MaterializationError("DESTINATION_FILE_VERIFICATION_MISMATCH")
    if _directory_projection(destination_tree) != _directory_projection(source_tree):
        raise MaterializationError("DESTINATION_DIRECTORY_VERIFICATION_MISMATCH")
    source_inodes = {(row["dev"], row["ino"]) for row in source_tree["files"]}
    destination_inodes = {(row["dev"], row["ino"]) for row in destination_tree["files"]}
    shared = source_inodes & destination_inodes
    if shared:
        raise MaterializationError("SOURCE_DESTINATION_SHARED_INODES")
    raw_intersections = None
    if raw_corroboration is not None:
        raw_inodes = {(row["dev"], row["ino"]) for row in raw_tree["files"]}
        raw_intersections = {
            "preferred_raw": len(source_inodes & raw_inodes),
            "destination_raw": len(destination_inodes & raw_inodes),
        }
        if any(raw_intersections.values()):
            raise MaterializationError("CROSS_TREE_SHARED_INODES " + repr(raw_intersections))
    return {
        "schema": "ep19-lean-materialization-v1", "result": "PASS",
        "source": str(source), "destination": str(destination),
        "selected_source": ("RAW_FULLY_VERIFIED_FALLBACK" if source_tree["symlink_count"]
                            else "PREFERRED_HISTORICAL_MATERIALIZED"),
        "historical_verification": history,
        "raw_corroboration": raw_result,
        "source_summary": {key: source_tree[key] for key in (
            "file_count", "directory_count_including_root", "root_included_in_directory_count",
            "symlink_count", "special_count", "shared_inode_alias_count")},
        "destination_summary": {key: destination_tree[key] for key in (
            "file_count", "directory_count_including_root", "root_included_in_directory_count",
            "symlink_count", "special_count", "shared_inode_alias_count")},
        "source_destination_shared_inode_count": 0,
        "cross_tree_shared_inode_counts": raw_intersections,
        "file_manifest": [{key: row[key] for key in
                           ("path", "kind", "size", "sha256", "mode", "uid", "gid", "nlink")}
                          for row in destination_tree["files"]],
        "directory_manifest": [{key: row[key] for key in
                                ("path", "kind", "mode", "uid", "gid", "nlink")}
                               for row in destination_tree["directories"]],
        "start": start, "end": time.time(),
        "materialization": "INDEPENDENT_REGULAR_FILES; MODES_PRESERVED_PER_ENTRY; NO_BLIND_LINK_FOLLOWING",
    }


def write_json_exclusive(path: Path, value: dict) -> None:
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--historical", type=Path, required=True)
    parser.add_argument("--raw-corroboration", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = materialize(args.source, args.destination, args.historical, args.raw_corroboration)
    write_json_exclusive(args.output, result)
    print(json.dumps({key: result[key] for key in ("result", "selected_source", "destination_summary")},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
