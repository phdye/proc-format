
# Registry for Modular EXEC SQL Handling
# --------------------------------------
# This module defines a registry (EXEC_SQL_REGISTRY) for handling different EXEC SQL constructs.
# Each entry specifies a regular expression pattern to match a construct and an optional "end_pattern"
# for multi-line constructs. The "action" defines how the construct's content is processed.
#
# Notes:
# - The braces '{' and '}' for BEGIN/END DECLARE SECTION are inserted to facilitate C formatting
#   but are removed during the restoration phase.
# - The patterns for single-line and multi-line constructs ensure the parsing logic in core.py
#   functions correctly for a variety of Pro*C statements.

# --- Registry for Modular EXEC SQL Handling ---

# Since we are not formating the EXEC SQL lines, simply
# maintain the original content and indent style offset only
# to align 'EXEC SQL' with statements the same block.
#
# When we start formatting EXEC SQL lines, we will strip() them:
#    "action": lambda lines: [lines[0].strip()]
#

import re

re_EXEC_SQL  = re.compile(r'EXEC\s+SQL\b(\s*(.*))?')
re_DECLARE   = re.compile(r'\s*(BEGIN|END)\s+DECLARE\s+SECTION\s*[;]')
re_INDENT    = re.compile(r'^(\s*)(.*)')

# Regex patterns for SQL Cursor Management
re_DECLARE_CURSOR = re.compile(r'EXEC\s+SQL\s+DECLARE\s+\w+\s+CURSOR\s+FOR\b')
re_OPEN_CURSOR = re.compile(r'EXEC\s+SQL\s+OPEN\s+\w+\b')
re_FETCH_CURSOR = re.compile(r'EXEC\s+SQL\s+FETCH\s+\w+\b')
re_CLOSE_CURSOR = re.compile(r'EXEC\s+SQL\s+CLOSE\s+\w+\b')

EXEC_SQL_REGISTRY = {
    "ORACLE-Single-Line": {
        "pattern": r"EXEC ORACLE\b([^;]*);",
        "action": lambda lines: lines  # Maintain original content
    },

    "ORACLE-Multi-Line": {
        "pattern": r"EXEC ORACLE\b",
        "end_pattern": r".*;",  # Block terminates with semicolon
        "action": lambda lines: lines  # Maintain original content
    },

    "EXECUTE-BEGIN-END-Multi-Line": {
        "pattern": r"EXEC SQL EXECUTE\b",
        "end_pattern": r"END-EXEC;",  # Block termination
        "action": lambda lines: lines  # Maintain original content
    },

    "STATEMENT-Single-Line": {
        "pattern": r"EXEC SQL\b([^;]*);",
        "action": lambda lines: lines  # Maintain original content
    },

    "STATEMENT-Multi-Line": {
        "pattern": r"EXEC SQL\b",
        "end_pattern": r".*;",  # Block terminates with semicolon
        "action": lambda lines: lines  # Maintain original content
    },

    # These two entries let one see during examine-sql that we missed a block
    # END-EXEC for COBOL Compatibility
    "END-EXEC": {
        "pattern": r"END-EXEC\b(.*);",
        "action": lambda lines: lines,  # Maintain original content
        "error" : None,
    },

    # ** 'END' must be after 'END-EXEC' as '-' matches '\b'
    "END": {
        "pattern": r"END\b(.*);",
        "action": lambda lines: lines,  # Maintain original content
        "error" : None,
    }
}
