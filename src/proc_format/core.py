"""Core formatting routines for proc_format."""

import sys
import os
import re
import subprocess
import logging
import shutil

try:
    import sqlparse
except ImportError:  # pragma: no cover - sqlparse optional
    sqlparse = None

from .registry import load_registry
from .registry import re_DECLARE_BEGIN, re_DECLARE_END, re_EXEC_SQL, re_INDENT

logging.basicConfig(level=logging.INFO)

MARKER_PREFIX = "// EXEC SQL MARKER"
re_MARKER_PREFIX = re.compile(r"([{}])?\s*//\s\s*EXEC\s\s*SQL\s\s*MARKER\s\s*:(\d+):")

BEFORE_PC = "before.pc"             # Original Pro*C content before formatting
BEFORE_C = "before.c"               # C content before formatting
AFTER_C = "after.c"                 # C content after formatting
AFTER_PC = "after.pc"               # Pro*C content after formatting
ERRORS_TXT = "errors.txt"           # List of segments with errors, one per line: <segment-idx>
SQL_DIR = "sql"                     # Directory with extracted EXEC SQL segments
EXEC_SQL_FILE_MODEL = "exec-sql--%s.txt"  # Template for combined EXEC SQL file name before/after formatting

class ProCFormatterContext:
    """Runtime configuration for :func:`process_file`.

    Instances are lightweight containers created from command-line
    arguments.  They expose the input and output paths, the location of
    the ``clang-format`` executable and a registry of EXEC SQL
    constructs.  The class intentionally avoids ``__dict__`` creation
    to keep attribute access inexpensive.
    """

    __slots__ = [
        "input_file",
        "output_file",
        "exec_sql_before_fh",
        "exec_sql_after_fh",
        "clang_format_path",
        "keep",
        "debug",
        "sql_dir",
        "registry",
    ]

    def __init__(self, args):
        self.input_file = args.input_file
        self.output_file = args.output_file
        self.clang_format_path = args.clang_format
        self.keep = args.keep
        self.debug = args.debug
        self.sql_dir = os.path.join(self.debug, SQL_DIR)
        search = not getattr(args, 'no_registry_parents', False)
        # The registry is loaded from ``.exec-sql-parser`` files in the
        # directory tree containing ``input_file``.
        self.registry = load_registry(os.path.dirname(self.input_file), search)

def format_name(debug_dir, *elements):
    elements = [str(e) for e in elements]
    return os.path.join(debug_dir, *elements)

def open_file(debug_dir, file_name):
    return open(format_name(debug_dir, file_name), "w")

def write_file(debug_dir, file_name, content):
    with open_file(debug_dir, file_name) as f:
        f.write(content)

def process_file(ctx):
    """Format a Pro*C file while preserving EXEC SQL segments.

    The function performs the following steps:

    1.  Capture EXEC SQL constructs and replace them with numbered
        markers.
    2.  Run ``clang-format`` over the resulting C code.
    3.  Restore the captured EXEC SQL text in place of the markers.

    Temporary files are written beneath ``ctx.debug`` for inspection.
    """

    print("Formatting: {0}".format(ctx.input_file))

    if not ctx.keep:
        if os.path.exists(ctx.debug):
            shutil.rmtree(ctx.debug, ignore_errors=True)
    if not os.path.exists(ctx.debug):
        os.makedirs(ctx.debug)

    if os.path.exists(ctx.sql_dir):
        shutil.rmtree(ctx.sql_dir, ignore_errors=True)
    os.makedirs(ctx.sql_dir)

    with open(ctx.input_file, 'r') as f:
        pc_before = f.read()
    write_file(ctx.debug, BEFORE_PC, pc_before)

    file_name = EXEC_SQL_FILE_MODEL % "before"
    ctx.exec_sql_before_fh = open(os.path.join(ctx.debug, file_name), 'w') or \
                                exit("Failed to create file '%s'" % file_name)
    file_name = EXEC_SQL_FILE_MODEL % "after"
    ctx.exec_sql_after_fh = open(os.path.join(ctx.debug, file_name), 'w') or \
                                exit("Failed to create file '%s'" % file_name)

    # Step 1: Mark EXEC SQL lines
    marked_content, exec_sql_segments = capture_exec_sql_blocks(ctx, pc_before.splitlines(), ctx.registry)
    c_before = "\n".join(marked_content)
    write_file(ctx.debug, BEFORE_C, c_before)

    # Step 2: Format using clang-format
    c_after = format_with_clang(ctx, c_before)
    write_file(ctx.debug, AFTER_C, c_after)

    # Step 3: Restore EXEC SQL lines
    pc_after = restore_exec_sql_blocks(c_after, exec_sql_segments, ctx)
    write_file(ctx.debug, AFTER_PC, pc_after)

    ctx.exec_sql_before_fh.close()
    ctx.exec_sql_after_fh.close()

    # Step 4: Write output to file
    with open(ctx.output_file, 'w') as f:
        f.write(pc_after)

    print("File processed successfully: {0}\nd".format(ctx.input_file))

def format_exec_sql_block(lines, construct):
    """Format EXEC SQL ``lines`` using ``sqlparse`` unless ORACLE.

    ``construct`` identifies the registry entry.  When ``sqlparse`` is
    unavailable or the block begins with ``EXEC ORACLE`` no formatting is
    applied.  The function returns a list of lines.
    """
    if not lines:
        return lines
    first = lines[0].lstrip()
    if first.startswith('EXEC ORACLE') or construct.startswith('ORACLE'):
        return lines
    if sqlparse is None:
        return lines
    match_indent = re_INDENT.match(lines[0])
    indent = match_indent.group(1)
    content = match_indent.group(2)
    m = re_EXEC_SQL.match(content)
    if not m:
        return lines
    rest = m.group(2) or ''
    sql_lines = []
    if rest:
        sql_lines.append(rest.strip())
    for line in lines[1:]:
        sql_lines.append(line.strip())
    sql_text = "\n".join(sql_lines)
    try:
        formatted = sqlparse.format(sql_text, keyword_case='upper')
    except Exception:
        return lines
    formatted_lines = formatted.splitlines()
    output = []
    if formatted_lines:
        output.append(indent + 'EXEC SQL ' + formatted_lines[0].lstrip())
        for line in formatted_lines[1:]:
            output.append(indent + line)
    else:
        output = lines
    return output

def capture_exec_sql_blocks(ctx, lines, registry):
    """Extract EXEC SQL blocks from ``lines``.

    Each matched block is replaced by a numbered marker and the original
    text is stored in ``ctx.sql_dir``.  The function returns a tuple of
    ``(output_lines, captured_blocks)`` where ``output_lines`` is the
    marker substituted content and ``captured_blocks`` contains the
    original lines for each marker.
    """
    captured_blocks = []
    output_lines = []
    inside_block = False
    current_block = []
    current_handler = None
    current_construct = None
    current_stripped_line = None
    marker_counter = 1  # Sequential counter for unique markers

    print("- Capture EXEC SQL segments ...")
    # Ensure specific patterns are matched before generic ones.  Python 3.2
    # dictionaries do not preserve insertion order, so ``registry`` entries
    # are sorted by the length of their pattern with longer (more specific)
    # patterns evaluated first.
    registry_items = sorted(
        registry.items(),
        key=lambda item: len(item[1].get("pattern", "")),
        reverse=True,
    )

    for line_number, line in enumerate(lines, 1):
        stripped_line = line.strip()
        if inside_block:
            current_block.append(line)  # Continue accumulating block
            # Detect the end of the current block using the handler's
            # ``end_pattern``.
            if re.match(current_handler["end_pattern"], stripped_line):
                # Block has ended; replace it with a marker
                marker = get_marker(marker_counter)
                output_lines.append(marker)
                captured = current_handler["action"](current_block)
                captured_blocks.append(format_exec_sql_block(captured, current_construct))
                with open_file(ctx.sql_dir, "%03d" % marker_counter) as f:
                    f.write(("Construct:  '{}'\n".format(current_construct))
                           +("Pattern:    '{}'\n".format(current_handler["pattern"]))
                           +("EndPattern: '{}'\n\n".format(current_handler["end_pattern"]))
                           +("Stripped:  '{}'\n\n".format(current_stripped_line))
                           +("\n".join(current_block)+"\n\n"))
                if hasattr(ctx, 'exec_sql_before_fh'):
                    ctx.exec_sql_before_fh.write("\n".join(current_block) + "\n= = = = =\n")
                marker_counter += 1
                inside_block = False
                current_block = []  # Reset the block
                current_handler = None
                current_construct = None
                current_stripped_line = None
                print("b", end="")
        else:
            for construct, details in registry_items:
                if re.match(details["pattern"], stripped_line):
                    if "error" in details:
                        raise ValueError("Unaccompanied block end marker detected at line {0}:\n{1}"
                            .format(line_number, line))
                    if "end_pattern" in details:
                        # Multi-line block detected
                        inside_block = True
                        current_block = [line]
                        current_handler = details
                        current_construct = construct
                        current_stripped_line = stripped_line
                    else:
                        # Single-line match
                        captured = details["action"]([line])
                        captured_blocks.append(format_exec_sql_block(captured, construct))
                        with open_file(ctx.sql_dir, "%03d" % marker_counter) as f:
                            f.write(("Construct:  '{}'\n".format(construct))
                                   +("Pattern:    '{}'\n\n".format(details["pattern"]))
                                   +("Stripped:   '{}'\n\n".format(stripped_line))
                                   +(line)+"\n\n")
                        if hasattr(ctx, 'exec_sql_before_fh'):
                            ctx.exec_sql_before_fh.write(line + "\n= = = = =\n")
                        marker = get_marker(marker_counter)
                        if re.match(re_DECLARE_BEGIN, stripped_line):
                            marker = '{ ' + marker
                        if re.match(re_DECLARE_END, stripped_line):
                            marker = '} ' + marker
                        output_lines.append(marker)
                        marker_counter += 1
                        print("s", end="")
                    break
            else:
                output_lines.append(line)
    print()

    if inside_block:
        marker = get_marker(marker_counter)
        output_lines.append(marker)
        captured = current_handler["action"](current_block)
        captured_blocks.append(format_exec_sql_block(captured, current_construct))
        with open_file(ctx.sql_dir, "%03d" % marker_counter) as f:
            f.write(("Construct:  '{0}'\n".format(current_construct))
                   +("Pattern:    '{0}'\n".format(current_handler["pattern"]))
                   +("EndPattern: '{0}'\n\n".format(current_handler["end_pattern"]))
                   +("Stripped:  '{0}'\n\n".format(current_stripped_line))
                   +("\n".join(current_block)+"\n\n"))
        if hasattr(ctx, 'exec_sql_before_fh'):
            ctx.exec_sql_before_fh.write("\n".join(current_block) + "\n= = = = =\n")
        marker_counter += 1
        print("b", end="")

    return output_lines, captured_blocks

def format_with_clang(ctx, content):
    """Return ``content`` formatted with ``clang-format``.

    ``ctx.clang_format_path`` is executed as a subprocess.  Any
    ``clang-format`` failure results in ``RuntimeError``.  On Python
    versions earlier than 3.7 the function encodes the input to bytes
    to satisfy ``subprocess``'s expectations.
    """
    print("- Apply clang-format to C code content ...")
    popen_additional_args = {}
    if sys.version_info >= (3, 7, 0):  # Python 3.7 added ``text``
        popen_additional_args["text"] = True
    else:
        # Python 3.2 subprocess expects byte strings
        if hasattr(content, "encode"):
            content = content.encode()
    process = subprocess.Popen([ctx.clang_format_path],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            **popen_additional_args)
    output, error = process.communicate(input=content)
    if process.returncode != 0:
        raise RuntimeError("Clang-format failed: {0}".format(error))
    if sys.version_info < (3, 7, 0):
        output = output.decode()
    return output

def restore_exec_sql_blocks(content, exec_sql_segments, ctx=None):
    """Replace markers in ``content`` with EXEC SQL blocks.

    ``exec_sql_segments`` must contain the original text for each marker
    in order.  Restored lines are indented to match the marker they
    replace.  Errors are raised for out-of-sequence markers or when not
    all segments are consumed.  ``ctx`` is optional and used only for
    debugging output.
    """
    lines = content.split('\n')
    restored_lines = []
    expected_marker = 1  # Start with the first marker

    print("- Restore EXEC SQL segments ...")

    for line in lines:
        match = re_MARKER_PREFIX.match(line.strip())
        if match:
            try:
                marker_number = int(match.group(2))
                if marker_number != expected_marker:
                    raise ValueError("Marker out of sequence: expected {0}, found {1}"
                                        .format(expected_marker, marker_number))
                lines = exec_sql_segments[marker_number - 1]
                if ctx is not None and hasattr(ctx, 'exec_sql_after_fh'):
                    ctx.exec_sql_after_fh.write("\n".join(lines) + "\n= = = = =\n")
                indent = len(line) - len(line.lstrip())
                first = lines.pop(0)
                restored_lines.append(" " * indent + first.lstrip())
                if len(lines) > 0:
                    prior_indent = len(first) - len(first.lstrip())
                    delta = indent - prior_indent
                    (more, less) = (0, delta) if delta < 0 else (delta, 0)
                    for line in lines:
                        restored_lines.append(" " * more + line[-less:])
                expected_marker += 1
                print(".", end="")
            except (IndexError, ValueError) as e:
                raise ValueError("Invalid or missing marker: {0}, Error: {1}"
                                    .format(line, e))
        else:
            restored_lines.append(line)

    print()

    remaining = len(exec_sql_segments) - expected_marker + 1
    if remaining > 0:
        raise ValueError("Not all EXEC SQL markers were restored: {0} markers missing"
                            .format(remaining))

    return "\n".join(restored_lines)

def get_marker(n):
    """Return the formatted marker string for index ``n``."""
    return "{0} :{1}:".format(MARKER_PREFIX, n)
