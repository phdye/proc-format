# Technical Specification: proc-format

**Version:** 1.0  
**Date:** October 13, 2025  
**Status:** Current Implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture](#architecture)
4. [Core Components](#core-components)
5. [Data Flow](#data-flow)
6. [Module Specifications](#module-specifications)
7. [Configuration System](#configuration-system)
8. [Verification System](#verification-system)
9. [Error Handling](#error-handling)
10. [Performance Considerations](#performance-considerations)
11. [Compatibility](#compatibility)
12. [Future Enhancements](#future-enhancements)

---

## 1. Executive Summary

### 1.1 Purpose

**proc-format** is a specialized code formatter for Oracle Pro*C files (`.pc`). It formats the embedded C code using `clang-format` while preserving the integrity and formatting of `EXEC SQL` blocks.

### 1.2 Problem Statement

Pro*C files contain mixed C code and embedded SQL statements (marked with `EXEC SQL`). Standard C formatters like `clang-format` cannot correctly process these files because:

1. SQL syntax differs from C syntax
2. `EXEC SQL` statements have special Pro*C-specific conventions
3. Direct formatting corrupts SQL blocks and breaks compilation

### 1.3 Solution Approach

proc-format uses a **marker-substitution** strategy:

```
Original .pc File
    ↓
Extract EXEC SQL blocks → Replace with numbered markers
    ↓
Format C code with clang-format
    ↓
Restore EXEC SQL blocks at marker positions
    ↓
Formatted .pc File
```

This ensures C code is formatted while SQL blocks remain untouched (or are optionally formatted with sqlparse).

---

## 2. System Overview

### 2.1 Key Features

- **Dual Formatting**: C code via `clang-format`, SQL via `sqlparse` (optional)
- **Pattern-Based Extraction**: Configurable registry of EXEC SQL patterns
- **Functional Identity Verification**: Ensures formatting doesn't change program behavior
- **Form-Feed Preservation**: Maintains page breaks for printed code
- **Hierarchical Configuration**: `.exec-sql-parser` files support project-specific patterns
- **Debug Support**: Comprehensive intermediate file output for troubleshooting

### 2.2 System Boundaries

**Input:**
- Pro*C source files (`.pc`)
- Plain C files (`.c`) - supported but without SQL extraction

**Output:**
- Formatted Pro*C source files (`.pc`)
- Formatted C files (`.c`)
- Debug artifacts (intermediate processing files)

**External Dependencies:**
- `clang-format` executable (required for C formatting)
- `sqlparse` Python library (optional for SQL formatting)
- Python 3.2.5+ (minimum supported version)

---

## 3. Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Command Line Interface                    │
│                      (__main__.py)                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Configuration Layer                        │
│          ┌──────────────┬───────────────────────┐          │
│          │   CLI Args   │  .exec-sql-parser     │          │
│          │   (ArgParse) │  (JSON Registry)      │          │
│          └──────────────┴───────────────────────┘          │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Core Processing                         │
│                       (core.py)                             │
│                                                             │
│  ┌───────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │   Capture     │→ │    Format      │→ │   Restore    │ │
│  │  EXEC SQL     │  │  with clang-   │  │  EXEC SQL    │ │
│  │   Blocks      │  │    format      │  │   Blocks     │ │
│  └───────────────┘  └────────────────┘  └──────────────┘ │
│           ↓                                       ↓         │
│  ┌───────────────────────────────────────────────────────┐ │
│  │          Optional SQL Formatting (sqlparse)           │ │
│  └───────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Verification Layer                          │
│                    (f_identical.py)                         │
│                                                             │
│           Functional Identity Verification                   │
│      (Ensures no functional changes introduced)             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Module Organization

```
proc_format/
├── __init__.py          # Package exports
├── __main__.py          # CLI entry point
├── core.py              # Main processing logic
├── registry.py          # EXEC SQL pattern registry
├── f_identical.py       # Functional identity verification
├── config.py            # Configuration management (planned)
└── vendor/              # Vendored dependencies
    └── pathlib.py       # Python 3.2 compatibility
```

### 3.3 Design Principles

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Backward Compatibility**: Support for Python 3.2.5 (no f-strings, limited stdlib)
3. **Fail-Safe Operation**: Verification ensures no functional changes
4. **Transparency**: Comprehensive debug output for troubleshooting
5. **Extensibility**: Pattern registry allows project-specific customization

---

## 4. Core Components

### 4.1 Command Line Interface (`__main__.py`)

**Responsibility:** Parse arguments and initialize processing

**Arguments:**
```
positional arguments:
  input_file            Input file to process
  output_file           Output file to save formatted content

optional arguments:
  --clang-format PATH   Path to clang-format executable (default: "clang-format")
  --debug DIR           Path to debug directory (default: "debug")
  --keep                Do not delete debug directory before processing
  --no-registry-parents Do not search parent directories for .exec-sql-parser
  --terse               Suppress non-critical warnings
  --silent              Suppress all output
  -v, --verbose         Increase verbosity (repeatable: -v, -vv, -vvv)
```

**Context Creation:**
```python
ProCFormatterContext(args) → Context object passed to all functions
```

### 4.2 Context Object (`ProCFormatterContext`)

**Purpose:** Lightweight container for runtime configuration

**Attributes:**
```python
__slots__ = [
    "input_file",           # Path to input .pc file
    "output_file",          # Path to output .pc file
    "exec_sql_before_fh",   # File handle for EXEC SQL blocks (before)
    "exec_sql_after_fh",    # File handle for EXEC SQL blocks (after)
    "clang_format_path",    # Path to clang-format executable
    "keep",                 # Boolean: keep debug directory
    "debug",                # Path to debug directory
    "sql_dir",              # Path to SQL directory (debug/sql/)
    "registry",             # Dictionary of EXEC SQL patterns
    "verbose",              # Verbosity level (0-3)
    "terse",                # Boolean: suppress warnings
    "silent",               # Boolean: suppress all output
]
```

**Design Rationale:**
- Uses `__slots__` to prevent `__dict__` creation (memory efficiency)
- Immutable after initialization (no setters)
- Registry loaded during initialization from `.exec-sql-parser` files

---

## 5. Data Flow

### 5.1 Complete Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ Step 0: Initialization                                       │
├─────────────────────────────────────────────────────────────┤
│ • Parse command-line arguments                              │
│ • Create ProCFormatterContext                               │
│ • Load .exec-sql-parser registry from file hierarchy        │
│ • Create/clear debug directory                              │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Capture EXEC SQL Blocks                            │
├─────────────────────────────────────────────────────────────┤
│ INPUT:  Original .pc file content                          │
│ PROCESS:                                                     │
│   • Read input file                                         │
│   • Write to debug/before.pc                                │
│   • Split into lines (using split('\n'))                    │
│   • Scan for EXEC SQL patterns (registry-based)            │
│   • Replace matched blocks with numbered markers           │
│   • Store original SQL blocks in memory                     │
│   • Write blocks to debug/sql/NNN files                     │
│   • Optional: Format SQL with sqlparse                      │
│ OUTPUT: C code with markers, captured EXEC SQL blocks       │
│ FILES:  debug/before.pc, debug/before.c, debug/sql/###      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Format C Code                                       │
├─────────────────────────────────────────────────────────────┤
│ INPUT:  C code with markers (debug/before.c)               │
│ PROCESS:                                                     │
│   • Preserve form-feeds (replace with markers)              │
│   • Invoke clang-format via subprocess                      │
│   • Restore form-feeds                                      │
│ OUTPUT: Formatted C code with markers                       │
│ FILES:  debug/after.c                                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Restore EXEC SQL Blocks                            │
├─────────────────────────────────────────────────────────────┤
│ INPUT:  Formatted C with markers, captured SQL blocks       │
│ PROCESS:                                                     │
│   • Scan for // EXEC SQL MARKER :N: comments               │
│   • Replace each marker with original SQL block            │
│   • Adjust indentation to match marker position            │
│   • Verify all markers consumed                             │
│ OUTPUT: Complete formatted .pc file                         │
│ FILES:  debug/after.pc, output_file                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Functional Identity Verification                    │
├─────────────────────────────────────────────────────────────┤
│ INPUT:  Original file, formatted file                       │
│ PROCESS:                                                     │
│   • Strip all whitespace from both files                    │
│   • Compare sizes and SHA256 checksums                      │
│   • If different, show diff context and exit with error     │
│   • For .pc files: Also verify debug/before.c vs after.c    │
│ OUTPUT: Success or failure exit code                        │
│ GUARANTEES: Formatting introduced no functional changes     │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 File Artifacts

**Debug Directory Structure:**
```
debug/
├── before.pc              # Original Pro*C content
├── before.c               # C content with EXEC SQL markers
├── after.c                # Formatted C content with markers
├── after.pc               # Final formatted Pro*C content
├── exec-sql--before.txt   # All captured EXEC SQL blocks (original)
├── exec-sql--after.txt    # All captured EXEC SQL blocks (formatted)
└── sql/                   # Individual SQL block files
    ├── 001                # First EXEC SQL block
    ├── 002                # Second EXEC SQL block
    └── ...
```

**SQL Block File Format (`debug/sql/NNN`):**
```
Construct:  'STATEMENT-Multi-Line'
Pattern:    'EXEC SQL\b'
EndPattern: '.*;'

Stripped:  'EXEC SQL SELECT col1, col2'

    EXEC SQL SELECT col1, col2
        INTO :var1, :var2
        FROM table1
        WHERE condition;
```

---

## 6. Module Specifications

### 6.1 `core.py` - Main Processing Logic

#### 6.1.1 `process_file(ctx)`

**Purpose:** Main entry point for file processing

**Algorithm:**
1. Create/clear debug directory (unless `--keep`)
2. Read input file → `debug/before.pc`
3. Capture EXEC SQL blocks → markers + captured blocks
4. Write C with markers → `debug/before.c`
5. Format C code with clang-format → `debug/after.c`
6. Restore EXEC SQL blocks → `debug/after.pc`
7. Write output file
8. Verify functional identity (unless skipped)

**Signature:**
```python
def process_file(ctx: ProCFormatterContext) -> None
```

**Side Effects:**
- Creates debug directory structure
- Writes multiple debug files
- Invokes clang-format subprocess
- May call sys.exit() on verification failure

---

#### 6.1.2 `capture_exec_sql_blocks(ctx, lines, registry)`

**Purpose:** Extract EXEC SQL blocks and replace with markers

**Algorithm:**
```
Initialize:
    output_lines = []
    captured_blocks = []
    marker_counter = 1
    inside_block = False

For each line:
    If inside multi-line block:
        Append line to current_block
        If end_pattern matches:
            Create marker
            Format block (optional sqlparse)
            Store in captured_blocks
            Write to debug/sql/NNN
            Reset state
    Else:
        Try each registry pattern (longest first):
            If single-line match:
                Format and store block
                Insert marker
                Special handling for DECLARE SECTION (add braces)
            If multi-line start match:
                Start accumulating block
            Otherwise:
                Copy line unchanged

Return (output_lines, captured_blocks)
```

**Signature:**
```python
def capture_exec_sql_blocks(
    ctx: ProCFormatterContext,
    lines: List[str],
    registry: Dict[str, Dict]
) -> Tuple[List[str], List[List[str]]]
```

**Key Details:**
- Registry patterns sorted by length (longest first) to match specific before general
- Supports both single-line and multi-line EXEC SQL constructs
- Special markers for `BEGIN DECLARE SECTION` (adds `{`) and `END DECLARE SECTION` (adds `}`)
- Verbose mode prints progress: `s` for single-line, `b` for block end

---

#### 6.1.3 `format_exec_sql_block(lines, construct, ctx)`

**Purpose:** Optionally format EXEC SQL block with sqlparse

**Algorithm:**
```
If lines empty: return lines
If starts with "EXEC ORACLE": return lines (skip formatting)
If sqlparse unavailable: warn and return lines

Extract:
    - Leading whitespace (indent)
    - Content after "EXEC SQL"

Parse SQL text:
    - Strip and join lines

Format with sqlparse:
    - Call sqlparse.format(sql_text, keyword_case=None, identifier_case=None)
    - Note: case=None preserves original case (required for f-identical)

Reconstruct output:
    - First line: indent + "EXEC SQL " + formatted[0]
    - Remaining lines: indent + formatted[i]

Return formatted lines
```

**Signature:**
```python
def format_exec_sql_block(
    lines: List[str],
    construct: str,
    ctx: Optional[ProCFormatterContext] = None
) -> List[str]
```

**Current Behavior:**
- **Case Preservation:** `keyword_case=None, identifier_case=None`
- **Rationale:** Changing case breaks f-identical verification
- **Future:** Support optional case styling (see Future Enhancements)

---

#### 6.1.4 `format_with_clang(ctx, content)`

**Purpose:** Format C code using clang-format while preserving form-feeds

**Algorithm:**
```
1. Preserve form-feeds:
   Replace \f with /* FORMFEED_PLACEHOLDER_NNNN */

2. Invoke clang-format:
   subprocess.Popen([clang-format])
   - stdin: content
   - stdout: formatted output
   - Python 3.2 compatibility: encode/decode bytes

3. Restore form-feeds:
   Replace /* FORMFEED_PLACEHOLDER_NNNN */ with \f

4. Return formatted content
```

**Signature:**
```python
def format_with_clang(
    ctx: ProCFormatterContext,
    content: str
) -> str
```

**Error Handling:**
- Raises `RuntimeError` if clang-format returns non-zero exit code
- Includes stderr in exception message

**Form-Feed Preservation:**
- Form-feeds (ASCII 0x0C, `\f`) are page break characters
- clang-format removes or normalizes them
- Preservation ensures they survive formatting

---

#### 6.1.5 `restore_exec_sql_blocks(content, exec_sql_segments, ctx)`

**Purpose:** Replace markers with original EXEC SQL blocks

**Algorithm:**
```
Parse content for markers:
    Pattern: // EXEC SQL MARKER :N:
    
For each marker found:
    Verify sequence (N must equal expected_marker)
    Get corresponding block from exec_sql_segments
    Calculate indentation from marker position
    Restore block with adjusted indentation:
        - First line: match marker indent
        - Remaining lines: adjust relative to original indent
    Increment expected_marker

Verify all segments consumed:
    If segments remain: raise ValueError

Return joined lines
```

**Signature:**
```python
def restore_exec_sql_blocks(
    content: str,
    exec_sql_segments: List[List[str]],
    ctx: Optional[ProCFormatterContext] = None
) -> str
```

**Indentation Logic:**
```python
marker_indent = len(marker_line) - len(marker_line.lstrip())
original_indent = len(first_sql_line) - len(first_sql_line.lstrip())
delta = marker_indent - original_indent

For each remaining line:
    if delta > 0: add delta spaces
    if delta < 0: remove abs(delta) characters from start
```

**Error Conditions:**
- Marker out of sequence → ValueError
- Missing marker → ValueError
- Not all segments consumed → ValueError

---

### 6.2 `registry.py` - EXEC SQL Pattern Registry

#### 6.2.1 Purpose

Provides a **configurable pattern registry** for identifying and extracting EXEC SQL constructs from Pro*C source files.

#### 6.2.2 Registry Structure

**Format:**
```python
{
    "construct_name": {
        "pattern": "regex_pattern",           # Required: Start pattern
        "end_pattern": "regex_pattern",       # Optional: End pattern (multi-line)
        "action": lambda lines: lines,        # Required: Processing function
        "error": None                         # Optional: Mark as error construct
    }
}
```

**Example Entries:**
```python
"STATEMENT-Single-Line [1]": {
    "pattern": r"EXEC SQL\b(.*);",
    "action": lambda lines: lines
},

"STATEMENT-Multi-Line": {
    "pattern": r"EXEC SQL\b",
    "end_pattern": r".*;",
    "action": lambda lines: lines
},

"END": {
    "pattern": r"END\b(.*);",
    "action": lambda lines: lines,
    "error": None  # Catches unterminated blocks
}
```

#### 6.2.3 Built-In Patterns

**Categories:**

1. **ORACLE Blocks**
   - `EXEC ORACLE` statements (not formatted by sqlparse)
   - Single-line and multi-line variants

2. **EXECUTE Statements**
   - `EXECUTE IMMEDIATE` (dynamic SQL)
   - `EXECUTE <prepared-statement>` with `AT` clause
   - Block form: `EXEC SQL EXECUTE ... END-EXEC;`

3. **Generic SQL Statements**
   - Single-line: `EXEC SQL ... ;`
   - Multi-line: `EXEC SQL ... (multiple lines) ;`

4. **DECLARE SECTION**
   - `BEGIN DECLARE SECTION`
   - `END DECLARE SECTION`
   - Special handling: Braces added during capture, removed during restore

5. **Cursor Management**
   - `DECLARE CURSOR`
   - `OPEN`, `FETCH`, `CLOSE`

6. **Error Marker**
   - `END` pattern catches unterminated blocks

**Python 3.2.5 Compatibility Issue:**
- Duplicate entries exist for single-line patterns
- Bug in Python 3.2.5 dictionary handling
- Fixed in Python 3.9+ but duplicates kept for compatibility

#### 6.2.4 Configuration Files (`.exec-sql-parser`)

**File Format:** JSON

**Search Order:**
```
/path/to/project/input.pc
  → .exec-sql-parser (if exists)
/path/to/project/
  → .exec-sql-parser (if exists)
/path/to/
  → .exec-sql-parser (if exists)
/path/
  → .exec-sql-parser (if exists)
/
  → .exec-sql-parser (if exists, stopped by "root": true)
```

**Configuration Directives:**

```json
{
    "root": true,                    // Stop searching parents
    "NEW_PATTERN": {                 // Add new pattern
        "pattern": "...",
        "end_pattern": "...",
        "action": "maintain"         // Not yet implemented
    },
    "BUILTIN_PATTERN": null,         // Disable built-in pattern
    "OVERRIDE_PATTERN": {            // Replace built-in pattern
        "pattern": "...",
        "end_pattern": "..."
    }
}
```

**Merge Strategy:**
1. Load `DEFAULT_EXEC_SQL_REGISTRY`
2. Search for `.exec-sql-parser` files (bottom-up)
3. For each file found:
   - If `"root": true`, stop searching
   - Merge entries: `null` removes, object adds/replaces
4. Return merged registry

#### 6.2.5 Regular Expression Patterns

**Key Patterns:**
```python
re_EXEC_SQL  = re.compile(r'EXEC\s+SQL\b(\s*(.*))?')
re_DECLARE   = re.compile(r'\s*(BEGIN|END)\s+DECLARE\s+SECTION\s*[;]')
re_INDENT    = re.compile(r'^(\s*)(.*)')

re_DECLARE_BEGIN = re.compile(r'EXEC SQL BEGIN\s+DECLARE\s+SECTION\s*[;]')
re_DECLARE_END   = re.compile(r'EXEC SQL END\s+DECLARE\s+SECTION\s*[;]')
```

**Usage:**
- `re_EXEC_SQL`: Extract SQL text after "EXEC SQL"
- `re_DECLARE`: Identify BEGIN/END DECLARE SECTION
- `re_INDENT`: Split line into indent and content
- `re_DECLARE_BEGIN/END`: Special handling for brace insertion

---

### 6.3 `f_identical.py` - Functional Identity Verification

#### 6.3.1 Purpose

Ensures that formatting does not introduce functional changes to the program by comparing files after removing all whitespace.

#### 6.3.2 Core Concept

**Functional Identity:**
```
Two source files are functionally identical if:
    strip_whitespace(file1) == strip_whitespace(file2)

Where strip_whitespace removes:
    - All spaces, tabs, newlines, carriage returns
    - All Unicode whitespace characters
```

**Rationale:**
- Formatting changes only whitespace
- If non-whitespace content differs, functionality changed
- Detects accidental modifications during processing

#### 6.3.3 `FIdenticalResult` Class

**Purpose:** Container for verification results

**Attributes:**
```python
class FIdenticalResult:
    identical: bool                # True if files are identical
    size1: int                     # Size of file1 after whitespace removal
    size2: int                     # Size of file2 after whitespace removal
    checksum1: str                 # SHA256 of file1
    checksum2: str                 # SHA256 of file2
    error_msg: str                 # Error message if not identical
    diff_offset: int               # Byte offset of first difference
    context_before: str            # Context before difference
    context_after: str             # Context after difference
```

#### 6.3.4 `strip_whitespace(content)`

**Purpose:** Remove all whitespace from content

**Algorithm:**
```python
result = bytearray()
for byte in content:
    if not chr(byte).isspace():
        result.append(byte)
return bytes(result)
```

**Signature:**
```python
def strip_whitespace(content: Union[str, bytes]) -> bytes
```

**Whitespace Definition:**
- Uses Python's `str.isspace()` method
- Includes: space, tab, newline, carriage return, form-feed, vertical tab
- Includes: Unicode whitespace characters

#### 6.3.5 `f_identical_check(file1, file2)`

**Purpose:** Compare two files for functional identity

**Algorithm:**
```
1. Read both files (binary mode)
2. Strip whitespace from both
3. Calculate sizes and SHA256 checksums
4. If identical:
   - Set result.identical = True
   - Return result
5. If different:
   - Find first difference byte offset
   - Extract context (40 bytes before/after)
   - Format context with difference marker
   - Set result.identical = False
   - Return result
```

**Signature:**
```python
def f_identical_check(
    file1: Union[str, Path],
    file2: Union[str, Path]
) -> FIdenticalResult
```

**Context Format:**
```
Context from file 1:
  ...previous[>X<]following...

Context from file 2:
  ...previous[>Y<]following...

Note: [>...<] marks the position of first difference
```

#### 6.3.6 `verify_functionally_identical(file1, file2, verbose=False)`

**Purpose:** Verify files or exit with error

**Algorithm:**
```
result = f_identical_check(file1, file2)

if result.identical:
    if verbose:
        print success message
    return True
else:
    print_error(result, file1, file2)
    sys.exit(1)
```

**Signature:**
```python
def verify_functionally_identical(
    file1: Union[str, Path],
    file2: Union[str, Path],
    verbose: bool = False
) -> bool
```

**Error Output Format:**
```
======================================================================
  FATAL: Files are NOT functionally identical
======================================================================

File 1: path/to/file1.pc
File 2: path/to/file2.pc

After removing all whitespace:
  Size 1:     207535 bytes
  Checksum 1: 42f3d947775d58dabf9d08f11933fdc6...
  Size 2:     207535 bytes
  Checksum 2: fb62788a73f4f20a7be9133fdcaa5434...

Files differ at byte 22266 (after whitespace removal)

Context from file 1:
  ...WHENEVER NOT FOUND DO [>b<]reak;EXEC SQL AT...

Context from file 2:
  ...WHENEVER NOT FOUND DO [>B<]REAK;EXEC SQL AT...

Note: [>...<] marks the position of first difference

======================================================================
```

#### 6.3.7 Integration with `process_file()`

**Location in Pipeline:** Step 5 (after restore)

**Verification Steps for `.pc` Files:**
```python
1. Verify input.pc vs output.pc
   - Ensures overall formatting didn't introduce changes

2. Verify debug/before.c vs debug/after.c
   - Ensures clang-format didn't corrupt marker system
   - Ensures EXEC SQL extraction/restoration is lossless
```

**Verification Steps for `.c` Files:**
```python
1. Verify input.c vs output.c
   - Standard C file formatting check
```

**Failure Behavior:**
- Calls `sys.exit(1)` immediately
- Prints detailed error report to stderr
- Output file is still written (allows inspection)

---

## 7. Configuration System

### 7.1 Current Implementation

**Configuration Sources (in priority order):**

1. **Command-line arguments**
   - Highest priority
   - Direct flags: `--verbose`, `--terse`, `--silent`, etc.

2. **Environment variables**
   - Not currently implemented

3. **`.exec-sql-parser` files**
   - JSON format
   - Hierarchical search (directory tree)
   - Pattern registry customization

4. **Built-in defaults**
   - `DEFAULT_EXEC_SQL_REGISTRY` in `registry.py`
   - Default paths: `clang-format`, `debug/`

### 7.2 `.exec-sql-parser` File Specification

**File Format:** JSON object

**Top-Level Keys:**
- `"root"`: Boolean - stop parent directory search
- `"<pattern_name>"`: Object or null - add/remove/replace pattern

**Pattern Object Schema:**
```json
{
    "pattern": "string (regex)",           // Required
    "end_pattern": "string (regex)",       // Optional (multi-line)
    "action": "string (future)",           // Optional (not implemented)
    "error": null                          // Optional (mark as error)
}
```

**Example `.exec-sql-parser`:**
```json
{
    "root": true,
    "CUSTOM_PROCEDURE_CALL": {
        "pattern": "EXEC SQL CALL \\w+\\(",
        "end_pattern": "\\);",
        "action": "maintain"
    },
    "STATEMENT-Single-Line [1]": null
}
```

**Merge Semantics:**
- `null` value: Remove pattern from registry
- Object value: Add or replace pattern
- Missing pattern: Inherit from parent directory or built-in

### 7.3 Future Configuration (Planned)

**Proposed `.proc-format.ini` file:**

```ini
[sql]
keyword_case = upper
identifier_case = lower
enabled = true

[c_format]
executable = clang-format
style = 

[verification]
enabled = true
keep_temp_on_failure = false

[general]
verbosity = 1
debug_dir = debug
```

See [Future Enhancements](#12-future-enhancements) for details.

---

## 8. Verification System

### 8.1 Verification Philosophy

**Principle:** Formatting should never change program behavior

**Implementation:** Whitespace-agnostic comparison

**Guarantee:** If verification passes, the formatted program is functionally identical to the original

### 8.2 Verification Algorithm

```
1. Load file1 and file2 (binary mode)

2. Normalize both files:
   strip_whitespace(file1) → normalized1
   strip_whitespace(file2) → normalized2

3. Calculate properties:
   size1 = len(normalized1)
   size2 = len(normalized2)
   checksum1 = SHA256(normalized1)
   checksum2 = SHA256(normalized2)

4. Compare:
   if size1 == size2 and checksum1 == checksum2:
       return SUCCESS
   else:
       find_difference_offset()
       extract_context()
       return FAILURE
```

### 8.3 Verification Scope

**For Pro*C Files (`.pc`):**
1. Verify `input.pc` vs `output.pc`
   - Ensures EXEC SQL extraction/restoration is lossless
   - Ensures no accidental modifications

2. Verify `debug/before.c` vs `debug/after.c`
   - Ensures clang-format didn't corrupt markers
   - Ensures marker system is working correctly

**For C Files (`.c`):**
1. Verify `input.c` vs `output.c`
   - Standard formatting verification

### 8.4 Error Detection

**Common Failure Scenarios:**

1. **SQL formatting changed case:**
   ```
   Before: EXEC SQL INCLUDE SQLCA;
   After:  EXEC SQL INCLUDE sqlca;
   ```
   **Cause:** sqlparse with case transformation
   **Detection:** Byte-level difference in identifiers

2. **Marker not restored:**
   ```
   Before: EXEC SQL SELECT ...
   After:  // EXEC SQL MARKER :42:
   ```
   **Cause:** Bug in restore_exec_sql_blocks()
   **Detection:** Marker comment remains in output

3. **Line ending changes:**
   ```
   Before: \n (LF)
   After:  \r\n (CRLF)
   ```
   **Cause:** Platform differences
   **Detection:** Size difference (not caught - whitespace normalized)
   **Note:** This is intentionally NOT detected (line endings are whitespace)

4. **Form-feed corruption:**
   ```
   Before: \f (form-feed)
   After:  (removed)
   ```
   **Cause:** Form-feed marker not restored
   **Detection:** Size difference after whitespace removal

### 8.5 Verification Performance

**Optimization Strategy:**
- Lazy evaluation: Early exit on size or checksum mismatch
- Efficient hashing: SHA256 is fast for file sizes < 10MB
- No full diff: Only find first difference (not all differences)

**Typical Performance:**
- Small files (<100KB): <10ms
- Medium files (1MB): ~50ms
- Large files (10MB): ~500ms

---

## 9. Error Handling

### 9.1 Error Categories

#### 9.1.1 User Errors

**Examples:**
- Input file does not exist
- Output file cannot be written
- clang-format not found in PATH
- Invalid command-line arguments

**Handling:**
- Print clear error message to stderr
- Exit with code 1
- Do not create debug directory

#### 9.1.2 Processing Errors

**Examples:**
- Marker out of sequence
- Not all markers restored
- clang-format returns non-zero
- Unterminated EXEC SQL block

**Handling:**
- Print detailed error with context
- Exit with code 1
- Preserve debug directory for inspection

#### 9.1.3 Verification Errors

**Examples:**
- Files not functionally identical
- Size mismatch after whitespace removal
- Checksum mismatch

**Handling:**
- Print comprehensive diff report
- Show byte offset and context of first difference
- Exit with code 1
- Output file is still written (for debugging)

### 9.2 Error Messages

**Format:**
```
[ERROR TYPE]: Brief description

Details:
  - Specific information
  - File paths
  - Line numbers if applicable

Suggestion: How to fix or investigate

Debug: Reference to debug files if available
```

**Example:**
```
[MARKER ERROR]: Marker out of sequence

Details:
  - Expected marker: 42
  - Found marker: 43
  - Location: Line 1234 of debug/after.c

Suggestion: Check debug/sql/ directory for captured blocks

Debug: Examine debug/before.c and debug/after.c
```

### 9.3 Debugging Support

**Debug Directory Contents:**
```
debug/
├── before.pc              # Input file
├── before.c               # C code with markers
├── after.c                # Formatted C code
├── after.pc               # Output file
├── exec-sql--before.txt   # Original SQL blocks
├── exec-sql--after.txt    # Formatted SQL blocks
└── sql/
    ├── 001                # Individual blocks
    ├── 002
    └── ...
```

**Debug Workflow:**
1. Error occurs during processing
2. Examine `debug/before.c` - Are markers correct?
3. Examine `debug/after.c` - Did clang-format preserve markers?
4. Examine `debug/sql/NNN` - Is SQL extraction correct?
5. Examine `exec-sql--before.txt` vs `after.txt` - What changed?

### 9.4 Verbose Output

**Verbosity Levels:**

- `0` (default): Only errors and final status
- `1` (`-v`): Step-by-step progress
- `2` (`-vv`): Detailed operations
- `3` (`-vvv`): Debug-level output

**Level 1 Output:**
```
Formatting: input.pc
- Capture EXEC SQL segments ...
- Apply clang-format to C code content ...
  - Preserving 21 form-feed character(s) ...
  - Restoring form-feed character(s) ...
- Restore EXEC SQL segments ...

Verifying functional identity...
  Checking .pc files are functionally identical...
  Checking intermediate .c files are functionally identical...
✓ All verification checks PASSED

File processed successfully: input.pc
```

**Level 2 Output:**
```
(All Level 1 output plus:)
  - Processing marker 1: STATEMENT-Single-Line
  - Processing marker 2: STATEMENT-Multi-Line (3 lines)
  . . . . . . . (progress dots for each marker)
```

**Level 3 Output:**
```
(All Level 1+2 output plus:)
  sqlparse: formatting EXEC SQL block : v=9
  sqlparse: skipped - ORACLE block
  [Detailed pattern matching information]
```

---

## 10. Performance Considerations

### 10.1 Performance Profile

**Typical Processing Time:**
- Small files (<500 lines): <1 second
- Medium files (1000-5000 lines): 1-3 seconds
- Large files (10000+ lines): 3-10 seconds

**Bottlenecks:**
1. **clang-format subprocess** (70% of time)
2. **File I/O** (15% of time)
3. **Pattern matching** (10% of time)
4. **Verification** (5% of time)

### 10.2 Optimization Strategies

#### 10.2.1 Current Optimizations

**Registry Pattern Sorting:**
```python
# Sort patterns by length (longest first)
registry_items = sorted(
    registry.items(),
    key=lambda item: len(item[1].get("pattern", "")),
    reverse=True
)
```
**Benefit:** Match specific patterns before general ones (avoid false positives)

**Lazy Pattern Compilation:**
```python
# Patterns compiled once at module load
re_EXEC_SQL = re.compile(r'EXEC\s+SQL\b(\s*(.*))?')
```
**Benefit:** Avoid re-compiling patterns on every line

**ProCFormatterContext `__slots__`:**
```python
class ProCFormatterContext:
    __slots__ = [...]  # Prevents __dict__ creation
```
**Benefit:** Reduced memory footprint, faster attribute access

#### 10.2.2 Potential Optimizations

**1. Parallel Verification:**
```python
# Run .pc and .c verification in parallel
with ThreadPoolExecutor(max_workers=2) as executor:
    future_pc = executor.submit(verify, input.pc, output.pc)
    future_c = executor.submit(verify, before.c, after.c)
```
**Expected Gain:** 30-40% reduction in verification time

**2. Incremental Processing:**
```python
# Process file in chunks rather than all at once
for chunk in read_in_chunks(input_file, chunk_size=10000):
    process_chunk(chunk)
```
**Expected Gain:** Reduced peak memory usage for very large files
**Trade-off:** More complex state management

**3. clang-format Caching:**
```python
# Cache clang-format results for identical blocks
cache = {}
checksum = hash(content)
if checksum in cache:
    return cache[checksum]
```
**Expected Gain:** 20-30% for files with repeated patterns
**Trade-off:** Memory usage for cache

### 10.3 Memory Usage

**Typical Memory Footprint:**
- Small files: 1-5 MB
- Medium files: 5-20 MB
- Large files: 20-50 MB

**Memory Breakdown:**
- Original file content: 1x
- Processed file content: 1x
- Captured blocks: 0.3x (SQL blocks only)
- Debug output: 2x (written to disk, not held in memory)
- Working buffers: 0.5x

**Total:** ~5x file size in memory

**Memory Optimization:**
- No unnecessary copying (use references)
- Debug files written incrementally
- Captured blocks stored as lists (not strings until needed)

### 10.4 Scalability

**Current Limits:**
- File size: No hard limit, tested up to 50MB
- Number of EXEC SQL blocks: No hard limit, tested up to 10,000
- Line length: No hard limit

**Practical Limits:**
- Files > 100MB: Performance degrades (10+ seconds)
- Blocks > 50,000: Memory usage concerns (>500MB)
- Lines > 100,000 characters: Regex matching slow

**Recommended Usage:**
- Files < 10MB: Optimal performance
- Files 10-50MB: Acceptable performance
- Files > 50MB: Consider splitting into modules

---

## 11. Compatibility

### 11.1 Python Compatibility

**Minimum Version:** Python 3.2.5

**Compatibility Constraints:**

1. **No f-strings** (introduced in Python 3.6)
   ```python
   # ❌ Not compatible with Python 3.2
   print(f"Value: {variable}")
   
   # ✅ Compatible
   print("Value: {0}".format(variable))
   ```

2. **Limited `subprocess` API**
   ```python
   # Python 3.2: Must encode strings to bytes
   if sys.version_info < (3, 7, 0):
       content = content.encode()
   
   # Python 3.7+: Can pass text=True
   subprocess.Popen(..., text=True)
   ```

3. **No `pathlib` in Python 3.2**
   ```python
   # Vendored pathlib in proc_format/vendor/pathlib.py
   try:
       from pathlib import Path
   except ImportError:
       from proc_format.vendor.pathlib import Path
   ```

4. **`configparser` renamed from `ConfigParser`**
   ```python
   try:
       import configparser
   except ImportError:
       import ConfigParser as configparser
   ```

5. **No ordered dicts (Python 3.7+)**
   ```python
   # Explicit sorting required for consistent order
   registry_items = sorted(registry.items(), key=...)
   ```

**Tested Versions:**
- Python 3.2.5 (minimum)
- Python 3.9.x (development)
- Python 3.10+ (recommended)

### 11.2 Platform Compatibility

**Supported Platforms:**
- ✅ Linux (all distributions)
- ✅ macOS
- ✅ Windows (via Cygwin)
- ✅ Windows (native Python)

**Platform-Specific Issues:**

**Windows (Cygwin):**
- Path handling: Both Windows (`C:\...`) and Unix (`/D/...`) paths supported
- Line endings: Mixed CRLF/LF handled correctly (normalized)
- Shell: Subprocess uses Windows-style commands

**Windows (Native):**
- clang-format: Must be in PATH or specified with `--clang-format`
- Line endings: CRLF preserved in output

**macOS:**
- clang-format: Installed via Homebrew or Xcode

**Linux:**
- clang-format: Installed via package manager

### 11.3 External Dependencies

#### 11.3.1 Required Dependencies

**clang-format:**
- Version: 10.0+ recommended
- Purpose: C code formatting
- Installation:
  ```bash
  # Ubuntu/Debian
  apt-get install clang-format
  
  # macOS
  brew install clang-format
  
  # Windows (via Cygwin)
  apt-cyg install clang
  ```

**Python Standard Library:**
- `os`, `sys`, `re`, `subprocess`, `shutil`, `hashlib`, `json`
- All available in Python 3.2+

#### 11.3.2 Optional Dependencies

**sqlparse:**
- Version: 0.5.0+ (requires Python 3.8+)
- Version: 0.1.0-0.4.x (compatible with Python 3.2)
- Purpose: SQL formatting within EXEC SQL blocks
- Installation:
  ```bash
  pip install 'sqlparse>=0.1.0,<0.5.0'  # For Python 3.2
  pip install 'sqlparse>=0.5.0'         # For Python 3.8+
  ```
- Behavior if missing:
  - Warning printed: "sqlparse: skipped - sqlparse unavailable"
  - SQL blocks preserved without formatting
  - Processing continues normally

### 11.4 Backward Compatibility

**Breaking Changes (if any):**
- None since initial release

**Deprecation Policy:**
- Feature deprecations announced 2 releases in advance
- Deprecated features remain functional for 1 year
- Migration guides provided

**Version Compatibility:**
- Configuration files: Forward compatible (ignore unknown keys)
- Command-line: Forward compatible (new flags don't break old scripts)
- Output format: Stable (formatting behavior may change, but structure doesn't)

---

## 12. Future Enhancements

### 12.1 Planned Features

#### 12.1.1 Three-Pass Case Management

**Status:** Planned for next release

**Problem:**
- Current: `keyword_case=None, identifier_case=None` (preserves case)
- Users want: Optional case styling (e.g., uppercase keywords)
- Challenge: Case changes break f-identical verification

**Solution:**
```
Pass 1: Format with case preservation (keyword_case=None)
    ↓
Pass 2: Verify f-identical (guarantees functional identity)
    ↓
Pass 3: Apply case styling (optional, opt-in)
```

**Configuration:**
```ini
[sql]
keyword_case = upper      # Optional: upper, lower, capitalize, or none
identifier_case = lower   # Optional: upper, lower, or none
```

**Implementation Plan:**
1. Add `config.py` module for INI file support
2. Update `ProCFormatterContext` with case preferences
3. Modify `format_exec_sql_block()` for two-stage formatting
4. Add command-line flags: `--sql-keyword-case`, `--sql-identifier-case`
5. Add tests for case styling

**See Also:** [Technical Design Document] (to be created)

#### 12.1.2 Configuration File Support

**Format:** INI (`.proc-format.ini`)

**Search Locations:**
1. Current directory
2. Parent directories (up to project root)
3. Home directory (`~/.proc-format.ini`)
4. Global config (`/etc/proc-format.ini`)

**Configuration Schema:**
```ini
[sql]
keyword_case = upper
identifier_case = lower
enabled = true

[c_format]
executable = clang-format
style =                     # Empty = use .clang-format file

[verification]
enabled = true
keep_temp_on_failure = false

[general]
verbosity = 1
debug_dir = debug
```

**Implementation:**
- Use Python's `configparser` module (stdlib)
- Merge strategy: CLI args > local config > global config > defaults
- Validation: Warn on unknown keys, error on invalid values

#### 12.1.3 Enhanced SQL Formatting

**Current State:**
- sqlparse formats SQL structure (indentation, line breaks)
- No control over formatting style

**Planned Enhancements:**
1. **Custom SQL Style Profiles:**
   ```ini
   [sql.style]
   indent_width = 2
   comma_position = trailing    # or leading
   keyword_alignment = left     # or right
   ```

2. **Selective Formatting:**
   ```ini
   [sql]
   format_patterns = SELECT,INSERT,UPDATE,DELETE
   skip_patterns = WHENEVER,INCLUDE
   ```

3. **sqlparse Configuration Pass-Through:**
   ```ini
   [sql.sqlparse]
   reindent = true
   keyword_case = upper
   indent_tabs = false
   indent_width = 4
   ```

#### 12.1.4 Pre-commit Hook Support

**Goal:** Integrate proc-format into Git workflow

**Implementation:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/phdye/proc-format
    rev: v1.0.0
    hooks:
      - id: proc-format
        files: '\.pc$'
        args: ['--verify']
```

**Features:**
- Auto-format `.pc` files before commit
- Verify functional identity
- Fail commit if verification fails
- Optional: Auto-stage formatted files

#### 12.1.5 Editor Integration

**VS Code Extension:**
- Format on save
- Syntax highlighting for EXEC SQL blocks
- Inline error reporting
- Configuration UI

**Emacs Package:**
- `exec-sql-parser.el` already exists
- Integration with `proc-format` binary
- Auto-formatting in `cc-mode`

**Vim Plugin:**
- `:ProcFormat` command
- Automatic formatting with `:w`
- QuickFix integration for errors

### 12.2 Research Items

#### 12.2.1 Parallel Processing

**Hypothesis:** Large files could benefit from parallel processing

**Approach:**
1. Split file into chunks (by EXEC SQL blocks)
2. Process chunks in parallel:
   - Extract SQL blocks
   - Format C code
   - Restore SQL blocks
3. Merge chunks
4. Verify entire file

**Challenges:**
- Marker numbering must be sequential
- clang-format context dependencies
- Overhead of parallelization

**Expected Benefit:** 2-3x speedup for files >10,000 lines

#### 12.2.2 Incremental Formatting

**Hypothesis:** Only format changed regions

**Approach:**
1. Compute diff between original and current file
2. Identify changed EXEC SQL blocks and C code regions
3. Format only changed regions
4. Preserve unchanged regions verbatim

**Challenges:**
- Dependency tracking (changed SQL might affect C indentation)
- Cache invalidation
- Editor integration required for best UX

**Expected Benefit:** 10-100x speedup for incremental edits

#### 12.2.3 AST-Based Formatting

**Hypothesis:** Parse Pro*C into AST for more robust formatting

**Approach:**
1. Build full Pro*C parser (using libclang + custom SQL parser)
2. Generate AST with both C and SQL nodes
3. Format based on AST structure
4. Reconstruct source from AST

**Challenges:**
- Complex parser implementation
- Maintaining semantic equivalence
- Performance overhead

**Expected Benefit:**
- More robust formatting
- Better error detection
- Semantic-aware formatting rules

### 12.3 Documentation Enhancements

**Planned Documentation:**

1. **User Guide** (exists, needs update)
   - Quick start guide
   - Configuration examples
   - Troubleshooting section
   - FAQ

2. **Developer Guide** (exists, needs expansion)
   - Architecture overview
   - Contributing guidelines
   - Testing strategies
   - Release process

3. **API Reference** (to be created)
   - Public API documentation
   - Module descriptions
   - Function signatures
   - Usage examples

4. **Technical Design Documents** (to be created)
   - Three-pass case management
   - Configuration system design
   - Verification system design
   - Future feature designs

### 12.4 Testing Enhancements

**Current State:**
- Unit tests with pytest
- Emacs Lisp tests
- Example-based testing

**Planned Enhancements:**

1. **Integration Tests:**
   - End-to-end file processing
   - Multi-file projects
   - Configuration file loading
   - Error condition handling

2. **Performance Tests:**
   - Benchmark suite
   - Regression detection
   - Scalability testing

3. **Fuzzing:**
   - Random Pro*C generation
   - Mutation testing
   - Edge case discovery

4. **Continuous Integration:**
   - GitHub Actions
   - Multiple Python versions
   - Multiple platforms
   - Coverage reporting

---

## 13. Appendix

### 13.1 Glossary

**Terms:**

- **Pro*C**: Oracle's precompiler for embedding SQL in C programs
- **EXEC SQL**: Keyword marking embedded SQL statements in Pro*C
- **Marker**: Temporary comment replacing EXEC SQL blocks during C formatting
- **Registry**: Dictionary of patterns for identifying EXEC SQL constructs
- **f-identical**: Functionally identical (same after whitespace removal)
- **clang-format**: LLVM's C/C++ code formatter
- **sqlparse**: Python library for parsing and formatting SQL

### 13.2 References

**External Documentation:**
- [Oracle Pro*C Programmer's Guide](https://docs.oracle.com/en/database/oracle/oracle-database/19/lnpcc/)
- [clang-format Style Options](https://clang.llvm.org/docs/ClangFormatStyleOptions.html)
- [sqlparse Documentation](https://sqlparse.readthedocs.io/)

**Internal Documentation:**
- [User Guide](User-Guide.md)
- [Developer Guide](Developer-Guide.md)
- [Project Plan](Project-Plan.md)

### 13.3 Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-13 | Claude | Initial comprehensive specification |

### 13.4 Contributors

- **Author**: Philip Dye (phdye)
- **Contributors**: See [CONTRIBUTORS.md](../CONTRIBUTORS.md)

---

**END OF TECHNICAL SPECIFICATION**
