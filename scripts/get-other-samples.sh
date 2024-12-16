#!/bin/bash

# Define the target directory
TARGET_DIR="examples/third-party"

# Create the directory if it does not exist
mkdir -p "$TARGET_DIR"

# Array of other Pro*C sample program URLs
declare -a URLS=(
    "https://raw.githubusercontent.com/campim/pro_c_code/master/exec_proc_oracle.pc"
    "https://raw.githubusercontent.com/campim/pro_c_code/master/generate_letters.pc"
    "https://raw.githubusercontent.com/rubin55/proc-adventures/refs/heads/master/hello.pc"
    "https://raw.githubusercontent.com/linux-experiments/proc-hello-world/refs/heads/master/hello.pc"
    "https://raw.githubusercontent.com/linux-experiments/proc-hello-world/refs/heads/master/hello-world.pc"
    "https://raw.githubusercontent.com/gregrahn/oracle-ascii-unload/refs/heads/master/oracle-ascii-unload.pc"
    "https://raw.githubusercontent.com/mvallebr/oralib/refs/heads/master/oralib.pc"
    ""
)

echo "Downloading Other Pro*C Sample Programs..."
for url in "${URLS[@]}"; do
    file_name=$(basename "$url" | sed 's/%20/-/g;s/%2520/-/g;s/%2A/-/g;s/[*]/-/g'  )
    if [[ "$file_name" != *".pc" ]]; then
        file_name="${file_name}.pc"
    fi
    output_path="$TARGET_DIR/$file_name"
    echo "Downloading $file_name..."
    wget -v -O "$output_path" "$url" || curl -o "$output_path" "$url"
done
