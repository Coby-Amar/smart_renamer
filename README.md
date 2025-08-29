# Smart Renamer

**Smart Renamer** is a cross-platform, regex-based file renaming utility with both **CLI** and **GUI** interfaces.  
It allows batch renaming files safely, previewing changes, and undoing operations using automatic logs.

---

## 🌟 Features

- Match files using **glob patterns** (e.g., `*.txt`)
- Extract parts of filenames using **regular expressions**
- Flexible **rename patterns** with placeholders `{}` or named groups
- **Preview renames** before applying changes
- **Undo renames** using JSON logs
- Cross-platform: **Windows, macOS, Linux**
- **CLI and GUI support**
- Standalone executables for users without Python

---

## 💻 Installation

### Clone and install

```bash
git clone https://github.com/Coby-Amar/smart_renamer.git
cd smart_renamer
pip install -e .
```

## 🚀 Usage
### Preview renaming without applying changes
```bash
smart_renamer -m "*.txt" -r "file_(\d+)" -p "doc_{}.txt" --dry-run
```

### Apply renaming
```bash
smart_renamer -m "*.txt" -r "file_(\d+)" -p "doc_{}.txt"
```

### Undo last rename operation
```bash
smart_renamer --undo latest
```

## 🛠 Development

### Install package in development mode
```bash
make install
```

### Build Python wheel + source distribution
```bash
make build
```

### Build standalone GUI
```bash
make gui
```

### Build standalone CLI executable
```bash
make cli
```

### Full release build (package + GUI + CLI)
```bash
make dist
```

### Clean build artifacts
```bash
make clean
```

## 📝 Examples
```bash
smart_renamer -m "*.txt" -r "file_(\d+)" -p "doc_{}.txt"
```