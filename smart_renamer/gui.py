import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

from .renamer import match_and_rename_files, test_regex, undo_from_log


class RenamerApp:
    def __init__(self, root):
        self.root = root
        root.title("Smart Renamer")

        # Folder selection
        tk.Label(root, text="Directory:").grid(row=0, column=0, sticky="w")
        self.dir_entry = tk.Entry(root, width=50)
        self.dir_entry.grid(row=0, column=1)
        tk.Button(root, text="Browse", command=self.browse_dir).grid(row=0, column=2)

        # Match pattern
        tk.Label(root, text="Match Pattern:").grid(row=1, column=0, sticky="w")
        self.match_entry = tk.Entry(root, width=50)
        self.match_entry.insert(0, "*.txt")
        self.match_entry.grid(row=1, column=1, columnspan=2)

        # Regex
        tk.Label(root, text="Regex:").grid(row=2, column=0, sticky="w")
        self.regex_entry = tk.Entry(root, width=50)
        self.regex_entry.insert(0, r"file_(\d+)")
        self.regex_entry.grid(row=2, column=1, columnspan=2)

        # Rename pattern
        tk.Label(root, text="Rename Pattern:").grid(row=3, column=0, sticky="w")
        self.rename_entry = tk.Entry(root, width=50)
        self.rename_entry.insert(0, "new_{}.txt")
        self.rename_entry.grid(row=3, column=1, columnspan=2)

        # Buttons
        tk.Button(root, text="Test Regex", command=self.test_regex).grid(
            row=4, column=0
        )
        tk.Button(root, text="Preview Rename", command=self.preview).grid(
            row=4, column=1
        )
        tk.Button(root, text="Rename", command=self.rename).grid(row=4, column=2)
        tk.Button(root, text="Undo Last", command=self.undo_last).grid(
            row=5, column=0, columnspan=3
        )

        # Output area
        self.output = scrolledtext.ScrolledText(root, width=80, height=20)
        self.output.grid(row=6, column=0, columnspan=3, pady=10)

    def browse_dir(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, folder)

    def test_regex(self):
        self.output.delete(1.0, tk.END)
        directory = self.dir_entry.get()
        match = self.match_entry.get()
        regex = self.regex_entry.get()
        test_regex(directory, match, regex)

    def preview(self):
        self.output.delete(1.0, tk.END)
        directory = Path(self.dir_entry.get())
        match = self.match_entry.get()
        regex = self.regex_entry.get()
        rename = self.rename_entry.get()
        match_and_rename_files(
            directory, match, rename, regex, dry_run=True, auto_yes=True
        )

    def rename(self):
        directory = Path(self.dir_entry.get())
        match = self.match_entry.get()
        regex = self.regex_entry.get()
        rename = self.rename_entry.get()
        match_and_rename_files(
            directory, match, rename, regex, dry_run=False, auto_yes=True
        )
        messagebox.showinfo("Done", "Renaming completed.")

    def undo_last(self):
        logs = sorted(Path.cwd().glob("smart_renamer_log_*.json"), reverse=True)
        if not logs:
            messagebox.showwarning("Undo", "No logs found in current directory.")
            return
        undo_from_log(logs[0], auto_yes=True)
        messagebox.showinfo("Undo", f"Undo completed using {logs[0].name}")


def main():
    root = tk.Tk()
    app = RenamerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
