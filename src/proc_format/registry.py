# Registry for Modular EXEC SQL Handling
# --------------------------------------
# This module defines a registry (EXEC_SQL_REGISTRY) for handling different
# EXEC SQL constructs.  Previously each specic construct was parsed.  That was
# overkill and made the code more time consuming to maintain.  Since we actually
# do not format the EXEC SQL lines, we can simply maintain the original content
# and indent style offset only to align 'EXEC SQL' with C statements the same C block.
#
# Each entry specifies a regular expression pattern to match a general construct and
# and end_pattern for multi-line constructs.  The "action" defines how the construct's
# content is processed.  Though so far, "maintain original content" is the only action.
#
# One bizarre aspect is the duplicate entries for single-line statements.  This is due
# to a bug in Python 3.2.5.  The bug is not present in Python 3.9+.
#
# Notes:
# - The braces '{' and '}' for BEGIN/END DECLARE SECTION are inserted to facilitate
#   C formatting but are removed during the restoration phase. -- occurs in core.py
# - The patterns for single-line and multi-line constructs ensure the parsing logic
#   in core.py functions correctly for a variety of Pro*C statements.
#
# --- Registry for Modular EXEC SQL Handling ---
#
# Since we are not formating the EXEC SQL lines, simply maintain the original content and indent style offset only
# to align 'EXEC SQL' with statements the same block.
#
# Shoould we start formatting EXEC SQL lines, we would most likely strip() them:
#    "action": lambda lines: [lines[0].strip()]
#
# However, most Pro*C EXEC SQL code is already hand formatted and quite
# carefully internally aligned.  As such, even if we start formatting, it
# would optional and quite likely enabled selectively in some manner.

import os
import re
import json

re_EXEC_SQL  = re.compile(r'EXEC\s+SQL\b(\s*(.*))?')
re_DECLARE   = re.compile(r'\s*(BEGIN|END)\s+DECLARE\s+SECTION\s*[;]')
re_INDENT    = re.compile(r'^(\s*)(.*)')

re_DECLARE_BEGIN   = re.compile(r'EXEC SQL BEGIN\s+DECLARE\s+SECTION\s*[;]')
re_DECLARE_END     = re.compile(r'EXEC SQL END\s+DECLARE\s+SECTION\s*[;]')

# Regex patterns for SQL Cursor Management
re_DECLARE_CURSOR = re.compile(r'EXEC\s+SQL\s+DECLARE\s+\w+\s+CURSOR\s+FOR\b')
re_OPEN_CURSOR = re.compile(r'EXEC\s+SQL\s+OPEN\s+\w+\b')
re_FETCH_CURSOR = re.compile(r'EXEC\s+SQL\s+FETCH\s+\w+\b')
re_CLOSE_CURSOR = re.compile(r'EXEC\s+SQL\s+CLOSE\s+\w+\b')

DEFAULT_EXEC_SQL_REGISTRY = {
    # *** Duplicate entries necessary due to Python 3.2.5 bug
    # ***   unnecessary in Python 3.9+
    #
    "ORACLE-Single-Line [1]": {
        "pattern": r"EXEC ORACLE\b(.*);",
        "action": lambda lines: lines  # Maintain original content
    },
    "ORACLE-Single-Line [2]": {
        "pattern": r"EXEC ORACLE\b(.*);",
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

    # *** Duplicate entries necessary due to Python 3.2.5 bug
    # ***   unnecessary in Python 3.9+
    #
    "STATEMENT-Single-Line [1]": {
        "pattern": r"EXEC SQL\b(.*);",
        "action": lambda lines: lines  # Maintain original content
    },
    "STATEMENT-Single-Line [2]": {
        "pattern": r"EXEC SQL\b(.*);",
        "action": lambda lines: lines  # Maintain original content
    },

    "STATEMENT-Multi-Line": {
        "pattern": r"EXEC SQL\b",
        "end_pattern": r".*;",  # Block terminates with semicolon
        "action": lambda lines: lines  # Maintain original content
    },

    # 'END-EXEC' and 'END' let use catch unterminated blocks as errors
    #  -- either as a bug in the source or a bug in the extraction logic
    #
    # Hrpmph, just realized Pro*C allows 'END-EXEC' to randomly appear in the code

    # END-EXEC for COBOL Compatibility
    "END-EXEC": {
        "pattern": r"END-EXEC\b(.*);",
        "action": lambda lines: lines,  # Maintain original content
        # "error" : None,
    },

    # ** 'END' must be after 'END-EXEC' as '-' matches '\b'
    "END": {
        "pattern": r"END\b(.*);",
        "action": lambda lines: lines,  # Maintain original content
        "error" : None,
    }
}

def load_registry(start_dir, search_parents=True):
    registry = DEFAULT_EXEC_SQL_REGISTRY.copy()
    path = os.path.abspath(start_dir)
    configs = []
    while True:
        cfg_path = os.path.join(path, '.exec-sql-parser')
        if os.path.isfile(cfg_path):
            try:
                f = open(cfg_path, 'r')
                data = json.load(f)
                f.close()
            except Exception:
                data = {}
            configs.append(data)
            if data.get('root'):
                break
        parent = os.path.dirname(path)
        if parent == path or not search_parents:
            break
        path = parent
    configs.reverse()
    for data in configs:
        for name, value in data.items():
            if name == 'root':
                continue
            if value is None:
                if name in registry:
                    del registry[name]
            elif isinstance(value, dict):
                pattern = value.get('pattern')
                if pattern is None:
                    continue
                entry = { 'pattern': pattern,
                          'action': lambda lines: lines }
                if 'end_pattern' in value:
                    entry['end_pattern'] = value['end_pattern']
                if 'error' in value:
                    entry['error'] = value['error']
                registry[name] = entry
    return registry
