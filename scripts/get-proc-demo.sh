#!/bin/bash

WHAT="Oracle Pro*C Demo Programs"

# Define the target directory
TARGET_DIR="examples/oracle-proc-demo"

# Create the directory if it does not exist
mkdir -p "$TARGET_DIR"

URL_BASE="https://stuff.mit.edu/afs/sipb/project/oracle-client/arch/sun4x_56/precomp/demo/proc"

# Array of TimesTen Pro*C sample program URLs
declare -a SAMPLES=(
    "ansidyn1.pc"
    "ansidyn2.pc"
    "coldemo1.pc"
    "coldemo1.typ"
    "cppdemo1.pc"
    "cppdemo2.pc"
    "cppdemo3.pc"
    "cv_demo.pc"
    "demo_proc.mk"
    "empclass.h"
    "empclass.pc"
    "lobdemo1.h"
    "lobdemo1.pc"
    "navdemo1.pc"
    "navdemo1.typ"
    "objdemo1.pc"
    "objdemo1.typ"
    "oraca.pc"
    "sample1.pc"
    "sample2.pc"
    "sample3.pc"
    "sample4.pc"
    "sample5.pc"
    "sample6.pc"
    "sample7.pc"
    "sample8.pc"
    "sample9.pc"
    "sample10.pc"
    "sample11.pc"
    "sample12.pc"
    "sqlvcp.pc"
)

# Download each sample file
echo "Downloading ${WHAT} ..."
for file_name in "${SAMPLES[@]}"; do
    url="$URL_BASE/$file_name"
    output_path="$TARGET_DIR/$file_name"
    
    echo "Downloading $file_name..."
    wget -v -O "$output_path" "$url" || curl -o "$output_path" "$url"
done

echo "${WHAT} have been downloaded to $TARGET_DIR."
