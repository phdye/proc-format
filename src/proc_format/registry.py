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
    # BEGIN and END DECLARE SECTION
    "DECLARE SECTION - BEGIN": {
        "pattern": r"EXEC\s+SQL\s+BEGIN\s+DECLARE\s+SECTION\s*;",
        "action": lambda lines: lines  # Maintain original content
    },
    "DECLARE SECTION - END": {
        "pattern": r"EXEC\s+SQL\s+END\s+DECLARE\s+SECTION\s*;",
        "action": lambda lines: lines  # Maintain original content
    },

    # Cursor Declaration
    "CURSOR DECLARATION": {
        "pattern": r"EXEC\s+SQL\s+DECLARE\s+\w+\s+CURSOR\s+FOR\b",
        "end_pattern": r";",  # Multi-line ending with semicolon
        "action": lambda lines: lines  # Maintain original content
    },
    # Fetch Cursor
    "FETCH CURSOR": {
        "pattern": r"EXEC\s+SQL\s+FETCH\s+\w+\s*;",
        "action": lambda lines: lines  # Maintain original content
    },
    # Close Cursor
    "CLOSE CURSOR": {
        "pattern": r"EXEC\s+SQL\s+CLOSE\s+\w+\s*;",
        "action": lambda lines: lines  # Maintain original content
    },

    # Commit Work
    "COMMIT WORK RELEASE": {
        "pattern": r"EXEC\s+SQL\s+COMMIT\s+WORK\s+RELEASE\s*;",
        "action": lambda lines: lines  # Maintain original c*ntent
    },

    # Connect Statement
    "CONNECT": {
        "pattern": r"EXEC\s+SQL\s+CONNECT\s+\S+\s*;",
        "action": lambda lines: lines  # Maintain original content
    },
    "CONNECT WITH DB": {
        "pattern": r"EXEC\s+SQL\s+CONNECT\s+\S+\s+AT\s+(.*\S)\s*;",
        "action": lambda lines: lines  # Maintain original content
    },

    # Include SQLCA
    "INCLUDE SQLCA": {
        "pattern": r"EXEC\s+SQL\s+INCLUDE\s+SQLCA\s*;",
        "action": lambda lines: lines  # Maintain original content
    },

    # Open Cursor
    "OPEN CURSOR": {
        "pattern": r"EXEC\s+SQL\s+OPEN\s+\w+\s*;",
        "action": lambda lines: lines  # Maintain original content
    },

    # WHENEVER Statements
    "WHENEVER SQLERROR": {
        "pattern": r"EXEC\s+SQL\s+WHENEVER\s+SQLERROR\s+(.*);",
        "action": lambda lines: lines  # Maintain original content
    },

    "WHENEVER NOT FOUND [1]": {
        # "pattern": r"EXEC\s\s*SQL\s\s*WHENEVER\s\s*NOT\s\s*FOUND\s+(.*);",
        "pattern": r"\s*EXEC SQL WHENEVER NOT FOUND\b.*;",
        "action": lambda lines: lines  # Maintain original content
    },

    # WERID TODO: A second copy sometimes hits when the first one doesn't ?
    "WHENEVER NOT FOUND [2]": {
        # "pattern": r"EXEC\s\s*SQL\s\s*WHENEVER\s\s*NOT\s\s*FOUND\s+(.*);",
        "pattern": r"\s*EXEC SQL WHENEVER NOT FOUND\b.*;",
        "action": lambda lines: lines  # Maintain original content
    },

    # Multi-line Statements
    "STATEMENT": {
        "pattern": r"EXEC SQL\b",
        "end_pattern": r";",  # Block terminates with semicolon
        "action": lambda lines: lines  # Maintain original content
    },

    # END; due to r";" hack
    "END;": {
        "pattern": r"END\s*;",
        "action": lambda lines: lines  # Maintain original content
    },
    # END-EXEC for COBOL Compatibility
    "END-EXEC;": {
        "pattern": r"END-EXEC\s*;",
        "action": lambda lines: lines  # Maintain original content
    }
}
