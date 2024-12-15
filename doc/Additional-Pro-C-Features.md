Yes, I can extend the current implementation to adhere to the **registry-based model**. The additions will follow the structure of `EXEC_SQL_REGISTRY`, ensuring consistency with the current design.

Here’s how we can address the missing features, broken down into individual registry entries:

---

### Proposed Additions to `EXEC_SQL_REGISTRY`

#### 1. **Transaction Control**
```python
"ROLLBACK": {
    "pattern": r"EXEC SQL ROLLBACK;",
    "action": lambda lines: [lines[0].strip()]  # Single-line processor
},
```

#### 2. **Advanced Cursor Features**
```python
"DECLARE SCROLL CURSOR": {
    "pattern": r"EXEC SQL DECLARE \w+ SCROLL CURSOR FOR",
    "end_pattern": r";",  # Multi-line ending with semicolon
    "action": lambda lines: lines  # Maintain original content
},
"DECLARE CURSOR FOR UPDATE": {
    "pattern": r"EXEC SQL DECLARE \w+ CURSOR FOR .* FOR UPDATE",
    "end_pattern": r";",  # Multi-line ending with semicolon
    "action": lambda lines: lines  # Maintain original content
},
```

#### 3. **Connection Management**
```python
"SET CONNECTION": {
    "pattern": r"EXEC SQL SET CONNECTION \S+;",
    "action": lambda lines: [lines[0].strip()]  # Single-line processor
},
"RELEASE": {
    "pattern": r"EXEC SQL RELEASE;",
    "action": lambda lines: [lines[0].strip()]  # Single-line processor
},
```

#### 4. **Dynamic SQL**
```python
"PREPARE": {
    "pattern": r"EXEC SQL PREPARE \w+ FROM",
    "end_pattern": r";",  # Multi-line ending with semicolon
    "action": lambda lines: lines  # Maintain original content
},
"EXECUTE": {
    "pattern": r"EXEC SQL EXECUTE \w+;",
    "action": lambda lines: [lines[0].strip()]  # Single-line processor
},
"DESCRIBE": {
    "pattern": r"EXEC SQL DESCRIBE \w+;",
    "action": lambda lines: [lines[0].strip()]  # Single-line processor
},
```

#### 5. **Embedded PL/SQL Blocks**
```python
"PL/SQL BLOCK": {
    "pattern": r"EXEC SQL BEGIN",
    "end_pattern": r"END;",
    "action": lambda lines: lines  # Maintain original content
},
```

---

### Updated Registry with Full Feature List

Here is the updated `EXEC_SQL_REGISTRY` including the proposed additions:

```python
EXEC_SQL_REGISTRY = {
    # Variable Declarations
    "DECLARE SECTION - BEGIN": {
        "pattern": r"EXEC SQL BEGIN DECLARE SECTION;",
        "action": lambda lines: [lines[0].strip()]
    },
    "DECLARE SECTION - END": {
        "pattern": r"EXEC SQL END DECLARE SECTION;",
        "action": lambda lines: [lines[0].strip()]
    },

    # Transaction Control
    "COMMIT WORK RELEASE": {
        "pattern": r"EXEC SQL COMMIT WORK RELEASE;",
        "action": lambda lines: [lines[0].strip()]
    },
    "ROLLBACK": {
        "pattern": r"EXEC SQL ROLLBACK;",
        "action": lambda lines: [lines[0].strip()]
    },

    # Cursor Operations
    "DECLARE CURSOR": {
        "pattern": r"EXEC SQL DECLARE \w+ CURSOR FOR",
        "end_pattern": r";",
        "action": lambda lines: lines
    },
    "DECLARE SCROLL CURSOR": {
        "pattern": r"EXEC SQL DECLARE \w+ SCROLL CURSOR FOR",
        "end_pattern": r";",
        "action": lambda lines: lines
    },
    "DECLARE CURSOR FOR UPDATE": {
        "pattern": r"EXEC SQL DECLARE \w+ CURSOR FOR .* FOR UPDATE",
        "end_pattern": r";",
        "action": lambda lines: lines
    },
    "OPEN CURSOR": {
        "pattern": r"EXEC SQL OPEN \w+;",
        "action": lambda lines: [lines[0].strip()]
    },
    "CLOSE CURSOR": {
        "pattern": r"EXEC SQL CLOSE \w+;",
        "action": lambda lines: [lines[0].strip()]
    },
    "FETCH CURSOR": {
        "pattern": r"EXEC SQL FETCH \w+;",
        "action": lambda lines: [lines[0].strip()]
    },

    # Connection Management
    "CONNECT": {
        "pattern": r"EXEC SQL CONNECT \S+;",
        "action": lambda lines: [lines[0].strip()]
    },
    "SET CONNECTION": {
        "pattern": r"EXEC SQL SET CONNECTION \S+;",
        "action": lambda lines: [lines[0].strip()]
    },
    "RELEASE": {
        "pattern": r"EXEC SQL RELEASE;",
        "action": lambda lines: [lines[0].strip()]
    },

    # Dynamic SQL
    "PREPARE": {
        "pattern": r"EXEC SQL PREPARE \w+ FROM",
        "end_pattern": r";",
        "action": lambda lines: lines
    },
    "EXECUTE": {
        "pattern": r"EXEC SQL EXECUTE \w+;",
        "action": lambda lines: [lines[0].strip()]
    },
    "DESCRIBE": {
        "pattern": r"EXEC SQL DESCRIBE \w+;",
        "action": lambda lines: [lines[0].strip()]
    },

    # Error Handling
    "WHENEVER SQLERROR": {
        "pattern": r"EXEC SQL WHENEVER SQLERROR .*;",
        "action": lambda lines: [lines[0].strip()]
    },
    "WHENEVER NOT FOUND": {
        "pattern": r"EXEC SQL WHENEVER NOT FOUND .*;",
        "action": lambda lines: [lines[0].strip()]
    },

    # Preprocessor Directives
    "INCLUDE SQLCA": {
        "pattern": r"EXEC SQL INCLUDE SQLCA;",
        "action": lambda lines: [lines[0].strip()]
    },

    # COBOL Compatibility
    "END-EXEC": {
        "pattern": r"END-EXEC;",
        "action": lambda lines: [lines[0].strip()]
    },

    # Embedded PL/SQL Blocks
    "PL/SQL BLOCK": {
        "pattern": r"EXEC SQL BEGIN",
        "end_pattern": r"END;",
        "action": lambda lines: lines
    },

    # Multi-line SQL Statements
    "STATEMENT": {
        "pattern": r"EXEC SQL\\b",
        "end_pattern": r";",
        "action": lambda lines: lines
    }
}
```

---

### Next Steps

Would you like me to:
1. **Update your `registry.py`** with the extended entries?
2. Implement test cases to validate these new constructs?