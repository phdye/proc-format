import os
import pytest
from proc_format.core import capture_exec_sql_blocks
from proc_format.registry import load_registry


def test_execute_with_at_connection(tmp_path):
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


def test_unterminated_multi_line(tmp_path):
    sql_dir = tmp_path / 'sql'
    os.makedirs(str(sql_dir))
    ctx = type('Ctx', (), {'sql_dir': str(sql_dir)})
    lines = [
        'EXEC SQL',
        'SELECT * FROM t',
    ]
    registry = load_registry('.')
    with pytest.raises(ValueError) as excinfo:
        capture_exec_sql_blocks(ctx, lines, registry)
    assert 'Unterminated EXEC SQL STATEMENT-Multi-Line' in str(excinfo.value)
