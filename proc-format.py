#!/usr/bin/env python3

import argparse
import subprocess
import os
import re

MARKER_PREFIX = "// EXEC SQL MARKER"

def get_marker(n : int):
    return f"{MARKER_PREFIX} :{n}:"


def is_complete_sql_statement(line, inside_quotes=False):
    """Check if a line ends an EXEC SQL block, considering string literals."""
    escaped = False
    for char in line:
        if char in ("'", '"') and not escaped:
            inside_quotes = not inside_quotes
        escaped = char == '\\' and not escaped
        if char == ';' and not inside_quotes:
            return True, inside_quotes
    return False, inside_quotes


def mark_exec_sql(content):
    """Replace EXEC SQL multi-line blocks with markers and store them."""
    lines = content.split('\n')
    exec_sql_segments = []
    marked_lines = []
    inside_exec_sql = False
    current_sql_block = []
    inside_quotes = False
    counter = 1

    for line in lines: 
        if inside_exec_sql:
            current_sql_block.append(line)
            is_complete, inside_quotes = is_complete_sql_statement(line, inside_quotes)
            if is_complete:
                # Save the full EXEC SQL block
                exec_sql_segments.append((counter, '\n'.join(current_sql_block)))
                marked_lines.append(get_marker(counter))
                current_sql_block = []
                inside_exec_sql = False
                counter += 1
        elif line.strip().startswith("EXEC SQL"):
            inside_exec_sql = not line.endswith(';')
            if inside_exec_sql:
                current_sql_block.append(line)
            else:
                exec_sql_segments.append((counter, line))
                marked_lines.append(get_marker(counter))
                counter += 1
        else:
            marked_lines.append(line)

    if inside_exec_sql:
        raise ValueError("Unterminated EXEC SQL block detected.")

    return '\n'.join(marked_lines), exec_sql_segments


def restore_exec_sql(content, exec_sql_segments):
    """Restore EXEC SQL lines in place of their markers."""
    lines = content.split('\n')
    restored_lines = []

    for line in lines:
        if line.strip().startswith(MARKER_PREFIX):
            try:
                marker_number = int(line.split(':')[1])
                restored_lines.append(exec_sql_segments[marker_number - 1][1])
            except (IndexError, ValueError):
                raise ValueError(f"Invalid or missing marker: {line}")
        else:
            restored_lines.append(line)

    return '\n'.join(restored_lines)


def format_with_clang(content, clang_format_path="clang-format"):
    """Format content using clang-format."""
    with open("f-before.c", "w") as f: f.write(content)
    process = subprocess.run([clang_format_path], input=content, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode != 0:
        raise RuntimeError(f"Clang-format failed: {process.stderr}")
    output = process.stdout
    with open("f-after.c", "w") as f: f.write(output)
    return output


def process_file(input_file, output_file, clang_format_path="clang-format"):
    """Main function to process the file."""
    with open(input_file, 'r') as f:
        original_content = f.read()

    try:
        # Step 1: Mark EXEC SQL lines
        marked_content, exec_sql_segments = mark_exec_sql(original_content)

        # Step 2: Format using clang-format
        formatted_content = format_with_clang(marked_content, clang_format_path)

        # Step 3: Restore EXEC SQL lines
        final_content = restore_exec_sql(formatted_content, exec_sql_segments)

        # Step 4: Write output to file
        with open(output_file, 'w') as f:
            f.write(final_content)

        print(f"File processed successfully: {output_file}")

    except Exception as e:
        print(f"Error processing file: {e}")


def main():
    parser = argparse.ArgumentParser(description="Format Pro*C files by aligning EXEC SQL and formatting C code.")
    parser.add_argument("input_file", help="Input file to process.")
    parser.add_argument("output_file", help="Output file to save the formatted content.")
    parser.add_argument("--clang-format", default="clang-format", help="Path to clang-format executable.")
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: Input file does not exist: {args.input_file}")
        return

    process_file(args.input_file, args.output_file, clang_format_path=args.clang_format)


if __name__ == "__main__":
    main()
