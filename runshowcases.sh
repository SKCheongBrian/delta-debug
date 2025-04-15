#!/usr/bin/env sh

VERBOSE=false

while [ "$#" -gt 0 ]; do
    case "$1" in
        --verbose) VERBOSE=true ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
    shift
done

if [ "$VERBOSE" = true ]; then
    python3 ./showcase1.py --verbose > verbose-showcase1.out 
    python3 ./showcase2.py --verbose > verbose-showcase2.out 
    python3 ./showcase3.py --verbose > verbose-showcase3.out 
else
    python3 ./showcase1.py > showcase1.out 
    python3 ./showcase2.py > showcase2.out 
    python3 ./showcase3.py > showcase3.out 
fi