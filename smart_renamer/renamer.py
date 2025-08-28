# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Coby Amar

#!/usr/bin/env python
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path


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
    rename_log_entries = []
    for old_path, new_path in rename_map:
        old_path.rename(new_path)
        rename_log_entries.append({"from": str(old_path), "to": str(new_path)})
        print(f"Renamed: {old_path.name} ➝ {new_path.name}")

    # Write log
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "regex": regex_pattern,
        "pattern": rename_pattern,
        "operations": rename_log_entries,
    }

    log_filename = f"smart_renamer_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(directory / log_filename, "w") as log_file:
        json.dump(log_data, log_file, indent=2)

    print(f"\nRenaming completed. Log saved to {log_filename}")


def undo_from_log(log_path, auto_yes=False):
    log_file = Path(log_path)
    if not log_file.exists():
        print(f"Log file '{log_path}' not found.")
        return

    try:
        with open(log_file, "r") as f:
            log_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Log file '{log_path}' is not a valid JSON file.")
        return

    rename_log = log_data.get("operations", [])
    print(f"Loaded log with {len(rename_log)} entries.")
    print("Preview of undo operations:")

    for entry in rename_log:
        print(f"{Path(entry['to']).name}  ➝  {Path(entry['from']).name}")

    if not auto_yes:
        confirm = input("\nProceed with undo? (y/n): ").strip().lower()
        if confirm != "y":
            print("Undo cancelled.")
            return

    for entry in rename_log:
        src = Path(entry["to"])
        dest = Path(entry["from"])
        if not src.exists():
            print(f"Missing file: {src}. Cannot undo.")
            continue
        if dest.exists():
            print(f"Conflict: {dest} already exists. Skipping undo of {src}.")
            continue
        src.rename(dest)
        print(f"Reverted: {src.name} ➝ {dest.name}")

    print("\nUndo completed.")


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
                logs = sorted(Path.cwd().glob("smart_renamer_log_*.json"), reverse=True)
                if not logs:
                    print("No smart renamer logs found in the current directory.")
                    return
                log_path = logs[0]
            undo_from_log(log_path, auto_yes=args.yes)
            return

        folder_path = (
            Path(args.directory)
            if args.directory
            else Path(
                input("Enter folder path (default: current directory): ").strip()
                or Path.cwd()
            )
        )
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
