import pytest
from proc_format.core import format_exec_sql_block

pytest.importorskip('sqlparse')


def test_exec_sql_formatted():
    lines = ['EXEC SQL select * from dual;']
    formatted = format_exec_sql_block(lines, 'STATEMENT-Single-Line [1]')
    assert formatted[0] == 'EXEC SQL SELECT * FROM dual;'


def test_exec_oracle_unchanged():
    lines = ['EXEC ORACLE OPTION (hold_cursor=yes);']
    formatted = format_exec_sql_block(lines, 'ORACLE-Single-Line [1]')
    assert formatted[0] == lines[0]
