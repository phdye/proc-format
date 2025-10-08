#!/usr/bin/env python3
"""Test form-feed preservation in proc-format."""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from proc_format.core import preserve_formfeeds, restore_formfeeds

def test_preserve_and_restore():
    """Test that form-feeds are preserved and restored correctly."""
    
    # Test content with form-feeds
    test_content = """/* Header comment */
#include <stdio.h>
\f
/* Function 1 */
void func1() {
    printf("Hello\\n");
}
\f
/* Function 2 */
void func2() {
    printf("World\\n");
}
\f
int main() {
    func1();
    func2();
    return 0;
}
"""
    
    print("Original content length:", len(test_content))
    print("Form-feeds in original:", test_content.count('\f'))
    
    # Preserve form-feeds
    preserved, count = preserve_formfeeds(test_content)
    print("\nAfter preserve_formfeeds:")
    print("  Form-feeds found:", count)
    print("  Content length:", len(preserved))
    print("  Form-feeds remaining:", preserved.count('\f'))
    print("  Markers inserted:", preserved.count('FORMFEED_PLACEHOLDER'))
    
    # Check that form-feeds are gone
    assert preserved.count('\f') == 0, "Form-feeds should be completely replaced"
    assert count == 3, "Should have found 3 form-feeds"
    
    # Restore form-feeds
    restored = restore_formfeeds(preserved)
    print("\nAfter restore_formfeeds:")
    print("  Content length:", len(restored))
    print("  Form-feeds restored:", restored.count('\f'))
    print("  Markers remaining:", restored.count('FORMFEED_PLACEHOLDER'))
    
    # Verify restoration
    assert restored == test_content, "Restored content should match original"
    assert restored.count('\f') == 3, "Should have 3 form-feeds restored"
    assert restored.count('FORMFEED_PLACEHOLDER') == 0, "No markers should remain"
    
    print("\n[PASS] All tests passed!")

if __name__ == '__main__':
    test_preserve_and_restore()
