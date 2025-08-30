# # SPDX-License-Identifier: MIT
# # Copyright (c) 2025 Coby Amar

import io
import json
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

# Import functions from CLI script
from smart_renamer.constants import DIRECTORY, MATCH, OPERATIONS, PATTERN, REGEX
from smart_renamer.renamer import (
    match_and_rename_files,
    test_regex,
    undo,
    undo_from_log,
)


class RenamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Renamer")
        self.root.geometry("780x580")

        # Directory selection
        tk.Label(root, text="Directory:").grid(row=0, column=0, sticky="w")
        self.dir_var = tk.StringVar(value=str(Path.cwd()))
        tk.Entry(root, textvariable=self.dir_var, width=55).grid(
            row=0, column=1, padx=5, pady=5
        )
        tk.Button(root, text="Browse", command=self.browse_dir).grid(row=0, column=2)

        # Glob pattern
        tk.Label(root, text="Glob Match: *.txt").grid(row=1, column=0, sticky="w")
        self.match_var = tk.StringVar(value="")
        tk.Entry(root, textvariable=self.match_var, width=40).grid(
            row=1, column=1, padx=5, pady=5
        )

        # Regex pattern
        tk.Label(root, text="Regex Pattern: r(.*)").grid(row=2, column=0, sticky="w")
        self.regex_var = tk.StringVar(value="")
        tk.Entry(root, textvariable=self.regex_var, width=40).grid(
            row=2, column=1, padx=5, pady=5
        )

        # Rename pattern
        tk.Label(root, text="Rename Pattern: {}.txt").grid(row=3, column=0, sticky="w")
        self.rename_var = tk.StringVar(value="")
        tk.Entry(root, textvariable=self.rename_var, width=40).grid(
            row=3, column=1, padx=5, pady=5
        )

        # Action buttons
        tk.Button(root, text="Test Regex", command=self.run_test).grid(
            row=4, column=0, pady=5
        )
        tk.Button(root, text="Preview Rename", command=self.run_preview).grid(
            row=4, column=1, pady=5
        )
        tk.Button(root, text="Apply Rename", command=self.run_rename).grid(
            row=4, column=2, pady=5
        )
        tk.Button(root, text="Undo", command=self.run_undo).grid(
            row=5,
            column=0,
        )
        tk.Button(root, text="Load Config", command=self.load_log).grid(
            row=5,
            column=1,
        )
        tk.Button(root, text="Clear log", command=self.clear_log).grid(
            row=5,
            column=2,
        )

        # Log / output window
        tk.Label(root, text="Log / Preview:").grid(row=6, column=0, sticky="w")
        self.output = scrolledtext.ScrolledText(root, width=95, height=22)
        self.output.grid(row=7, column=0, columnspan=5, padx=5, pady=5)

        # Store loaded JSON operations
        self.loaded_operations = []

    def browse_dir(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dir_var.set(folder)

    def log(self, text):
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)

    def clear_log(self):
        self.output.delete("1.0", tk.END)

    def run_in_thread(self, func, *args, **kwargs):
        """Run heavy tasks in a background thread so GUI stays responsive"""

        def wrapper():
            try:
                # Capture prints
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()

                func(*args, **kwargs)

                # Get all printed text and log it
                output = sys.stdout.getvalue()
                self.log(output.strip())
            except Exception as e:
                self.log(f"Error: {e}")
            finally:
                sys.stdout = old_stdout

        threading.Thread(target=wrapper, daemon=True).start()

    def run_test(self):
        self.log("🔍 Testing regex...")
        self.run_in_thread(
            test_regex, self.dir_var.get(), self.match_var.get(), self.regex_var.get()
        )

    def run_preview(self):
        self.run_in_thread(
            match_and_rename_files,
            self.dir_var.get(),
            self.match_var.get(),
            self.rename_var.get(),
            self.regex_var.get(),
            dry_run=True,
            auto_yes=False,
        )

    def run_rename(self):
        if not messagebox.askyesno("Confirm", "Proceed with renaming?"):
            return
        self.log("✍️ Applying rename...")
        self.run_in_thread(
            match_and_rename_files,
            self.dir_var.get(),
            self.match_var.get(),
            self.rename_var.get(),
            self.regex_var.get(),
            dry_run=False,
            auto_yes=True,
        )

    def run_undo(self):
        folder_path = self.dir_var.get()
        self.run_in_thread(
            undo_from_log,
            "latest",
            folder_path=folder_path,
            auto_yes=True,
        )

    def load_log(self):
        """Load config from a JSON log"""
        file_path = filedialog.askopenfilename(
            title="Select JSON Log",
            filetypes=[("JSON files", "*.json")],
        )
        if not file_path:
            return

        try:
            with open(file_path, "r") as f:
                config = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON: {e}")
            return

        directory = config.get(DIRECTORY, None)
        operations = config.get(OPERATIONS, None)
        match = config.get(MATCH, None)
        regex = config.get(REGEX, None)
        pattern = config.get(PATTERN, None)
        if not directory or not Path(directory).exists():
            messagebox.showinfo("Invalid Directory", "Directory in log does not exist.")
            return
        if not match:
            messagebox.showinfo(
                "No Match Pattern", "No match pattern found in the log."
            )
            return
        if not regex:
            messagebox.showinfo(
                "No Regex Pattern", "No regex pattern found in the log."
            )
            return
        if not pattern:
            messagebox.showinfo(
                "No Rename Pattern", "No rename pattern found in the log."
            )
            return
        self.dir_var.set(directory)
        self.match_var.set(match)
        self.regex_var.set(regex)
        self.rename_var.set(pattern)

        self.log(f"📂 Loaded config from {file_path}")
        if operations:
            self.log("Preview of operations:")
            for entry in operations:
                self.log(f"{entry['from']}  ➝  {entry['to']}")
            if not messagebox.askyesno("Confirm", "Proceed with undoing operations?"):
                return
            self.run_in_thread(undo, directory, operations)
        else:
            self.run_rename()


def main():
    root = tk.Tk()
    RenamerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
