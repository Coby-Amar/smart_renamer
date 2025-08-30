# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Coby Amar

#!/usr/bin/env python
import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from smart_renamer.constants import (
    DIRECTORY,
    MATCH,
    OPERATIONS,
    PATTERN,
    REGEX,
    TIMESTAMP,
)


def get_latest_log(log_dir: str):
    """Return path to the most recent log file in log_dir."""
    logs = glob.glob(os.path.join(log_dir, "*.json"))
    if not logs:
        print("❌ No log files found.")
        return None
    return max(logs, key=os.path.getmtime)


def test_regex(directory, match_pattern, regex_pattern):
    directory = Path(directory)
    matched_files = sorted(directory.glob(match_pattern))

    if not matched_files:
        print(f"No files found matching pattern '{match_pattern}' in {directory}")
        return

    print(f"Found {len(matched_files)} files for regex testing.")
    regex = re.compile(regex_pattern)

    for old_path in matched_files:
        match = regex.search(old_path.name)
        if not match:
            print(f"{old_path.name}: no match")
        elif match.groupdict():
            print(f"{old_path.name}: {match.groupdict()}")
        elif match.groups():
            print(f"{old_path.name}: {match.groups()}")
        else:
            print(f"{old_path.name}: {match.group()}")


def rename(rename_map):
    # Perform renaming
    rename_log_entries = []
    for old_path, new_path in rename_map:
        old_path.rename(new_path)
        rename_log_entries.append({"from": old_path.name, "to": new_path.name})
        print(f"✅ Renamed: {old_path.name} ➝ {new_path.name}")
    return rename_log_entries


def renamed_mapper(directory, matched_files, regex, rename_pattern):
    rename_map = []
    for old_path in matched_files:
        old_name = old_path.name
        match = regex.search(old_name)
        if not match:
            print(f"Skipping {old_name}: regex pattern did not match")
            continue

        try:
            if match.groupdict():
                new_name = rename_pattern.format(**match.groupdict())
            elif match.groups():
                new_name = rename_pattern.format(*match.groups())
            else:
                new_name = rename_pattern.format(match.group())
        except (IndexError, KeyError) as e:
            print(f"Error: placeholders do not match regex groups for {old_name} ({e})")
            continue

        new_path = directory / new_name
        if new_path.exists():
            print(f"Skipping {old_name}: target '{new_name}' already exists.")
            continue

        rename_map.append((old_path, new_path))
    return rename_map


def crate_log(
    directory, match_pattern, regex_pattern, rename_pattern, rename_log_entries
):
    log_data = {
        TIMESTAMP: datetime.now().isoformat(),
        MATCH: str(match_pattern),
        REGEX: str(regex_pattern),
        PATTERN: str(rename_pattern),
        DIRECTORY: str(directory),
        OPERATIONS: rename_log_entries,
    }

    log_filename = f"smart_renamer_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(directory / log_filename, "w") as log_file:
        json.dump(log_data, log_file, indent=2)

    print(f"\nRenaming completed. Log saved to {log_filename}")


def undo(directory, operations):
    directory = Path(directory)
    for entry in operations:
        src = directory / Path(entry["to"])
        dest = directory / Path(entry["from"])
        if not src.exists():
            print(f"⚠️ Missing file: {src}")
            continue
        if dest.exists():
            print(f"⚠️ Conflict: {dest} already exists, skipping")
            continue
        try:
            src.rename(dest)
            print(f"✅ Renamed: {src.name} ➝ {dest.name}")
        except Exception as e:
            print(f"❌ Failed to rename {src} → {dest}: {e}")
    print("✅ Undo completed.")


def undo_from_log(log_path, folder_path="./", auto_yes=False):
    print("🔄 Undoing from log...")
    if log_path == "latest":
        log_path = get_latest_log(folder_path)
        if not log_path:
            return
    log_file = Path(log_path)
    if not log_file.exists():
        print(f"❌ Log file '{log_path}' not found.")
        return

    try:
        with open(log_file, "r") as f:
            log_data = json.load(f)
    except json.JSONDecodeError:
        print(f"❌ Log file '{log_path}' is not a valid JSON file.")
        return

    operations = log_data.get("operations", [])
    print(f"📂 Loaded latest from {log_path}")
    print("👀 Preview of undo operations:")

    for entry in operations:
        print(f"{Path(entry['to']).name}  ➝  {Path(entry['from']).name}")

    if not auto_yes:
        confirm = input("Proceed with undo? (y/n): ").strip().lower()
        if confirm != "y":
            print("❌ Undo cancelled.")
            return

    undo(folder_path, operations)


def match_and_rename_files(
    directory,
    match_pattern,
    rename_pattern,
    regex_pattern,
    dry_run=False,
    auto_yes=False,
):
    directory = Path(directory)
    matched_files = sorted(directory.glob(match_pattern))

    if not matched_files:
        print(f"No files found matching pattern '{match_pattern}' in {directory}")
        return

    print(f"Found {len(matched_files)} files matching pattern '{match_pattern}'")
    regex = re.compile(regex_pattern)
    rename_map = renamed_mapper(directory, matched_files, regex, rename_pattern)

    if not rename_map:
        print("No files to rename after regex filtering.")
        return

    print("\nPreview of changes:")
    for old_path, new_path in rename_map:
        print(f"{old_path.name}  ➝  {new_path.name}")

    if dry_run:
        print("\nDry run: No files were renamed.")
        return

    if not auto_yes:
        confirm = input("\nProceed with renaming? (y/n): ").strip().lower()
        if confirm != "y":
            print("Renaming cancelled.")
            return

    # Perform renaming
    rename_log_entries = rename(rename_map)
    crate_log(
        directory, match_pattern, regex_pattern, rename_pattern, rename_log_entries
    )


def main():
    parser = argparse.ArgumentParser(
        description="Match files by pattern, extract part by regex, rename accordingly with preview."
    )
    parser.add_argument(
        "-d", "--directory", help="Folder path (default: current directory)"
    )
    parser.add_argument("-m", "--match", help="Glob match pattern, e.g. '*.txt'")
    parser.add_argument(
        "-r",
        "--regex",
        help=r"Regex pattern to capture parts, e.g. 'file_(\d+)_version'",
    )
    parser.add_argument(
        "-p", "--pattern", help="Rename pattern with placeholders, e.g. 'image_{}.txt'"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview rename actions without applying changes",
    )
    parser.add_argument(
        "-u",
        "--undo",
        nargs="?",
        const="latest",
        help="Undo using rename log file (or latest)",
    )
    parser.add_argument(
        "-y", "--yes", action="store_true", help="Skip confirmation prompts"
    )
    parser.add_argument(
        "--test-regex",
        action="store_true",
        help="Test regex against matching files without renaming",
    )
    args = parser.parse_args()
    try:
        if args.undo:
            log_path = args.undo
            if log_path == "latest":
                undo_from_log(log_path, auto_yes=args.yes)
            return

        folder_path = (
            Path(args.directory)
            if args.directory
            else input("Enter folder path (default: current directory): ").strip()
            or Path.cwd()
        )
        if not folder_path.exists():
            print(f"❌ Directory '{folder_path}' does not exist.")
            sys.exit(1)

        file_match_pattern = (
            args.match or input("Enter glob match pattern (e.g. '*.txt'): ").strip()
        )
        regex_pattern = (
            args.regex
            or input("Enter regex pattern (e.g. r'file_(\\d+)_version'): ").strip()
        )

        if args.test_regex:
            test_regex(folder_path, file_match_pattern, regex_pattern)
            return

        rename_pattern = (
            args.pattern
            or input("Enter rename pattern (e.g. 'image_{}.txt'): ").strip()
        )

        match_and_rename_files(
            folder_path,
            file_match_pattern,
            rename_pattern,
            regex_pattern,
            dry_run=args.dry_run,
            auto_yes=args.yes,
        )
    except KeyboardInterrupt:
        print("\nOperation cancelled by user. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
