import os

import argparse

from proc_format import process_file, ProCFormatterContext

def main():

    parser = argparse.ArgumentParser(description="Format Pro*C files by aligning EXEC SQL and formatting C code.")
    parser.add_argument("input_file", help="Input file to process.")    
    parser.add_argument("output_file", help="Output file to save the formatted content.")
    parser.add_argument("--clang-format", default="clang-format", help="Path to clang-format executable.")
    parser.add_argument("--debug", default="debug", help="Path to debug directory.")

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print("Error: Input file does not exist: {}" % (args.input_file))
        return

    process_file(ProCFormatterContext(args.input_file, args.output_file, args.clang_format, args.debug))

if __name__ == "__main__":
    main()
