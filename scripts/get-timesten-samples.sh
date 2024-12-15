#!/bin/bash

# Define the target directory
TARGET_DIR="examples/third-party"

# Create the directory if it does not exist
mkdir -p "$TARGET_DIR"

URL_BASE="https://raw.githubusercontent.com/oracle-samples/oracle-timesten-samples/refs/heads/master/quickstart/classic/sample_code/proc"

# Array of TimesTen Pro*C sample program URLs
declare -a SAMPLES=(
    "addempPROC.pc"
    "ansidyn1.pc"
    "batchfetchPROC.pc"
    "cursorPROC.pc"
    "getempPROC.pc"
    "plsqlPROC.pc"
)

# Download each sample file
echo "Downloading TimesTen Pro*C Sample Programs..."
for file_name in "${SAMPLES[@]}"; do
    url="$URL_BASE/$file_name"
    output_path="$TARGET_DIR/$file_name"
    
    echo "Downloading $file_name..."
    curl -o "$output_path" "$url" || wget -O "$output_path" "$url"
done

echo "TimesTen Pro*C sample programs have been downloaded to $TARGET_DIR."
