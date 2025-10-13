"""
Test f_identical module functionality.
"""

import os
import sys
import tempfile

# Try standard pathlib first, fall back to vendored version
try:
    from pathlib import Path
except ImportError:
    # Add src to path for imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from proc_format.vendor.pathlib import Path

# Add src to path for module imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from proc_format.f_identical import (
    strip_whitespace,
    f_identical_check,
    verify_functionally_identical
)


def test_strip_whitespace():
    """Test whitespace stripping."""
    content = "hello   world\n\t  test"
    result = strip_whitespace(content)
    assert result == b"helloworldtest"
    
    # Test with bytes input
    content_bytes = b"hello   world\n\t  test"
    result = strip_whitespace(content_bytes)
    assert result == b"helloworldtest"
    
    print("✓ test_strip_whitespace passed")


def test_identical_files():
    """Test that identical files (ignoring whitespace) are detected."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
        f1.write("int main() {\n    return 0;\n}\n")
        file1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
        f2.write("int main(){return 0;}")
        file2 = f2.name
    
    try:
        result = f_identical_check(file1, file2)
        assert result.identical, "Files should be functionally identical"
        assert result.size1 == result.size2
        assert result.checksum1 == result.checksum2
        print("✓ test_identical_files passed")
    finally:
        os.unlink(file1)
        os.unlink(file2)


def test_different_files():
    """Test that different files are detected."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
        f1.write("int main() { return 0; }")
        file1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
        f2.write("int main() { return 1; }")
        file2 = f2.name
    
    try:
        result = f_identical_check(file1, file2)
        assert not result.identical, "Files should be functionally different"
        assert result.diff_offset >= 0
        assert result.context_before
        assert result.context_after
        print("✓ test_different_files passed")
    finally:
        os.unlink(file1)
        os.unlink(file2)


def test_context_extraction():
    """Test that context is properly extracted around differences."""
    content1 = "int main() { return 0; }"
    content2 = "int main() { return 1; }"
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
        f1.write(content1)
        file1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
        f2.write(content2)
        file2 = f2.name
    
    try:
        result = f_identical_check(file1, file2)
        assert not result.identical
        # Check that context contains the difference marker
        assert "[>" in result.context_before
        assert "<]" in result.context_before
        assert "[>" in result.context_after
        assert "<]" in result.context_after
        print("✓ test_context_extraction passed")
    finally:
        os.unlink(file1)
        os.unlink(file2)


if __name__ == '__main__':
    print("Running f_identical tests...\n")
    test_strip_whitespace()
    test_identical_files()
    test_different_files()
    test_context_extraction()
    print("\n✓ All f_identical tests passed!")
