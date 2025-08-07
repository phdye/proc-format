import os
import tempfile
import shutil

from proc_format.registry import load_registry


def write_cfg(dirpath, content):
    path = os.path.join(dirpath, '.exec-sql-parser')
    f = open(path, 'w')
    f.write(content)
    f.close()


def test_registry_override_and_disable():
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

