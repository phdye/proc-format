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


def test_exec_sql_respects_sqlparse_config(tmp_path):
    cfg = tmp_path / '.sqlparse-format'
    cfg.write_text('keywords:\n  case: lower\n')
    ctx = type('Ctx', (), {'input_file': str(tmp_path / 'sample.pc'), 'verbose': 0})()
    lines = ['EXEC SQL select * from dual;']
    formatted = format_exec_sql_block(lines, 'STATEMENT-Single-Line [1]', ctx)
    assert formatted[0] == 'EXEC SQL select * from dual;'
