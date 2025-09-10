# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Coby Amar

# import sys

# from smart_renamer.renamer import main

# if __name__ == "__main__":
#     sys.exit(main())
#!/usr/bin/env python
import argparse
from pathlib import Path

from .renamer import (
    apply_from_config,
    confirm_and_apply,
    rename_files,
    show_history,
    undo_last,
)


def main():
    parser = argparse.ArgumentParser(description="File Renamer CLI")
    parser.add_argument("directory", nargs="?", help="Directory containing files")
    parser.add_argument(
        "match_pattern", nargs="?", help="Regex pattern to match filenames"
    )
    parser.add_argument(
        "replace_pattern",
        nargs="?",
        help="Replacement pattern. Use {counter} for increment mode.",
    )
    parser.add_argument("--mode", choices=["pattern", "increment"], default="pattern")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--undo", action="store_true")
    parser.add_argument("--history", action="store_true")
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
            "directory, match_pattern, and replace_pattern are required unless using --undo, --history, or --from-file"
        )

    directory = Path(args.directory).resolve()
    changes = rename_files(
        directory,
        args.match_pattern,
        args.replace_pattern,
        args.mode,
        args.start,
        args.recursive,
    )
    confirm_and_apply(changes, dry_run=args.dry_run, auto_confirm=args.yes)


if __name__ == "__main__":
    main()
