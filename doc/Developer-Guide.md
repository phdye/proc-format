# Developer Guide

This guide provides technical details for extending and maintaining **proc-format**.

## Architecture Overview

The Python package extracts `EXEC SQL` blocks, formats the surrounding C code with `clang-format`, and then restores the SQL text.

* `src/proc_format/core.py` – high level formatting workflow.
* `src/proc_format/registry.py` – registry of `EXEC SQL` patterns.
* `exec-sql-parser.el` – Emacs Lisp implementation mirroring the Python parser for editor tooling.

## Registry Customisation

Both the Python and Emacs implementations load pattern definitions from `.exec-sql-parser` JSON files. Entries may add, override, or remove patterns.

## Running Tests

Use `pytest` to run the test suite:
```bash
pytest tests/
```

## Documentation

Docstrings are provided throughout the codebase. The `doc/` directory contains user and developer guides.
