#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "$0")/.." && pwd)"
test_binary="$(mktemp /tmp/infoglobe-console.XXXXXX)"
trap 'rm -f "$test_binary"' EXIT
cc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined \
    -I "$repo_dir/firmware" "$repo_dir/firmware/console.c" \
    "$repo_dir/firmware/tests/test_console.c" -o "$test_binary"
"$test_binary"
/workspace/infoglobe-tools/bin/python "$repo_dir/firmware/tests/test_pio.py" \
    "$repo_dir/firmware/build/transmit.pio.h"

/workspace/infoglobe-tools/bin/python "$repo_dir/firmware/tests/test_capture_pio.py" \
    "$repo_dir/firmware/build/capture.pio.h"
cd "$repo_dir"
/workspace/infoglobe-tools/bin/python -m unittest discover -s tools/tests -v
