from pathlib import Path
import hashlib
import json
import os
import tempfile
import unittest

import lean_materialization as lm


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class LeanMaterializationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ep19-lean-materialization-")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_strict_inspection_rejects_symlink(self):
        source = self.root / "source"
        source.mkdir()
        (source / "real").write_bytes(b"bytes")
        (source / "alias").symlink_to("real")
        with self.assertRaisesRegex(lm.MaterializationError, "DISALLOWED_SYMLINKS"):
            lm.inspect_tree(source, allow_file_links=False)

    def test_complete_chain_is_recorded(self):
        source = self.root / "source"
        source.mkdir()
        (source / "real").write_bytes(b"bytes")
        (source / "second").symlink_to("real")
        (source / "first").symlink_to("second")
        target, chain = lm.resolve_link_chain(source, source / "first")
        self.assertEqual(target, source / "real")
        self.assertEqual([row["link"] for row in chain], ["first", "second"])

    def test_cycle_is_rejected(self):
        source = self.root / "source"
        source.mkdir()
        (source / "a").symlink_to("b")
        (source / "b").symlink_to("a")
        with self.assertRaisesRegex(lm.MaterializationError, "LINK_CYCLE"):
            lm.resolve_link_chain(source, source / "a")

    def test_missing_target_is_rejected(self):
        source = self.root / "source"
        source.mkdir()
        (source / "a").symlink_to("missing")
        with self.assertRaisesRegex(lm.MaterializationError, "LINK_TARGET_MISSING"):
            lm.resolve_link_chain(source, source / "a")

    def test_outside_target_is_rejected(self):
        source = self.root / "source"
        source.mkdir()
        outside = self.root / "outside"
        outside.write_bytes(b"outside")
        (source / "a").symlink_to(outside)
        with self.assertRaisesRegex(lm.MaterializationError, "LINK_ESCAPES_ROOT"):
            lm.resolve_link_chain(source, source / "a")

    def test_special_target_is_rejected(self):
        source = self.root / "source"
        source.mkdir()
        os.mkfifo(source / "fifo")
        (source / "a").symlink_to("fifo")
        with self.assertRaisesRegex(lm.MaterializationError, "LINK_TARGET_NOT_REGULAR"):
            lm.resolve_link_chain(source, source / "a")

    def test_shared_regular_inode_is_rejected(self):
        source = self.root / "source"
        source.mkdir()
        (source / "one").write_bytes(b"bytes")
        os.link(source / "one", source / "two")
        with self.assertRaisesRegex(lm.MaterializationError, "SHARED_INODE_ALIASES"):
            lm.inspect_tree(source, allow_file_links=False)

    def test_external_hardlink_is_rejected(self):
        source = self.root / "source"
        source.mkdir()
        outside = self.root / "outside"
        outside.write_bytes(b"bytes")
        os.link(outside, source / "linked")
        with self.assertRaisesRegex(lm.MaterializationError, "NONINDEPENDENT_REGULAR_FILE"):
            lm.inspect_tree(source, allow_file_links=False)

    def test_symlinked_root_ancestor_is_rejected(self):
        real = self.root / "real"
        real.mkdir()
        (real / "child").mkdir()
        alias = self.root / "alias"
        alias.symlink_to(real, target_is_directory=True)
        with self.assertRaisesRegex(lm.MaterializationError, "ROOT_OR_ANCESTOR_SYMLINK"):
            lm.inspect_tree(alias / "child", allow_file_links=False)

    def test_materialized_equivalent_has_independent_regular_files(self):
        raw = self.root / "raw"
        raw.mkdir(mode=0o750)
        (raw / "real").write_bytes(b"bytes")
        os.chmod(raw / "real", 0o640)
        (raw / "alias").symlink_to("real")
        historical = self.root / "historical.json"
        # The production verifier requires 4617 rows. Patch its projection in
        # this small behavioral fixture; membership mechanics remain real.
        rows = [
            {"path": "alias", "source_sha256": digest(b"bytes"),
             "destination_sha256": digest(b"bytes"), "original_symlink": "real"},
            {"path": "real", "source_sha256": digest(b"bytes"),
             "destination_sha256": digest(b"bytes"), "original_symlink": None},
        ]
        historical.write_text(json.dumps({"mapping": rows}))
        original = lm._historical_projection
        def fixture_projection(path):
            document = json.loads(Path(path).read_text())
            hashes = {row["path"]: row["destination_sha256"] for row in document["mapping"]}
            links = {row["path"]: row.get("original_symlink") for row in document["mapping"]}
            return hashes, links, hashlib.sha256(Path(path).read_bytes()).hexdigest()
        lm._historical_projection = fixture_projection
        try:
            result = lm.materialize(raw, self.root / "dest", historical)
        finally:
            lm._historical_projection = original
        self.assertEqual(result["result"], "PASS")
        self.assertTrue((self.root / "dest/alias").is_file())
        self.assertFalse((self.root / "dest/alias").is_symlink())
        self.assertEqual((self.root / "dest/alias").read_bytes(), b"bytes")
        self.assertNotEqual(os.lstat(self.root / "dest/alias").st_ino,
                            os.lstat(self.root / "dest/real").st_ino)
        self.assertEqual(os.lstat(self.root / "dest/alias").st_nlink, 1)


if __name__ == "__main__":
    unittest.main()
