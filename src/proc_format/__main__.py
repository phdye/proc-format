import os

import argparse

from proc_format import process_file

def main():
    parser = argparse.ArgumentParser(description="Format Pro*C files by aligning EXEC SQL and formatting C code.")
    parser.add_argument("input_file", help="Input file to process.")
    parser.add_argument("output_file", help="Output file to save the formatted content.")
    parser.add_argument("--clang-format", default="clang-format", help="Path to clang-format executable.")
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: Input file does not exist: {args.input_file}")
        return

    process_file(args.input_file, args.output_file, clang_format_path=args.clang_format)

if __name__ == "__main__":
    main()
