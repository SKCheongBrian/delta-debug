#!/usr/bin/env sh

VERBOSE=false
OUTPUT_DIR="showcase_output"

mkdir -p "$OUTPUT_DIR"
rm -f "$OUTPUT_DIR"/*.out 2>/dev/null

while [ "$#" -gt 0 ]; do
    case "$1" in
        --verbose) VERBOSE=true ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
    shift
done

for file in ./showcase*.py; do
    base_name=$(basename "$file" .py)
    if [ "$VERBOSE" = true ]; then
        python3 "$file" --verbose > "$OUTPUT_DIR/verbose-$base_name.out" 
    else
        python3 "$file" > "$OUTPUT_DIR/$base_name.out" 
    fi
done