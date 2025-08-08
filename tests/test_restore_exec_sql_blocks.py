import pytest
from proc_format.core import restore_exec_sql_blocks, get_marker


def test_restore_exec_sql_blocks_with_indent():
    # Validates that SQL segments replace markers and adopt the marker's indentation.
    content = "void f()\n{\n    " + get_marker(1) + "\n}"
    segments = [["EXEC SQL SELECT 1;", "END-EXEC;"]]
    restored = restore_exec_sql_blocks(content, segments)
    expected = "void f()\n{\n    EXEC SQL SELECT 1;\n    END-EXEC;\n}"
    assert restored == expected


def test_restore_exec_sql_blocks_missing_segment():
    # Ensures that unused captured segments trigger an error.
    content = get_marker(1)
    segments = [["EXEC SQL SELECT 1;"], ["EXEC SQL SELECT 2;"]]
    with pytest.raises(ValueError):
        restore_exec_sql_blocks(content, segments)
