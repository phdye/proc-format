import pytest
from proc_format.core import format_exec_sql_block

pytest.importorskip('sqlparse')


class Ctx(object):
    def __init__(self, verbose=0, terse=False, silent=False):
        self.verbose = verbose
        self.terse = terse
        self.silent = silent


def test_verbose_reports_sqlparse_use(capsys):
    lines = ['EXEC SQL select * from dual;']
    format_exec_sql_block(lines, 'STATEMENT-Single-Line [1]', Ctx(1))
    out = capsys.readouterr().out
    assert 'sqlparse: formatting' in out


def test_warns_when_sqlparse_skipped(capsys):
    lines = ['EXEC ORACLE OPTION (hold_cursor=yes);']
    format_exec_sql_block(lines, 'ORACLE-Single-Line [1]', Ctx())
    err = capsys.readouterr().err
    assert 'sqlparse: skipped' in err


@pytest.mark.parametrize("ctx", [Ctx(terse=True), Ctx(silent=True)])
def test_warn_suppressed_with_terse_or_silent(ctx, capsys):
    lines = ['EXEC ORACLE OPTION (hold_cursor=yes);']
    format_exec_sql_block(lines, 'ORACLE-Single-Line [1]', ctx)
    out = capsys.readouterr()
    assert out.err == ''

