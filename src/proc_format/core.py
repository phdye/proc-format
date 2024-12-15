
# Restructured Proc Formatter
# Original functionality preserved, with modularized and testable structure

import logging

logging.basicConfig(level=logging.INFO)

# --- Core Logic ---

#!/usr/bin/env python3

import subprocess
import os
import re

re_EXEC_SQL  = re.compile(r'EXEC\s\s*SQL\b(\s*(.*))?')
re_DECLARE   = re.compile(r'\s*(BEGIN|END)\s\s*DECLARE\s\s*SECTION\s*[;]')
re_INDENT    = re.compile(r'^(\s*)(.*)')

# Regex patterns for SQL Cursor Management
re_DECLARE_CURSOR = re.compile(r'EXEC\s+SQL\s+DECLARE\s+\w+\s+CURSOR\s+FOR\b')
re_OPEN_CURSOR = re.compile(r'EXEC\s+SQL\s+OPEN\s+\w+\b')
re_FETCH_CURSOR = re.compile(r'EXEC\s+SQL\s+FETCH\s+\w+\b')
re_CLOSE_CURSOR = re.compile(r'EXEC\s+SQL\s+CLOSE\s+\w+\b')

MARKER_PREFIX = "// EXEC SQL MARKER"
re_MARKER_PREFIX = re.compile(r"([{}])?\s*//\s\s*EXEC\s\s*SQL\s\s*MARKER\s\s*:(\d+):")

def get_marker(n : int, prefix=""):
    return f"{prefix}{MARKER_PREFIX} :{n}:"

def is_complete_sql_statement(line, inside_quotes=False, current_quote=None, q_quote_delimiter=None):
    """
    Check if a line ends an EXEC SQL block, considering Oracle Pro*C quoting rules.
    Supports single quotes, double quotes, and q-Quotes.
    """
    escaped = False
    i = 0
    while i < len(line):
        char = line[i]

        # Handle escaping (only applicable outside of q-Quotes in Oracle Pro*C)
        if escaped:
            escaped = False
            i += 1
            continue

        if char == '\\':
            escaped = True
            i += 1
            continue

        # Handle q-Quotes
        if q_quote_delimiter:
            if line[i:i + len(q_quote_delimiter)] == q_quote_delimiter:
                return False, False  # q-Quote closes; we exit the context
            i += 1
            continue

        # Detect the start of a q-Quote
        if char == 'q' and i + 2 < len(line) and line[i + 1] in ("'", '"', '[', '(', '{', '<'):
            # Find the closing delimiter
            open_delim = line[i + 1]
            close_delim = {'[': ']', '(': ')', '{': '}', '<': '>'}.get(open_delim, open_delim)
            q_quote_delimiter = close_delim
            i += 2
            continue

        # Toggle single/double quote context
        if char in ("'", '"'):
            if current_quote is None:
                current_quote = char  # Entering a quote
                inside_quotes = True
            elif current_quote == char:
                current_quote = None  # Exiting a quote
                inside_quotes = False

        # Semicolon ends the statement only outside quotes
        if char == ';' and not inside_quotes and not q_quote_delimiter:
            return True, False

        i += 1

    # Line ends; return whether we are inside any quote
    return False, inside_quotes or bool(q_quote_delimiter)

def mark_exec_sql(content):
    """Replace EXEC SQL blocks with markers and store them."""
    lines = content.split('\n')
    exec_sql_segments = []
    marked_lines = []
    inside_exec_sql = False
    current_sql_block = []
    inside_quotes = False
    counter = 1

    for line in lines:
        stripped_line = line.strip()
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
        elif any(re.match(stripped_line) for re in [re_DECLARE_CURSOR, re_OPEN_CURSOR, re_FETCH_CURSOR, re_CLOSE_CURSOR]):
            # Handle SQL Cursor Statements
            exec_sql_segments.append((counter, line))
            marked_lines.append(get_marker(counter))
            counter += 1
        elif match := re_EXEC_SQL.match(stripped_line):
            inside_exec_sql = not stripped_line.endswith(';')
            if inside_exec_sql:
                current_sql_block.append(line)
            else:
                exec_sql_segments.append((counter, line))
                prefix = ""
                if declare := re_DECLARE.match(match.group(2)):
                    prefix = "{ " if declare.group(1) == "BEGIN" else "} "
                marked_lines.append(get_marker(counter, prefix))
                counter += 1
        else:
            marked_lines.append(line)

    if inside_exec_sql:
        raise ValueError("Unterminated EXEC SQL block detected.")

    return '\n'.join(marked_lines), exec_sql_segments

def ic (line):
    match = re_INDENT.match(line)
    indent = match.group(1)
    content = match.group(2)
    return (indent, content)

def restore_exec_sql(content, exec_sql_segments):
    """Restore EXEC SQL blocks with proper alignment."""
    lines = content.split('\n')
    restored_lines = []

    for line in lines:
        stripped_line = line.strip()
        if match := re_MARKER_PREFIX.match(stripped_line):
            try:
                # marker_number = int(line.split(':')[1])
                marker_number = int(match.group(2))
                block = exec_sql_segments[marker_number - 1][1]
                # Restore with indentation
                base_indent = len(line) - len(line.lstrip())
                if '\n' not in block:
                    (indent, content) = ic(block)
                    restored_lines.append(" " * base_indent + content)
                else:
                    lines = block.split('\n')
                    first = lines.pop(0)
                    (leader, content) = ic(first)
                    prior_indent = len(leader)
                    delta = base_indent - prior_indent
                    restored_lines.append(" " * base_indent + content)
                    for line in lines:
                        (indent, content) = ic(line)
                        if delta < 0:
                            restored_lines.append(line[-delta:])
                        else:
                            restored_lines.append(" "*delta +line)
            except (IndexError, ValueError):
                raise ValueError(f"Invalid or missing marker: {line}")
        else:
            restored_lines.append(line)

    return '\n'.join(restored_lines)

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

