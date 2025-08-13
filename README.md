# Proc Formatter

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](#)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Formats Pro*C source files by aligning `EXEC SQL` blocks with the surrounding C code. Each SQL block is temporarily replaced by a numbered marker, the remaining C code is processed by `clang-format`, and the original SQL text is restored.

## Quickstart

```bash
pip install proc-format
python -m proc_format input.pc output.pc
```
Ensure `clang-format` is available on your system.

## Usage

```bash
python -m proc_format input_file output_file
```

Use `-v`/`--verbose` for progress details. Repeat the flag (e.g., `-vvv`) to
increase verbosity. Warnings about skipped `sqlparse` formatting are emitted by
default; suppress them with `--terse` or silence all output with `--silent`.

### Configuration

`proc_format` can read additional EXEC SQL parsing patterns from a file named `.exec-sql-parser`. The file is searched in the directory of the input file and its ancestors with entries in lower directories overriding higher ones. Each file is a JSON object where keys are pattern names. Setting a name to `null` disables the built-in pattern; providing an object with `"pattern"` and optional `"end_pattern"` adds or replaces a pattern. A file may contain `"root": true` to stop searching for configurations in higher directories. Use `--no-registry-parents` to only consider the configuration file in the input file's directory.

## Documentation

- [User Guide](doc/User-Guide.md)
- [Developer Guide](doc/Developer-Guide.md)

## Testing

Run tests using pytest:

```bash
pytest tests/
```

## Examples

See the `examples/` directory for example inputs and expected outputs.
