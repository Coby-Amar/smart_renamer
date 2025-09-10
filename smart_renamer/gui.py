# # SPDX-License-Identifier: MIT
# # Copyright (c) 2025 Coby Amar
import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .renamer import apply_from_config, confirm_and_apply, rename_files, undo_last


class RenamerGUI:
    def __init__(self, root):
        self.root = root
        root.title("File Renamer GUI")
        root.geometry("600x450")

        # Directory
        ttk.Label(root, text="Directory:").pack(anchor="w", padx=10, pady=2)
        frame_dir = ttk.Frame(root)
        frame_dir.pack(fill="x", padx=10)
        self.dir_entry = ttk.Entry(frame_dir)
        self.dir_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(frame_dir, text="Browse", command=self.browse_dir).pack(
            side="left", padx=5
        )

        # Match pattern
        ttk.Label(root, text="Match Pattern (Regex):").pack(anchor="w", padx=10, pady=2)
        self.match_entry = ttk.Entry(root)
        self.match_entry.pack(fill="x", padx=10)

        # Replace pattern
        ttk.Label(root, text="Replace Pattern:").pack(anchor="w", padx=10, pady=2)
        self.replace_entry = ttk.Entry(root)
        self.replace_entry.pack(fill="x", padx=10)

        # Mode & Start
        frame_mode = ttk.Frame(root)
        frame_mode.pack(anchor="w", padx=10, pady=5)
        self.mode_var = tk.StringVar(value="pattern")
        ttk.Radiobutton(
            frame_mode,
            text="Pattern",
            variable=self.mode_var,
            value="pattern",
            command=self.update_preview,
        ).pack(side="left")
        ttk.Radiobutton(
            frame_mode,
            text="Increment",
            variable=self.mode_var,
            value="increment",
            command=self.update_preview,
        ).pack(side="left")
        ttk.Label(frame_mode, text="Start:").pack(side="left", padx=5)
        self.start_entry = ttk.Entry(frame_mode, width=5)
        self.start_entry.insert(0, "1")
        self.start_entry.pack(side="left")

        # Preview list
        ttk.Label(root, text="Preview:").pack(anchor="w", padx=10)
        self.preview_list = tk.Listbox(root)
        self.preview_list.pack(fill="both", expand=True, padx=10, pady=5)

        # Buttons
        frame_buttons = ttk.Frame(root)
        frame_buttons.pack(pady=5)
        ttk.Button(frame_buttons, text="Preview", command=self.update_preview).pack(
            side="left", padx=5
        )
        ttk.Button(frame_buttons, text="Apply Rename", command=self.apply_rename).pack(
            side="left", padx=5
        )
        ttk.Button(frame_buttons, text="Undo Last", command=self.undo).pack(
            side="left", padx=5
        )
        ttk.Button(frame_buttons, text="Load Config", command=self.load_config).pack(
            side="left", padx=5
        )

    def browse_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            self.update_preview()

    def update_preview(self):
        directory = self.dir_entry.get()
        match_pattern = self.match_entry.get()
        replace_pattern = self.replace_entry.get()
        mode = self.mode_var.get()
        start = int(self.start_entry.get() or 1)

        self.preview_list.delete(0, tk.END)
        if not directory or not match_pattern or not replace_pattern:
            return

        dir_path = Path(directory)
        try:
            changes = rename_files(
                dir_path, match_pattern, replace_pattern, mode, start
            )
            for old, new in changes:
                self.preview_list.insert(tk.END, f"{old.name} -> {new.name}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def apply_rename(self):
        directory = self.dir_entry.get()
        match_pattern = self.match_entry.get()
        replace_pattern = self.replace_entry.get()
        mode = self.mode_var.get()
        start = int(self.start_entry.get() or 1)
        dir_path = Path(directory)
        changes = rename_files(dir_path, match_pattern, replace_pattern, mode, start)
        if not changes:
            messagebox.showinfo("Info", "No files to rename.")
            return
        confirm_and_apply(changes, dry_run=False, auto_confirm=False)
        self.update_preview()

    def undo(self):
        undo_last(dry_run=False, auto_confirm=False)
        self.update_preview()

    def load_config(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not file_path:
            return

        try:
            with open(file_path, "r") as f:
                config = json.load(f)

            # Apply config
            apply_from_config(file_path)

            # Update GUI fields
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, config.get("directory", "."))
            self.match_entry.delete(0, tk.END)
            self.match_entry.insert(0, config.get("match_pattern", ""))
            self.replace_entry.delete(0, tk.END)
            self.replace_entry.insert(0, config.get("replace_pattern", ""))
            self.mode_var.set(config.get("mode", "pattern"))
            self.start_entry.delete(0, tk.END)
            self.start_entry.insert(0, str(config.get("start", 1)))

            # Show preview
            self.update_preview()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")


def main():
    root = tk.Tk()
    RenamerGUI(root)
    root.mainloop()
