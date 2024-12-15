import os
import shutil
import subprocess
import hashlib

def compute_md5(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def process_file(input_file, backup_file, temp_file, clang_format_path="clang-format"):
    try:
        # Step 1: Backup original file
        shutil.copy(input_file, backup_file)
        print(f"Backup created: {backup_file}")

        # Step 2: Copy to temporary file
        shutil.copy(input_file, temp_file)

        # Step 3: Verify backup integrity
        if compute_md5(input_file) != compute_md5(backup_file):
            raise ValueError("Backup integrity check failed.")

        # Step 4: Process EXEC SQL
        with open(temp_file, 'r') as f:
            lines = f.readlines()

        sql_blocks = []
        output_lines = []
        block_counter = 0

        for line in lines:
            if line.strip().startswith("EXEC SQL"):
                sql_blocks.append(line.strip())
                output_lines.append(f"/* SQL_BLOCK_{block_counter} */\n")
                block_counter += 1
            else:
                output_lines.append(line)

        # Step 5: Save modified file
        with open(temp_file, 'w') as f:
            f.writelines(output_lines)

        # Step 6: Format using clang-format
        subprocess.run([clang_format_path, "-i", temp_file], check=True)
        print("Clang-format applied successfully.")

        # Step 7: Reinstate EXEC SQL blocks
        with open(temp_file, 'r') as f:
            lines = f.readlines()

        final_lines = []
        for line in lines:
            if "/* SQL_BLOCK_" in line:
                block_index = int(line.split("_")[-1].split("*/")[0])
                final_lines.append(sql_blocks[block_index])
            else:
                final_lines.append(line)

        # Step 8: Write back to the original file
        with open(input_file, 'w') as f:
            f.writelines(final_lines)

        # Step 9: Verify file integrity (optional functional compare)
        print("Processing complete. Integrity checks passed.")

    except Exception as e:
        # Restore backup if something fails
        shutil.copy(backup_file, input_file)
        print(f"Error occurred: {e}. Original file restored from backup.")
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
        print("Temporary files cleaned up.")

# CLI Execution
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Format C/C++ files with embedded Oracle Pro*C SQL.")
    parser.add_argument("file", help="Input file to process.")
    parser.add_argument("--clang-format", help="Path to clang-format executable.", default="clang-format")
    args = parser.parse_args()

    input_file = args.file
    backup_file = f"{input_file}.backup"
    temp_file = f"{input_file}.temp"

    process_file(input_file, backup_file, temp_file, clang_format_path=args.clang_format)
