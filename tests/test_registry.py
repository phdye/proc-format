import os
import tempfile
import shutil
from collections import OrderedDict

from proc_format.registry import load_registry
from proc_format.registry import DEFAULT_EXEC_SQL_REGISTRY
from proc_format import core


def write_cfg(dirpath, content):
    path = os.path.join(dirpath, '.exec-sql-parser')
    f = open(path, 'w')
    f.write(content)
    f.close()


def test_registry_override_and_disable():
    # Confirm that local configuration disables and adds registry entries.
    base = tempfile.mkdtemp()
    try:
        write_cfg(base, '{"STATEMENT-Single-Line [1]": null}')
        sub = os.path.join(base, 'sub')
        os.mkdir(sub)
        write_cfg(sub,
                  '{"CUSTOM": {"pattern": "EXEC SQL TEST;", "end_pattern": "END;"}}')
        reg = load_registry(sub)
        assert 'STATEMENT-Single-Line [1]' not in reg
        assert reg['CUSTOM']['pattern'] == 'EXEC SQL TEST;'
        assert 'end_pattern' in reg['CUSTOM']
    finally:
        shutil.rmtree(base)


def test_registry_no_parents():
    # Verify parent directories are ignored when search_parents is False.
    base = tempfile.mkdtemp()
    try:
        write_cfg(base, '{"STATEMENT-Single-Line [1]": null}')
        sub = os.path.join(base, 'sub')
        os.mkdir(sub)
        reg = load_registry(sub, search_parents=False)
        assert 'STATEMENT-Single-Line [1]' in reg
    finally:
        shutil.rmtree(base)


def test_registry_root_stops_search():
    # Ensure a config with "root": true halts upward search.
    base = tempfile.mkdtemp()
    try:
        write_cfg(base, '{"STATEMENT-Single-Line [1]": null}')
        mid = os.path.join(base, 'mid')
        os.mkdir(mid)
        write_cfg(mid, '{"root": true}')
        sub = os.path.join(mid, 'sub')
        os.mkdir(sub)
        reg = load_registry(sub)
        assert 'STATEMENT-Single-Line [1]' in reg
    finally:
        shutil.rmtree(base)


def test_load_registry_verbose(capsys):
    # Ensure verbose output lists configuration file sources.
    base = tempfile.mkdtemp()
    try:
        write_cfg(base, '{"STATEMENT-Single-Line [1]": null}')
        sub = os.path.join(base, 'sub')
        os.mkdir(sub)
        write_cfg(sub, '{"CUSTOM": {"pattern": "EXEC SQL TEST;"}}')
        load_registry(sub, verbose=1)
        captured = capsys.readouterr()
        base_cfg = os.path.join(base, '.exec-sql-parser')
        sub_cfg = os.path.join(sub, '.exec-sql-parser')
        assert base_cfg in captured.out
        assert sub_cfg in captured.out
    finally:
        shutil.rmtree(base)


def test_capture_exec_sql_blocks_variants():
    # Validate capture_exec_sql_blocks handles known registry variants.
    path = os.path.join(os.path.dirname(__file__), 'data', 'exec_sql_variants.pc')
    f = open(path, 'r')
    lines = f.read().splitlines()
    f.close()

    tmpdir = tempfile.mkdtemp()
    try:
        ctx = type('Ctx', (object,), {'sql_dir': tmpdir})()
        registry = OrderedDict()
        for name, entry in DEFAULT_EXEC_SQL_REGISTRY.items():
            def action(lines, name=name):
                return (name, lines)
            e = entry.copy()
            e['action'] = action
            registry[name] = e
        output, captured = core.capture_exec_sql_blocks(ctx, lines, registry)
        assert len(captured) == 9
        assert len(captured[0][1]) == 5
        assert len(captured[1][1]) == 2
        assert len(captured[2][1]) == 2
        markers = []
        for line in output:
            if core.re_MARKER_PREFIX.match(line.strip()):
                markers.append(line)
        assert len(markers) == 9
    finally:
        shutil.rmtree(tmpdir)
