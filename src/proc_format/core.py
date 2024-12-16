import sys
import os
import re
import subprocess
import logging
import shutil

from .registry import EXEC_SQL_REGISTRY
from .registry import re_DECLARE_BEGIN, re_DECLARE_END

logging.basicConfig(level=logging.INFO)

MARKER_PREFIX = "// EXEC SQL MARKER"
re_MARKER_PREFIX = re.compile(r"([{}])?\s*//\s\s*EXEC\s\s*SQL\s\s*MARKER\s\s*:(\d+):")

BEFORE_PC = "before.pc"             # Original Pro*C content before formatting
BEFORE_C = "before.c"               # C content before formatting
AFTER_C = "after.c"                 # C content after formatting
AFTER_PC = "after.pc"               # Pro*C content after formatting
ERRORS_TXT = "errors.txt"           # List of segments with errors, one per line: <segment-idx>
SQL_DIR = "sql"                     # Directory with extracted EXEC SQL segments

class ProCFormatterContext:
    __slots__ = ["input_file", "output_file", "clang_format_path", "debug", "sql_dir"]
    def __init__(self, input_file, output_file, clang_format_path="clang-format", debug="debug"):
        self.input_file = input_file
        self.output_file = output_file
        self.clang_format_path = clang_format_path
        self.debug = debug
        self.sql_dir = os.path.join(debug, SQL_DIR)

def format_name(debug_dir, file_name):
    return os.path.join(debug_dir, file_name)

def open_file(debug_dir, file_name):
    return open(format_name(debug_dir, file_name), "w")

def write_file(debug_dir, file_name, content):
    with open_file(debug_dir, file_name) as f:
        f.write(content)

def process_file(ctx : ProCFormatterContext):
    """Main function to process the file."""

    print("Formatting: {0}".format(ctx.input_file))

    shutil.rmtree(ctx.sql_dir, ignore_errors=True)
    shutil.rmtree(ctx.debug, ignore_errors=True)
    os.makedirs(ctx.debug)
    os.makedirs(ctx.sql_dir)

    with open(ctx.input_file, 'r') as f:
        pc_before = f.read()
    write_file(ctx.debug, BEFORE_PC, pc_before)

    # Step 1: Mark EXEC SQL lines
    marked_content, exec_sql_segments = capture_exec_sql_blocks(ctx, pc_before.splitlines())
    c_before = "\n".join(marked_content)
    write_file(ctx.debug, BEFORE_C, c_before)

    # Step 2: Format using clang-format
    c_after = format_with_clang(ctx, c_before)
    write_file(ctx.debug, AFTER_C, c_after)

    # Step 3: Restore EXEC SQL lines
    pc_after = restore_exec_sql_blocks(c_after, exec_sql_segments)
    write_file(ctx.debug, AFTER_PC, pc_after)

    # Step 4: Write output to file
    with open(ctx.output_file, 'w') as f:
        f.write(pc_after)

    print("File processed successfully: {0}".format(ctx.output_file))

def capture_exec_sql_blocks(ctx, lines):
    """
    Parses the input lines, replacing EXEC SQL blocks with markers
    and capturing their content for later restoration.
    """
    captured_blocks = []
    output_lines = []
    inside_block = False
    current_block = []
    current_handler = None
    current_construct = None
    current_construct = None
    current_stripped_line = None
    marker_counter = 1  # Sequential counter for unique markers

    print("- Capture EXEC SQL segments ...")

    for line_number, line in enumerate(lines, 1):
        stripped_line = line.strip()
        if inside_block:
            current_block.append(line)  # Add the line to the current block
            # TODO: should check END pattern but is often fails
            if re.match(current_handler["end_pattern"], stripped_line):
                # Block has ended; replace it with a marker
                marker = get_marker(marker_counter)
                output_lines.append(marker)
                captured_blocks.append(current_handler["action"](current_block))
                with open_file(ctx.sql_dir, marker_counter) as f:
                    f.write(("Construct:  '{}'\n".format(current_construct))
                           +("Pattern:    '{}'\n".format(current_handler["pattern"]))
                           +("EndPattern: '{}'\n\n".format(current_handler["end_pattern"]))
                           +("Stripped:  '{}'\n\n".format(current_stripped_line))
                           +("\n".join(current_block)+"\n\n"))
                marker_counter += 1
                inside_block = False
                current_block = []  # Reset the block
                current_handler = None
                current_construct = None
                current_stripped_line = None
                print("b", end="")
        else:
            for construct, details in EXEC_SQL_REGISTRY.items():
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
                        captured_blocks.append(details["action"]([line]))
                        with open_file(ctx.sql_dir, marker_counter) as f:
                            f.write(("Construct:  '{}'\n".format(construct))
                                   +("Pattern:    '{}'\n\n".format(details["pattern"]))
                                   +("Stripped:   '{}'\n\n".format(stripped_line))
                                   +(line)+"\n\n")
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
        raise ValueError(
            "Unterminated EXEC SQL {0} detected at line {1}:\n{2}"
                .format(current_construct, line_number, "\n".join(current_block))
        )

    return output_lines, captured_blocks

def format_with_clang(ctx, content):
    """Format content using clang-format."""
    print("- Apply clang-format to C code content ...")
    popen_additional_args = {}
    if sys.version_info >= (3, 7, 0): # Python ? 3.2.5
        popen_additional_args["text"] = True
    else:
        if True : # if hasattr(content, "encode"):
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

def restore_exec_sql_blocks(content, exec_sql_segments):
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
                # get the block, split it on newline
                lines = exec_sql_segments[marker_number - 1]
                # Align EXEC SQL with C statements
                indent = len(line) - len(line.lstrip())
                first = lines.pop(0)
                restored_lines.append(" " * indent + first.lstrip())
                if len(lines) > 0:
                    prior_indent = len(first) - len(first.lstrip())
                    delta = indent - prior_indent
                    (more, less) = (0, delta) if delta < 0 else (delta, 0)
                    for line in lines:
                        # this_indent = len(line) - len(line.lstrip()) + delta
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
    return "{0} :{1}:".format(MARKER_PREFIX, n)
