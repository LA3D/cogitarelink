<!-- codex.md: Development and Usage Guide for CogitareLink -->
# CogitareLink Coding Workflow (Codex)

This document outlines the recommended workflow for editing, building, and testing the CogitareLink codebase using nbdev, Jupytext, and uv (the project’s package manager). Follow these steps to make sure your changes propagate correctly between notebooks and Python modules, and that tests continue to pass.

## 1. Environment Setup
1. Create a virtual environment in .venv:
    uv venv
2. Activate the environment:
    source .venv/bin/activate
3. Install the package in development mode (with dev dependencies):
    uv pip install -e ".[dev]"

## 2. Editing Code via Notebooks and Jupytext
CogitareLink source is driven by notebooks (*.ipynb) with #| export markers. To safely edit code:

1. Pair a notebook with a percent-formatted Python file (one-time per notebook):
    jupytext --set-formats ipynb,py:percent path/to/notebook.ipynb
   This will generate path/to/notebook.py alongside the .ipynb.
2. Edit the .py file in your editor, or edit the .ipynb directly.
3. Sync changes back into the notebook:
    jupytext --sync path/to/notebook.ipynb
   This preserves cell outputs and markdown while updating code cells.
4. Mark any new public functions or classes with #| export at the top of the code cell in the notebook.

## 3. Exporting Python Modules (nbdev)
After editing notebook source, regenerate the Python library modules:
    nbdev_export
This reads all notebooks, extracts #| export cells, and rewrites the corresponding .py modules under cogitarelink/.

## 4. Building Documentation
Optionally, build or preview documentation from notebooks:
    nbdev_build_docs
    nbdev_preview    # local preview server

## 5. Testing
Use pytest for unit tests and integration tests:
    pytest -q --disable-warnings
If you add new notebooks with tests, you can also run:
    nbdev_test_nbs

## 6. Linting & Formatting
Keep code formatted with Black (88 columns). Run pre-commit hooks manually:
    pre-commit run --all-files

## 7. Incremental Development
This project follows Jeremy Howard’s incremental, test-driven style:
- Make a small change in a notebook or .py file.
- Sync with Jupytext and export via nbdev_export.
- Run tests; fix any failures immediately.
- Commit with a descriptive message.

## 8. Common Commands
Task                     ; Command
-------------------------;------------------------------------------
Create venv             ; uv venv
Install (dev mode)      ; uv pip install -e ".[dev]"
Pair notebook           ; jupytext --set-formats ipynb,py:percent NB.ipynb
Sync notebook           ; jupytext --sync NB.ipynb
Export lib modules      ; nbdev_export
Run tests               ; pytest -q --disable-warnings
Run notebook tests      ; nbdev_test_nbs
Lint & format           ; pre-commit run --all-files

---
*End of Codex Workflow Guide*