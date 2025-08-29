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
from smart_renamer.renamer import match_and_rename_files, test_regex, undo_from_log


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

        # Options
        self.dry_var = tk.BooleanVar(value=True)
        self.yes_var = tk.BooleanVar(value=False)
        tk.Checkbutton(root, text="Dry Run", variable=self.dry_var).grid(
            row=4, column=0, sticky="w"
        )
        tk.Checkbutton(root, text="Auto-Yes", variable=self.yes_var).grid(
            row=4, column=1, sticky="w"
        )

        # Action buttons
        tk.Button(root, text="Test Regex", command=self.run_test).grid(
            row=5, column=0, pady=5
        )
        tk.Button(root, text="Preview Rename", command=self.run_preview).grid(
            row=5, column=1, pady=5
        )
        tk.Button(root, text="Apply Rename", command=self.run_rename).grid(
            row=5, column=2, pady=5
        )
        tk.Button(root, text="Undo", command=self.run_undo).grid(
            row=5, column=3, pady=5
        )
        tk.Button(root, text="Load JSON", command=self.load_json).grid(
            row=5, column=4, pady=5
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
        self.log("👀 Previewing rename...")
        self.run_in_thread(
            match_and_rename_files,
            self.dir_var.get(),
            self.match_var.get(),
            self.rename_var.get(),
            self.regex_var.get(),
            dry_run=True,
            auto_yes=self.yes_var.get(),
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
            dry_run=self.dry_var.get(),
            auto_yes=self.yes_var.get(),
        )

    def run_undo(self):
        self.log("⏪ Undoing last rename...")
        self.run_in_thread(undo_from_log, "latest", auto_yes=self.yes_var.get())

    def load_json(self):
        """Load rename operations from a JSON log"""
        file_path = filedialog.askopenfilename(
            title="Select JSON Log",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON: {e}")
            return

        operations = data.get("operations", [])
        if not operations:
            messagebox.showwarning("No Operations", "No operations found in this log.")
            return

        self.loaded_operations = operations
        self.log(f"📂 Loaded {len(operations)} operations from {file_path}")
        self.log("Preview of changes:")

        for entry in operations:
            self.log(f"{Path(entry['from']).name}  ➝  {Path(entry['to']).name}")

        if messagebox.askyesno(
            "Apply Changes?", "Do you want to reapply these changes?"
        ):
            self.apply_loaded_operations()

    def apply_loaded_operations(self):
        """Apply loaded operations from JSON"""
        for entry in self.loaded_operations:
            src = Path(entry["from"])
            dest = Path(entry["to"])
            if not src.exists():
                self.log(f"⚠️ Missing file: {src}")
                continue
            if dest.exists():
                self.log(f"⚠️ Conflict: {dest} already exists, skipping")
                continue
            try:
                src.rename(dest)
                self.log(f"✅ Renamed: {src.name} ➝ {dest.name}")
            except Exception as e:
                self.log(f"❌ Failed to rename {src} → {dest}: {e}")


# if __name__ == "__main__":
#     root = tk.Tk()
#     app = RenamerGUI(root)
#     root.mainloop()


def main():
    root = tk.Tk()
    app = RenamerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
