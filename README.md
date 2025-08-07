
# Proc Formatter

A script for processing and formatting code.

## Usage

```bash
python -m proc_format input_file output_file
```

### Configuration

`proc_format` can read additional EXEC SQL parsing patterns from a file
named `.exec-sql-parser`.  The file is searched in the directory of the
input file and its ancestors with entries in lower directories
overriding higher ones.  Each file is a JSON object where keys are
pattern names.  Setting a name to `null` disables the built-in pattern;
providing an object with `"pattern"` and optional `"end_pattern"` adds
or replaces a pattern.  A file may contain `"root": true` to stop
searching for configurations in higher directories.  Use
`--no-registry-parents` to only consider the configuration file in the
input file's directory.

## Testing

Run tests using pytest:

```bash
pytest tests/
```

## Examples

See the `examples/` directory for example inputs and expected outputs.
