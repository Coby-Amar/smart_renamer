# # SPDX-License-Identifier: MIT
# # Copyright (c) 2025 Coby Amar
#!/usr/bin/env python
import argparse
import json
import re
from datetime import datetime
from pathlib import Path

LOG_FILE = ".rename_log.json"
MAX_HISTORY = 50  # Keep only last 50 sessions


def sanitize_filename(name: str) -> str:
    """Remove characters not allowed on all systems (Windows in particular)."""
    return re.sub(r'[<>:"/\\|?*]', "_", name)


def rename_files(
    directory: Path,
    match_pattern: str,
    replace_pattern: str,
    mode="pattern",
    start=1,
    recursive=False,
):
    """
    Unified rename function for pattern and increment modes.
    """
    regex = re.compile(match_pattern)
    files = sorted(directory.rglob("*") if recursive else directory.iterdir())
    counter = start
    changes = []

    for file in files:
        if not file.is_file():
            continue

        match = regex.search(file.name)
        if not match:
            continue

        ext = file.suffix  # preserve original extension
        if mode == "increment":
            try:
                base_name = replace_pattern.format(counter=counter, **match.groupdict())
            except (IndexError, KeyError):
                base_name = replace_pattern.format(counter=counter)
            counter += 1
        else:  # pattern mode
            base_name = regex.sub(replace_pattern, file.name)
            # always append original extension if not included
            if not base_name.endswith(ext):
                base_name += ext
            ext = ""

        new_name = sanitize_filename(base_name + ext)
        new_path = file.with_name(new_name)
        changes.append((file, new_path))

    return changes


def load_history():
    path = Path(LOG_FILE)
    if not path.exists():
        return []
    return json.loads(path.read_text())


def save_history(history):
    Path(LOG_FILE).write_text(json.dumps(history, indent=2))


def add_to_history(changes):
    history = load_history()
    session = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "changes": [{"old": str(old), "new": str(new)} for old, new in changes],
    }
    history.append(session)
    history = history[-MAX_HISTORY:]  # keep last N sessions
    save_history(history)
    print(f"📒 Logged {len(changes)} renames at {session['timestamp']}")


def confirm_and_apply(
    changes, dry_run=False, auto_confirm=False, save_history_flag=True
):
    if not changes:
        print("⚠️ No matching files found.")
        return

    print(f"\nPreview: {len(changes)} files will be renamed:")
    for old, new in changes:
        print(f"  {old.name} -> {new.name}")

    if dry_run:
        print("\n💡 Dry run mode enabled. No files will be renamed.")
        return

    if not auto_confirm:
        confirm = input("\nApply these changes? (y/N): ").strip().lower()
        if confirm != "y":
            print("❌ Operation cancelled.")
            return

    for old, new in changes:
        try:
            old.rename(new)
        except Exception as e:
            print(f"❌ Failed to rename {old} -> {new}: {e}")

    print("✅ Renaming complete.")

    if save_history_flag:
        add_to_history(changes)


def undo_last(dry_run=False, auto_confirm=False):
    history = load_history()
    if not history:
        print("⚠️ No history found. Nothing to undo.")
        return

    session = history.pop()
    changes = []
    missing_files = []

    for item in reversed(session["changes"]):
        old = Path(item["old"])
        new = Path(item["new"])
        if new.exists():
            changes.append((new, old))
        else:
            missing_files.append(str(new))

    if missing_files:
        print("⚠️ Warning: Some files are missing and will be skipped in undo:")
        for f in missing_files:
            print("   " + f)

    if not changes:
        print("⚠️ Nothing to undo.")
        return

    print(f"\nUndoing session from {session['timestamp']}:")
    for old, new in changes:
        print(f"  {old.name} -> {new.name}")

    if dry_run:
        print("\n💡 Dry run mode enabled. No files will be renamed.")
        return

    if not auto_confirm:
        confirm = input("\nUndo these changes? (y/N): ").strip().lower()
        if confirm != "y":
            print("❌ Undo cancelled.")
            return

    for old, new in changes:
        try:
            old.rename(new)
        except Exception as e:
            print(f"❌ Failed to rename {old} -> {new}: {e}")

    save_history(history)
    print("✅ Undo complete.")


def show_history():
    history = load_history()
    if not history:
        print("⚠️ No history found.")
        return

    print("\n📜 Rename history:")
    for i, session in enumerate(history, 1):
        print(f"[{i}] {session['timestamp']} - {len(session['changes'])} changes")
        for item in session["changes"][:3]:
            print(f"   {Path(item['old']).name} -> {Path(item['new']).name}")
        if len(session["changes"]) > 3:
            print("   ...")


def apply_from_config(file_path):
    """Load arguments from JSON config file and run renaming."""
    config = json.loads(Path(file_path).read_text())
    directory = Path(config.get("directory", ".")).resolve()
    if not directory.is_dir():
        print(f"❌ Error: {directory} is not a valid directory.")
        return

    changes = rename_files(
        directory,
        config.get("match_pattern"),
        config.get("replace_pattern"),
        config.get("mode", "pattern"),
        config.get("start", 1),
        config.get("recursive", False),
    )

    confirm_and_apply(
        changes,
        dry_run=config.get("dry_run", False),
        auto_confirm=config.get("yes", False),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Cross-platform file renamer with regex, increment, undo, and history."
    )
    parser.add_argument("directory", nargs="?", help="Directory containing files")
    parser.add_argument(
        "match_pattern", nargs="?", help="Regex pattern to match filenames"
    )
    parser.add_argument(
        "replace_pattern",
        nargs="?",
        help="Replacement pattern. Use {counter} for increment mode.",
    )
    parser.add_argument(
        "--mode",
        choices=["pattern", "increment"],
        default="pattern",
        help="Rename mode defaults to pattern\nCan also use named groups in increment",
    )
    parser.add_argument(
        "--start", type=int, default=1, help="Starting number for increment mode"
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process files in subdirectories recursively",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show preview only, don’t rename"
    )
    parser.add_argument(
        "--yes", action="store_true", help="Skip preview confirmation and apply changes"
    )
    parser.add_argument(
        "--undo", action="store_true", help="Undo last rename operation"
    )
    parser.add_argument("--history", action="store_true", help="Show rename history")
    parser.add_argument(
        "--from-file", help="Load rename configuration from a JSON file"
    )

    args = parser.parse_args()

    if args.undo:
        undo_last(dry_run=args.dry_run, auto_confirm=args.yes)
        return
    if args.history:
        show_history()
        return
    if args.from_file:
        apply_from_config(args.from_file)
        return
    if not args.directory or not args.match_pattern or not args.replace_pattern:
        parser.error(
            "❌ directory, match_pattern and replace_pattern are required unless using --undo, --history, or --from-file"
        )

    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        print(f"❌ Error: {directory} is not a valid directory.")
        return

    changes = rename_files(
        directory,
        args.match_pattern,
        args.replace_pattern,
        args.mode,
        args.start,
        args.recursive,
    )

    confirm_and_apply(changes, args.dry_run, args.yes)


if __name__ == "__main__":
    main()
