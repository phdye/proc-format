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
