import os
import re
import subprocess
import logging

from .registry import EXEC_SQL_REGISTRY

logging.basicConfig(level=logging.INFO)

MARKER_PREFIX = "// EXEC SQL MARKER"
re_MARKER_PREFIX = re.compile(r"([{}])?\s*//\s\s*EXEC\s\s*SQL\s\s*MARKER\s\s*:(\d+):")

def get_marker(n):
    return "{0} :{1}:".format(MARKER_PREFIX, n)

def process_declare_section(lines):
    # Add curly braces for formatting and maintain original content
    processed_lines = ["{ // EXEC SQL DECLARE SECTION"]
    processed_lines.extend([line.strip() for line in lines[1:-1]])  # Inner content
    processed_lines.append("} // EXEC SQL DECLARE SECTION")
    return processed_lines

def capture_exec_sql_blocks(lines):
    """
    Parses the input lines, replacing EXEC SQL blocks with markers
    and capturing their content for later restoration.
    """
    captured_blocks = []
    output_lines = []
    inside_block = False
    current_block = []
    current_handler = None
    marker_counter = 1  # Sequential counter for unique markers

    for line_number, line in enumerate(lines, 1):
        if inside_block:
            stripped_line = line.strip()
            current_block.append(line)  # Add the line to the current block
            if ';' in stripped_line:
                # Block has ended; replace it with a marker
                marker = get_marker(marker_counter)
                output_lines.append(marker)
                captured_blocks.append(current_handler["action"](current_block))
                marker_counter += 1
                inside_block = False
                current_block = []  # Reset the block
                current_handler = None
        else:
            for construct, details in EXEC_SQL_REGISTRY.items():
                if re.match(details["pattern"], line.strip()):
                    if "end_pattern" in details:
                        # Multi-line block detected
                        inside_block = True
                        current_block = [line]
                        current_handler = details
                    else:
                        # Single-line match
                        captured_blocks.append(details["action"]([line]))
                        marker = get_marker(marker_counter)
                        if 'BEGIN' in construct:
                            marker = '{{ {0}'.format(marker)
                        if 'END' in construct:
                            marker = '}} {0}'.format(marker)
                        output_lines.append(marker)
                        marker_counter += 1
                    break
            else:
                output_lines.append(line)

    if inside_block:
        raise ValueError(
            "Unterminated EXEC SQL block detected at line {0}: {1}".format(line_number, current_block[0])
        )

    return output_lines, captured_blocks

def restore_exec_sql_blocks(content, exec_sql_segments):
    lines = content.split('\n')
    restored_lines = []
    expected_marker = 1  # Start with the first marker

    for line in lines:
        match = re_MARKER_PREFIX.match(line.strip())
        if match:
            try:
                marker_number = int(match.group(2))
                if marker_number != expected_marker:
                    raise ValueError("Marker out of sequence: expected {0}, found {1}".format(expected_marker, marker_number))
                restored_lines.extend(exec_sql_segments[marker_number - 1])
                expected_marker += 1
            except (IndexError, ValueError) as e:
                raise ValueError("Invalid or missing marker: {0}, Error: {1}".format(line, e))
        else:
            restored_lines.append(line)

    if expected_marker - 1 != len(exec_sql_segments):
        raise ValueError("Not all markers were restored. Possible residual markers in the output.")

    return "\n".join(restored_lines)

def format_with_clang(content, clang_format_path="clang-format"):
    """Format content using clang-format."""
    with open("debug/f-before.c", "w") as f:
        f.write(content)
    process = subprocess.Popen([clang_format_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, error = process.communicate(input=content)
    if process.returncode != 0:
        raise RuntimeError("Clang-format failed: {0}".format(error))
    with open("debug/f-after.c", "w") as f:
        f.write(output)
    return output

def process_file(input_file, output_file, clang_format_path="clang-format"):
    """Main function to process the file."""
    with open(input_file, 'r') as f:
        original_content = f.read()

    # Step 1: Mark EXEC SQL lines
    marked_content, exec_sql_segments = capture_exec_sql_blocks(original_content.splitlines())

    # Step 2: Format using clang-format
    formatted_content = format_with_clang("\n".join(marked_content), clang_format_path)

    # Step 3: Restore EXEC SQL lines
    final_content = restore_exec_sql_blocks(formatted_content, exec_sql_segments)

    # Step 4: Write output to file
    with open(output_file, 'w') as f:
        f.write(final_content)

    print("File processed successfully: {0}".format(output_file))
