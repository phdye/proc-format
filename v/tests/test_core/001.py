
import pytest
from proc_format.core import get_marker, is_complete_sql_statement, mark_exec_sql, restore_exec_sql, MARKER_PREFIX

def test_get_marker():
    # Test with different values of n and prefix
    marker = get_marker(n=1, prefix="PREFIX")
    assert marker == f"PREFIX{MARKER_PREFIX} :1:"

def test_is_complete_sql_statement():
    # Test SQL statements for completeness and quote tracking
    sql_complete = "SELECT * FROM table;"
    sql_incomplete = "SELECT * FROM table"
    quoted_sql = 'SELECT * FROM table WHERE name = "O\'Connor";'
    escaped_sql = 'SELECT * FROM table WHERE name = "O\\\'Connor";'

    assert is_complete_sql_statement(sql_complete) == (True, False)
    assert is_complete_sql_statement(sql_incomplete) == (False, False)
    assert is_complete_sql_statement(quoted_sql) == (True, False)
    assert is_complete_sql_statement(escaped_sql) == (True, False)

def test_mark_exec_sql():
    # Test EXEC SQL processing
    input_text = "EXEC SQL SELECT * FROM table;\
Other line;"
    marked, segments = mark_exec_sql(input_text)

    expected_segments = [(1, "EXEC SQL SELECT * FROM table;")]

    assert f"{MARKER_PREFIX} :1:" in marked  # Marker should appear in the output
    assert segments == expected_segments

def test_restore_exec_sql():
    # Test restoring EXEC SQL blocks
    input_text = f"{MARKER_PREFIX} :1:"
    exec_sql_segments = [(1, "EXEC SQL SELECT * FROM table;")]
    expected_output = "EXEC SQL SELECT * FROM table;"

    restored = restore_exec_sql(input_text, exec_sql_segments)
    assert restored == expected_output

# Since pytest-mock is unavailable, use monkeypatch as a fallback for mocking
def test_format_with_clang(monkeypatch):
    # Mock the subprocess call to `clang-format`
    def mock_run(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.stdout = b"formatted output"
        return MockResponse()

    monkeypatch.setattr("subprocess.run", mock_run)
    input_text = "unformatted input"
    from proc_format.core import format_with_clang
    assert format_with_clang(input_text) == "formatted output"
