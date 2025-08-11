import os
import pytest
from proc_format.core import capture_exec_sql_blocks, get_marker
from proc_format.registry import load_registry


def test_execute_with_at_connection(tmp_path):
    # Validates parsing of EXECUTE statements with an AT clause.
    sql_dir = tmp_path / 'sql'
    os.makedirs(str(sql_dir))
    ctx = type('Ctx', (), {'sql_dir': str(sql_dir)})
    lines = [
        'EXEC SQL INCLUDE SQLCA;',
        '',
        'void call(char * alias_arg) {',
        '    EXEC SQL BEGIN DECLARE SECTION;',
        '    char * gl_server_alias = alias_arg;',
        '    EXEC SQL END DECLARE SECTION;',
        '',
        '    EXEC SQL AT :gl_server_alias EXECUTE',
        '    BEGIN',
        '        make_call();',
        '    END;',
        '    END-EXEC;',
        '}',
    ]
    registry = load_registry('.')
    output, blocks = capture_exec_sql_blocks(ctx, lines, registry)
    assert len(blocks) == 4


def test_multi_line_terminated_at_eof(tmp_path):
    # Ensures a multi-line statement ending at EOF is captured.
    sql_dir = tmp_path / 'sql'
    os.makedirs(str(sql_dir))
    ctx = type('Ctx', (), {'sql_dir': str(sql_dir)})
    lines = [
        'EXEC SQL',
        'SELECT * FROM t',
    ]
    registry = load_registry('.')
    output, blocks = capture_exec_sql_blocks(ctx, lines, registry)
    assert output == [get_marker(1)]
    try:
        import sqlparse  # type: ignore  # noqa: F401
    except Exception:
        expected = lines
    else:
        expected = ['EXEC SQL SELECT * FROM t']
    assert blocks == [expected]
