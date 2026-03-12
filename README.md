# 🔒 File Sentinel

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()

A Python file integrity monitoring tool that watches directories for unauthorized changes and automatically restores files from secure backups.

## Features

- 📁 **Real-time Monitoring** — Watches files and directories for changes using polling
- 🔐 **SHA-256 Integrity Checks** — Cryptographic hashing ensures tamper detection
- 💾 **Auto-Backup & Restore** — Automatically backs up files and restores on tampering
- 📊 **Change Reports** — Detailed logs of all modifications, additions, and deletions
- ⚙️ **Configurable Rules** — Include/exclude patterns, custom actions, flexible intervals

## Installation

```bash
pip install file-sentinel
```

## Quick Start

```python
from file_sentinel import Sentinel

sentinel = Sentinel(
    watch_dir="./important_files",
    backup_dir="./backups",
    auto_restore=True
)

# Create initial baseline
sentinel.create_baseline()

# Start monitoring
sentinel.watch()
```

## CLI Usage

```bash
# Create a baseline snapshot
file-sentinel baseline ./my_directory

# Check integrity against baseline
file-sentinel check ./my_directory

# Watch for changes in real-time
file-sentinel watch ./my_directory --auto-restore
```

## Configuration

```python
sentinel = Sentinel(
    watch_dir="./data",
    backup_dir="./backups",
    auto_restore=True,
    hash_algorithm="sha256",
    exclude_patterns=["*.tmp", "*.log", "__pycache__"],
    on_change=my_callback_function,
    check_interval=5,
)
```

## How It Works

1. **Baseline** — Scans all files, calculates SHA-256 hashes, creates backups
2. **Monitor** — Periodically rescans and compares against baseline
3. **Detect** — Identifies modified, deleted, and new files
4. **Restore** — Optionally auto-restores tampered files from backup

## License

MIT License — see [LICENSE](LICENSE) for details.
