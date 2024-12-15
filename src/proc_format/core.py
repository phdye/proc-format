import os
import re
import subprocess
import logging

logging.basicConfig(level=logging.INFO)

MARKER_PREFIX = "// EXEC SQL MARKER"
re_MARKER_PREFIX = re.compile(r"([{}])?\s*//\s\s*EXEC\s\s*SQL\s\s*MARKER\s\s*:(\d+):")

# --- Registry for Modular EXEC SQL Handling ---
EXEC_SQL_REGISTRY = {
    # BEGIN and END DECLARE SECTION
    "DECLARE SECTION - BEGIN": {
        "pattern": r"EXEC SQL BEGIN DECLARE SECTION;",
        "action": lambda lines: [lines[0].strip()]  # Replace only BEGIN line
    },
    "DECLARE SECTION - END": {
        "pattern": r"EXEC SQL END DECLARE SECTION;",
        "action": lambda lines: [lines[0].strip()]  # Replace only END line
    },

    # Cursor Declaration
    "CURSOR DECLARATION": {
        "pattern": r"EXEC SQL DECLARE \w+ CURSOR FOR",
        "end_pattern": r";",  # Multi-line ending with semicolon
        "action": lambda lines: lines  # Maintain original content
    },

    # Close Cursor
    "CLOSE CURSOR": {
        "pattern": r"EXEC SQL CLOSE \w+;",
        "action": lambda lines: [lines[0].strip()]  # Single-line statement
    },

    # Commit Work
    "COMMIT WORK RELEASE": {
        "pattern": r"EXEC SQL COMMIT WORK RELEASE;",
        "action": lambda lines: [lines[0].strip()]  # Single-line statement
    },

    # Connect Statement
    "CONNECT": {
        "pattern": r"EXEC SQL CONNECT \S+;",
        "action": lambda lines: [lines[0].strip()]  # Single-line statement
    },
    "CONNECT WITH DB": {
        "pattern": r"EXEC SQL CONNECT \S+ AT \S+;",
        "action": lambda lines: [lines[0].strip()]  # Single-line statement
    },

    # Fetch Cursor
    "FETCH CURSOR": {
        "pattern": r"EXEC SQL FETCH \w+;",
        "action": lambda lines: [lines[0].strip()]  # Single-line statement
    },

    # Include SQLCA
    "INCLUDE SQLCA": {
        "pattern": r"EXEC SQL INCLUDE SQLCA;",
        "action": lambda lines: [lines[0].strip()]  # Single-line statement
    },

    # Open Cursor
    "OPEN CURSOR": {
        "pattern": r"EXEC SQL OPEN \w+;",
        "action": lambda lines: [lines[0].strip()]  # Single-line statement
    },

    # WHENEVER Statements
    "WHENEVER SQLERROR": {
        "pattern": r"EXEC SQL WHENEVER SQLERROR .*;",
        "action": lambda lines: [lines[0].strip()]  # Single-line statement
    },
    "WHENEVER NOT FOUND": {
        "pattern": r"EXEC SQL WHENEVER NOT FOUND .*;",
        "action": lambda lines: [lines[0].strip()]  # Single-line statement
    },

    # Multi-line Statements
    "STATEMENT": {
        "pattern": r"EXEC SQL\b",
        "end_pattern": r";",  # Block terminates with semicolon
        "action": lambda lines: lines  # Maintain original content
    },

    # END-EXEC for COBOL Compatibility
    "END-EXEC;": {
        "pattern": r"END-EXEC;",
        "action": lambda lines: [lines[0].strip()]  # Single-line statement
    }
}

def get_marker(n):
    return f"{MARKER_PREFIX} :{n}:"

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
            # if re.match(current_handler["end_pattern"], stripped_line):  # Check for termination
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
            # Check if this line starts a new block
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
                            marker = '{ ' + marker
                        if 'END' in construct:
                            marker = '} ' + marker
                        output_lines.append(marker)
                        marker_counter += 1
                    break
            else:
                # Not part of a recognized block; pass through
                output_lines.append(line)

    if inside_block:
        raise ValueError(
            f"Unterminated EXEC SQL block detected at line {line_number}: {current_block[0]}"
        )

    return output_lines, captured_blocks

def capture_single_line_exec_sql(line):
    for construct, details in EXEC_SQL_REGISTRY.items():
        if re.match(details["pattern"], line.strip()):
            return details["action"]([line])
    return None  # Return None if no match is found

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
                    raise ValueError(f"Marker out of sequence: expected {expected_marker}, found {marker_number}")
                # Restore the block corresponding to the marker
                restored_lines.extend(exec_sql_segments[marker_number - 1])
                expected_marker += 1
            except (IndexError, ValueError) as e:
                raise ValueError(f"Invalid or missing marker: {line}, Error: {e}")
        else:
            restored_lines.append(line)

    if expected_marker - 1 != len(exec_sql_segments):
        raise ValueError("Not all markers were restored. Possible residual markers in the output.")

    return "\n".join(restored_lines)

def format_with_clang(content, clang_format_path="clang-format"):
    """Format content using clang-format."""
    with open("debug/f-before.c", "w") as f: f.write(content)
    process = subprocess.run([clang_format_path], input=content, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode != 0:
        raise RuntimeError(f"Clang-format failed: {process.stderr}")
    output = process.stdout
    with open("debug/f-after.c", "w") as f: f.write(output)
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

    print(f"File processed successfully: {output_file}")
