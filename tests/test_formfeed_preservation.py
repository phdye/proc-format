"""Tests for form-feed character preservation in proc-format."""

import pytest
from proc_format.core import preserve_formfeeds, restore_formfeeds


def test_preserve_formfeeds_empty():
    """Test preservation with no form-feeds."""
    content = "Hello, World!"
    preserved, count = preserve_formfeeds(content)
    assert count == 0
    assert preserved == content
    assert '\f' not in preserved


def test_preserve_formfeeds_single():
    """Test preservation with a single form-feed."""
    content = "Line 1\fLine 2"
    preserved, count = preserve_formfeeds(content)
    assert count == 1
    assert '\f' not in preserved
    assert 'FORMFEED_PLACEHOLDER_0000' in preserved


def test_preserve_formfeeds_multiple():
    """Test preservation with multiple form-feeds."""
    content = "A\fB\fC\fD"
    preserved, count = preserve_formfeeds(content)
    assert count == 3
    assert '\f' not in preserved
    assert 'FORMFEED_PLACEHOLDER_0000' in preserved
    assert 'FORMFEED_PLACEHOLDER_0001' in preserved
    assert 'FORMFEED_PLACEHOLDER_0002' in preserved


def test_restore_formfeeds_empty():
    """Test restoration with no markers."""
    content = "Hello, World!"
    restored = restore_formfeeds(content)
    assert restored == content
    

def test_restore_formfeeds_single():
    """Test restoration with a single marker."""
    content = "Line 1/* FORMFEED_PLACEHOLDER_0000 */Line 2"
    restored = restore_formfeeds(content)
    assert restored == "Line 1\fLine 2"
    assert 'FORMFEED_PLACEHOLDER' not in restored


def test_restore_formfeeds_multiple():
    """Test restoration with multiple markers."""
    content = "A/* FORMFEED_PLACEHOLDER_0000 */B/* FORMFEED_PLACEHOLDER_0001 */C"
    restored = restore_formfeeds(content)
    assert restored == "A\fB\fC"
    assert 'FORMFEED_PLACEHOLDER' not in restored


def test_preserve_and_restore_roundtrip():
    """Test that preserve -> restore is idempotent."""
    original = """/* Header */
#include <stdio.h>
\f
void func1() {
    printf("test");
}
\f
int main() {
    return 0;
}
"""
    # Preserve
    preserved, count = preserve_formfeeds(original)
    assert count == 2
    assert '\f' not in preserved
    
    # Restore
    restored = restore_formfeeds(preserved)
    assert restored == original
    assert restored.count('\f') == 2
    assert 'FORMFEED_PLACEHOLDER' not in restored


def test_preserve_formfeeds_with_special_characters():
    """Test preservation with various special characters."""
    content = "Tab:\tNewline:\nFormfeed:\fCarriage:\r"
    preserved, count = preserve_formfeeds(content)
    assert count == 1
    assert '\f' not in preserved
    assert '\t' in preserved  # Other special chars preserved
    assert '\n' in preserved
    assert '\r' in preserved
