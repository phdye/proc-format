"""
f_identical.py - Functional identity verification for proc-format

Verifies that two files are functionally identical by comparing them
after removing all whitespace. This ensures code reformatting doesn't
introduce functional changes.
"""

import sys
import hashlib
from pathlib import Path


class FIdenticalResult:
    """Result of functional identity check."""
    
    def __init__(self):
        self.identical = False
        self.size1 = 0
        self.size2 = 0
        self.checksum1 = ""
        self.checksum2 = ""
        self.error_msg = ""
        self.diff_offset = -1
        self.context_before = ""
        self.context_after = ""


def strip_whitespace(content):
    """Remove all whitespace from content.
    
    Args:
        content: String or bytes content
        
    Returns:
        bytes: Content with all whitespace removed
    """
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    # Remove all whitespace characters
    result = bytearray()
    for byte in content:
        if not chr(byte).isspace():
            result.append(byte)
    
    return bytes(result)


def calculate_checksum(data):
    """Calculate SHA256 checksum of data.
    
    Args:
        data: bytes to checksum
        
    Returns:
        str: Hex digest of checksum
    """
    return hashlib.sha256(data).hexdigest()


def find_first_difference(data1, data2):
    """Find byte offset of first difference between two byte arrays.
    
    Args:
        data1: First byte array
        data2: Second byte array
        
    Returns:
        int: Offset of first difference, or -1 if identical
    """
    min_len = min(len(data1), len(data2))
    
    for i in range(min_len):
        if data1[i] != data2[i]:
            return i
    
    # If one is prefix of the other
    if len(data1) != len(data2):
        return min_len
    
    return -1


def extract_context(data, offset, context_size=40):
    """Extract context around a difference point.
    
    Args:
        data: bytes data
        offset: Position of difference
        context_size: Number of chars before/after to show
        
    Returns:
        str: Context string with difference marked
    """
    start = max(0, offset - context_size)
    end = min(len(data), offset + context_size)
    
    context_parts = []
    
    # Add leading ellipsis if not at start
    if start > 0:
        context_parts.append("...")
    
    # Build context with visible characters
    for i in range(start, end):
        if i == offset:
            context_parts.append("[>")
        
        byte = data[i]
        char = chr(byte)
        
        if char.isprintable() and char not in '\n\r\t':
            context_parts.append(char)
        elif char == '\n':
            context_parts.append('\n')
        elif char == '\r':
            context_parts.append('\r')
        elif char == '\t':
            context_parts.append('\t')
        else:
            context_parts.append('\\x{:02x}'.format(byte))
        
        if i == offset:
            context_parts.append("<]")
    
    # Add trailing ellipsis if not at end
    if end < len(data):
        context_parts.append("...")
    
    return ''.join(context_parts)


def f_identical_check(file1_path, file2_path):
    """Check if two files are functionally identical.
    
    Args:
        file1_path: Path to first file
        file2_path: Path to second file
        
    Returns:
        FIdenticalResult: Result object with comparison details
    """
    result = FIdenticalResult()
    
    # Read files
    try:
        with open(file1_path, 'rb') as f:
            content1 = f.read()
    except Exception as e:
        result.error_msg = f"Cannot read {file1_path}: {e}"
        return result
    
    try:
        with open(file2_path, 'rb') as f:
            content2 = f.read()
    except Exception as e:
        result.error_msg = f"Cannot read {file2_path}: {e}"
        return result
    
    # Strip whitespace
    stripped1 = strip_whitespace(content1)
    stripped2 = strip_whitespace(content2)
    
    result.size1 = len(stripped1)
    result.size2 = len(stripped2)
    
    # Calculate checksums
    result.checksum1 = calculate_checksum(stripped1)
    result.checksum2 = calculate_checksum(stripped2)
    
    # Compare
    if stripped1 == stripped2:
        result.identical = True
        return result
    
    # Files differ - find where
    result.identical = False
    result.diff_offset = find_first_difference(stripped1, stripped2)
    
    if result.diff_offset >= 0:
        result.context_before = extract_context(stripped1, result.diff_offset)
        result.context_after = extract_context(stripped2, result.diff_offset)
        result.error_msg = f"Files differ at byte {result.diff_offset} (after whitespace removal)"
    else:
        result.error_msg = f"Files have different sizes: {result.size1} vs {result.size2} bytes"
    
    return result


def print_error(result, file1, file2, fp=sys.stderr):
    """Print detailed error message with context.
    
    Args:
        result: FIdenticalResult object
        file1: Name of first file (for display)
        file2: Name of second file (for display)
        fp: File pointer to write to (default: stderr)
    """
    print("\n" + "=" * 70, file=fp)
    print("  FATAL: Files are NOT functionally identical", file=fp)
    print("=" * 70 + "\n", file=fp)
    
    print(f"File 1: {file1}", file=fp)
    print(f"File 2: {file2}\n", file=fp)
    
    print("After removing all whitespace:", file=fp)
    print(f"  Size 1:     {result.size1} bytes", file=fp)
    print(f"  Checksum 1: {result.checksum1}", file=fp)
    print(f"  Size 2:     {result.size2} bytes", file=fp)
    print(f"  Checksum 2: {result.checksum2}\n", file=fp)
    
    print(result.error_msg, file=fp)
    
    if result.diff_offset >= 0 and result.context_before:
        print("\nContext from file 1:", file=fp)
        print(f"  {result.context_before}\n", file=fp)
        print("Context from file 2:", file=fp)
        print(f"  {result.context_after}\n", file=fp)
        print("Note: [>...<] marks the position of first difference", file=fp)
    
    print("\n" + "=" * 70 + "\n", file=fp)


def verify_functionally_identical(file1, file2, verbose=False):
    """Verify two files are functionally identical, exit on failure.
    
    Args:
        file1: Path to first file
        file2: Path to second file
        verbose: If True, print success message
        
    Raises:
        SystemExit: If files are not identical or cannot be read
    """
    result = f_identical_check(file1, file2)
    
    if result.error_msg and not result.identical:
        print_error(result, file1, file2)
        sys.exit(1)
    
    if result.identical:
        if verbose:
            print(f"✓ Files are functionally identical:", file=sys.stderr)
            print(f"    {file1}", file=sys.stderr)
            print(f"    {file2}", file=sys.stderr)
            print(f"  Size: {result.size1} bytes, Checksum: {result.checksum1[:16]}...", 
                  file=sys.stderr)
        return True
    
    # Should not reach here
    print_error(result, file1, file2)
    sys.exit(1)


# Command-line interface for standalone use
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Compare two files for functional equivalence'
    )
    parser.add_argument('file1', help='First file to compare')
    parser.add_argument('file2', help='Second file to compare')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed comparison information')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Only set exit code (0=same, 1=different)')
    
    args = parser.parse_args()
    
    result = f_identical_check(args.file1, args.file2)
    
    if not args.quiet:
        if result.identical:
            print(f"[SUCCESS] Files are functionally IDENTICAL")
            print(f"  Both files have same content after whitespace normalization")
            print(f"  Size: {result.size1} bytes, Checksum: {result.checksum1[:16]}...")
        else:
            print_error(result, args.file1, args.file2)
    
    sys.exit(0 if result.identical else 1)
