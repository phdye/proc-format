import sys
import subprocess
from proc_format.core import format_with_clang


class DummyCtx(object):
    clang_format_path = 'clang-format'


def test_format_with_clang_encodes_input(monkeypatch):
    # Validates that content is encoded to bytes on Python versions before 3.7.
    captured = {}

    class DummyPopen(object):
        def __init__(self, *args, **kwargs):
            self.returncode = 0
        def communicate(self, input=None):
            captured['input'] = input
            return input, b''

    monkeypatch.setattr(subprocess, 'Popen', DummyPopen)
    monkeypatch.setattr(sys, 'version_info', (3, 6, 0))
    content = 'int x;'
    result = format_with_clang(DummyCtx, content)
    assert captured['input'] == content.encode()
    assert result == content


def test_format_with_clang_text_mode(monkeypatch):
    # Ensures text input is preserved when Python 3.7+ is detected.
    captured = {}

    class DummyPopen(object):
        def __init__(self, *args, **kwargs):
            self.returncode = 0
        def communicate(self, input=None):
            captured['input'] = input
            return input, ''

    monkeypatch.setattr(subprocess, 'Popen', DummyPopen)
    monkeypatch.setattr(sys, 'version_info', (3, 7, 0))
    content = 'int y;'
    result = format_with_clang(DummyCtx, content)
    assert captured['input'] == content
    assert result == content
