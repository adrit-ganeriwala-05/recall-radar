#!/usr/bin/env bash
# Download NHTSA source files once per machine and record SHA-256 sums. Owner: A.
# Usage: bash scripts/fetch_sources.sh [gate1|all]   (default: all)
# Output dir: $RR_RAW_DIR (default: ${RR_DATA_DIR:-data}/raw). Existing files are kept.
set -euo pipefail
SET="${1:-all}"
RAW="${RR_RAW_DIR:-${RR_DATA_DIR:-data}/raw}"
BASE="https://static.nhtsa.gov/odi/ffdd"
GATE1=(cmpl/COMPLAINTS_RECEIVED_2015-2019.zip inv/FLAT_INV.zip rcl/FLAT_RCL_POST_2010.zip
       cmpl/CMPL.txt inv/INV.txt rcl/RCL.txt)
REST=(cmpl/COMPLAINTS_RECEIVED_2010-2014.zip cmpl/COMPLAINTS_RECEIVED_2020-2024.zip)
FILES=("${GATE1[@]}")
[ "$SET" = "all" ] && FILES+=("${REST[@]}")
mkdir -p "$RAW"
for f in "${FILES[@]}"; do
  name="$(basename "$f")"
  if [ -s "$RAW/$name" ]; then echo "keep $name"; continue; fi
  echo "get  $name"
  curl -fL --retry 3 --retry-delay 5 -o "$RAW/$name.part" "$BASE/$f"
  mv "$RAW/$name.part" "$RAW/$name"
done
( cd "$RAW" && if command -v sha256sum >/dev/null; then sha256sum -- *.zip *.txt; else shasum -a 256 -- *.zip *.txt; fi ) \
  | grep -v SHA256SUMS > "$RAW/SHA256SUMS.txt"
echo "wrote $RAW/SHA256SUMS.txt"; cat "$RAW/SHA256SUMS.txt"
