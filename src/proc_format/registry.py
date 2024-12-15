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
    "CURSOR - DECLARE": {
        "pattern": r"EXEC\s+SQL\s+DECLARE\s+\w+\s+CURSOR\s+FOR\b",
        "end_pattern": r";",  # Multi-line ending with semicolon
        "action": lambda lines: lines  # Maintain original content
    },
    # Fetch Cursor
    "CURSOR - FETCH": {
        "pattern": r"EXEC\s+SQL\s+FETCH\b(.*);",
        "action": lambda lines: lines  # Maintain original content
    },
    # Close Cursor
    "CURSOR - CLOSE": {
        "pattern": r"EXEC\s+SQL\s+CLOSE\b(.*);",
        "action": lambda lines: lines  # Maintain original content
    },

    # Commit Work
    "COMMIT": {
        "pattern": r"EXEC\s+SQL\s+COMMIT\b(.*);",
        "action": lambda lines: lines  # Maintain original c*ntent
    },

    # Rollback Work
    "ROLLBACK": {
        "pattern": r"EXEC\s+SQL\s+ROLLBACK\b(.*);",
        "action": lambda lines: lines  # Maintain original c*ntent
    },

    # Connect Statement:
    #   EXEC SQL CONNECT { :user IDENTIFIED BY :oldpswd | :usr_psw }
    #       [[ AT { dbname | :host_variable }] USING :connect_string ]
    #       [ {ALTER AUTHORIZATION :newpswd  |  IN { SYSDBA | SYSOPER } MODE} ] ;
    #
    "CONNECT": {
        "pattern": r"EXEC\s+SQL\s+CONNECT\b(.*);",
        "action": lambda lines: lines  # Maintain original content
    },

    # Include SQLCA
    "INCLUDE SQLCA": {
        "pattern": r"EXEC\s+SQL\s+INCLUDE\s+SQLCA\s*;",
        "action": lambda lines: lines  # Maintain original content
    },

    # Open Cursor
    "OPEN CURSOR": {
        "pattern": r"EXEC\s+SQL\s+OPEN\b(.*);",
        "action": lambda lines: lines  # Maintain original content
    },

    # WHENEVER Statements
    "WHENEVER SQLERROR": {
        "pattern": r"EXEC\s+SQL\s+WHENEVER\s+SQLERROR\b(.*);",
        "action": lambda lines: lines  # Maintain original content
    },

    "WHENEVER NOT FOUND [1]": {
        "pattern": r"EXEC\s+SQL\s+WHENEVER\s+NOT\s+FOUND\b(.*);",
        # "pattern": r"EXEC SQL WHENEVER NOT FOUND\b(.*);",
        "action": lambda lines: lines  # Maintain original content
    },

    # TODO: A second copy will catch it when the first one doesn't ?
    #   Possibly only Python 3.2.5 issue?
    "WHENEVER NOT FOUND [2]": {
        "pattern": r"EXEC\s+SQL\s+WHENEVER\s+NOT\s+FOUND\b(.*);",
        # "pattern": r"EXEC SQL WHENEVER NOT FOUND\b(.*);",
        "action": lambda lines: lines  # Maintain original content
    },

    # Multi-line Statements
    "STATEMENT-Single-Line": {
        "pattern": r"EXEC SQL\b(.*);",
        "action": lambda lines: lines  # Maintain original content
    },

    "STATEMENT-Multi-Line": {
        "pattern": r"EXEC SQL\b",
        "end_pattern": r";",  # Block terminates with semicolon
        "action": lambda lines: lines  # Maintain original content
    },

    # END-EXEC for COBOL Compatibility
    "END-EXEC": {
        "pattern": r"END-EXEC\b(.*);",
        "action": lambda lines: lines  # Maintain original content
    },

    # END; due to r";" hack
    # ** 'END' must be after 'END-EXEC' as '-' matches '\b'
    "END": {
        "pattern": r"END\b(.*);",
        "action": lambda lines: lines  # Maintain original content
    }
}
