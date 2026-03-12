"""Tests for File Sentinel."""
import os
import tempfile
import unittest
from pathlib import Path
from file_sentinel import Sentinel


class TestSentinel(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.backup_dir = tempfile.mkdtemp()
        Path(self.test_dir, "file1.txt").write_text("Hello World")
        Path(self.test_dir, "file2.txt").write_text("Test content")
        subdir = Path(self.test_dir, "subdir")
        subdir.mkdir()
        Path(subdir, "file3.txt").write_text("Nested file")
        self.sentinel = Sentinel(
            watch_dir=self.test_dir, backup_dir=self.backup_dir, auto_restore=True,
        )

    def test_create_baseline(self):
        count = self.sentinel.create_baseline()
        self.assertEqual(count, 3)

    def test_no_changes(self):
        self.sentinel.create_baseline()
        changes = self.sentinel.check_integrity()
        self.assertEqual(len(changes), 0)

    def test_detect_modification(self):
        self.sentinel.create_baseline()
        Path(self.test_dir, "file1.txt").write_text("Modified!")
        changes = self.sentinel.check_integrity()
        modified = [c for c in changes if c.event_type == "modified"]
        self.assertEqual(len(modified), 1)
        self.assertEqual(modified[0].path, "file1.txt")

    def test_detect_deletion(self):
        self.sentinel.create_baseline()
        os.remove(Path(self.test_dir, "file2.txt"))
        changes = self.sentinel.check_integrity()
        deleted = [c for c in changes if c.event_type == "deleted"]
        self.assertEqual(len(deleted), 1)

    def test_detect_creation(self):
        self.sentinel.create_baseline()
        Path(self.test_dir, "new_file.txt").write_text("New!")
        changes = self.sentinel.check_integrity()
        created = [c for c in changes if c.event_type == "created"]
        self.assertEqual(len(created), 1)

    def test_restore_file(self):
        self.sentinel.create_baseline()
        original = Path(self.test_dir, "file1.txt").read_text()
        Path(self.test_dir, "file1.txt").write_text("Tampered!")
        self.sentinel.restore_file("file1.txt")
        restored = Path(self.test_dir, "file1.txt").read_text()
        self.assertEqual(original, restored)

    def test_exclude_patterns(self):
        Path(self.test_dir, "debug.log").write_text("log data")
        sentinel = Sentinel(
            watch_dir=self.test_dir, backup_dir=self.backup_dir,
            exclude_patterns=["*.log"],
        )
        count = sentinel.create_baseline()
        self.assertEqual(count, 3)

    def test_report(self):
        self.sentinel.create_baseline()
        report = self.sentinel.report()
        self.assertEqual(report["baseline_files"], 3)
        self.assertEqual(report["total_changes"], 0)


if __name__ == "__main__":
    unittest.main()
