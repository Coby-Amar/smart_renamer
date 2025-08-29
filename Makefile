# Project variables
PACKAGE = smart_renamer
APPNAME = SmartRenamer
PYTHON = python3

.PHONY: install build clean dist gui cli

setup: requirements.txt
    pip install -r requirements.txt

# Install package in editable mode (for development)
install:
	$(PYTHON) -m pip install -e .

# Build source distribution and wheel
build:
	$(PYTHON) -m build

# Build standalone GUI executable with PyInstaller
gui:
	pyinstaller --onefile --noconsole $(PACKAGE)/gui.py -n $(APPNAME)

# Build CLI executable with PyInstaller (optional)
cli:
	pyinstaller --onefile $(PACKAGE)/cli.py -n $(PACKAGE)

# Clean up build artifacts
clean:
	rm -rf build dist *.egg-info __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Full release build (wheel + sdist + executables)
dist: clean build gui cli
