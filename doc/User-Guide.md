# User Guide

This guide explains how to use **proc-format** to format Pro*C source files and how to leverage the accompanying Emacs integration.

## Command Line Usage

Format a file by running:
```bash
python -m proc_format input.pc output.pc
```
Ensure `clang-format` is installed and accessible.

## Configuration

Place a `.exec-sql-parser` JSON file in the project directory to extend or override `EXEC SQL` patterns.

## Emacs Integration

Load `exec-sql-parser.el` in Emacs to navigate `EXEC SQL` blocks within buffers. Use `M-x exec-sql-goto-next` to jump between statements or `M-x exec-sql-count-remaining` to count remaining statements.
