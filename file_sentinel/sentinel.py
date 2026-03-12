"""
File Sentinel - File integrity monitoring with auto-restore.

Watches directories for unauthorized changes and automatically
restores files from secure backups when tampering is detected.
"""

import os
import hashlib
import json
import shutil
import time
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict
from fnmatch import fnmatch


__version__ = "0.1.0"


@dataclass
class FileRecord:
    """Record of a file's integrity state."""
    path: str
    hash: str
    size: int
    modified: float
    permissions: int


@dataclass
class ChangeEvent:
    """Represents a detected file change."""
    path: str
    event_type: str  # 'modified', 'created', 'deleted', 'permissions_changed'
    timestamp: str
    original_hash: Optional[str] = None
    current_hash: Optional[str] = None
    restored: bool = False


class Sentinel:
    """File integrity monitor with backup and auto-restore."""

    def __init__(self, watch_dir, backup_dir=".sentinel_backups", auto_restore=False,
                 hash_algorithm="sha256", exclude_patterns=None, on_change=None,
                 check_interval=5):
        self.watch_dir = Path(watch_dir).resolve()
        self.backup_dir = Path(backup_dir).resolve()
        self.auto_restore = auto_restore
        self.hash_algorithm = hash_algorithm
        self.exclude_patterns = exclude_patterns or ["*.tmp", "*.pyc", "__pycache__"]
        self.on_change = on_change
        self.check_interval = check_interval
        self._baseline: Dict[str, FileRecord] = {}
        self._baseline_file = self.backup_dir / "baseline.json"
        self._running = False
        self._changes: List[ChangeEvent] = []

    def _hash_file(self, filepath):
        """Calculate hash of a file."""
        h = hashlib.new(self.hash_algorithm)
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            return h.hexdigest()
        except (IOError, OSError):
            return ""

    def _should_exclude(self, filepath):
        """Check if file matches exclude patterns."""
        name = filepath.name
        rel = str(filepath.relative_to(self.watch_dir))
        return any(fnmatch(name, p) or fnmatch(rel, p) for p in self.exclude_patterns)

    def _scan_directory(self):
        """Scan directory and build file records."""
        records = {}
        if not self.watch_dir.exists():
            return records
        for filepath in self.watch_dir.rglob("*"):
            if filepath.is_file() and not self._should_exclude(filepath):
                rel_path = str(filepath.relative_to(self.watch_dir))
                stat = filepath.stat()
                records[rel_path] = FileRecord(
                    path=rel_path,
                    hash=self._hash_file(filepath),
                    size=stat.st_size,
                    modified=stat.st_mtime,
                    permissions=stat.st_mode,
                )
        return records

    def create_baseline(self):
        """Create initial baseline snapshot and backup files."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._baseline = self._scan_directory()

        baseline_data = {
            path: {
                "path": rec.path, "hash": rec.hash, "size": rec.size,
                "modified": rec.modified, "permissions": rec.permissions,
            }
            for path, rec in self._baseline.items()
        }
        with open(self._baseline_file, "w") as f:
            json.dump(baseline_data, f, indent=2)

        for rel_path in self._baseline:
            src = self.watch_dir / rel_path
            dst = self.backup_dir / "files" / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

        return len(self._baseline)

    def load_baseline(self):
        """Load existing baseline from disk."""
        if not self._baseline_file.exists():
            return False
        with open(self._baseline_file) as f:
            data = json.load(f)
        self._baseline = {path: FileRecord(**rec) for path, rec in data.items()}
        return True

    def check_integrity(self):
        """Check current files against baseline."""
        if not self._baseline:
            self.load_baseline()

        changes = []
        current = self._scan_directory()
        now = datetime.now().isoformat()

        for path, baseline_rec in self._baseline.items():
            if path not in current:
                changes.append(ChangeEvent(
                    path=path, event_type="deleted", timestamp=now,
                    original_hash=baseline_rec.hash,
                ))
            elif current[path].hash != baseline_rec.hash:
                changes.append(ChangeEvent(
                    path=path, event_type="modified", timestamp=now,
                    original_hash=baseline_rec.hash, current_hash=current[path].hash,
                ))
            elif current[path].permissions != baseline_rec.permissions:
                changes.append(ChangeEvent(
                    path=path, event_type="permissions_changed", timestamp=now,
                ))

        for path in current:
            if path not in self._baseline:
                changes.append(ChangeEvent(
                    path=path, event_type="created", timestamp=now,
                    current_hash=current[path].hash,
                ))

        return changes

    def restore_file(self, rel_path):
        """Restore a file from backup."""
        backup_path = self.backup_dir / "files" / rel_path
        target_path = self.watch_dir / rel_path
        if backup_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, target_path)
            return True
        return False

    def watch(self):
        """Start watching directory for changes."""
        if not self._baseline:
            self.create_baseline()

        self._running = True
        print(f"[Sentinel] Watching {self.watch_dir} (interval: {self.check_interval}s)")

        try:
            while self._running:
                changes = self.check_integrity()
                for change in changes:
                    self._handle_change(change)
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self._running = False
            print("[Sentinel] Stopped.")

    def stop(self):
        """Stop watching."""
        self._running = False

    def _handle_change(self, change):
        """Handle a detected change."""
        print(f"[Sentinel] {change.event_type.upper()}: {change.path}")

        if self.auto_restore and change.event_type in ("modified", "deleted"):
            restored = self.restore_file(change.path)
            change.restored = restored
            if restored:
                print(f"[Sentinel] RESTORED: {change.path}")

        self._changes.append(change)
        if self.on_change:
            self.on_change(change)

    @property
    def change_log(self):
        """Get all recorded changes."""
        return list(self._changes)

    def report(self):
        """Generate a summary report."""
        return {
            "watch_dir": str(self.watch_dir),
            "baseline_files": len(self._baseline),
            "total_changes": len(self._changes),
            "modifications": sum(1 for c in self._changes if c.event_type == "modified"),
            "deletions": sum(1 for c in self._changes if c.event_type == "deleted"),
            "creations": sum(1 for c in self._changes if c.event_type == "created"),
            "restorations": sum(1 for c in self._changes if c.restored),
        }
