#!/bin/bash
# .iconset から macOS 用 .icns を作成
# macOS の iconutil を使用（macOS でのみ実行可能）

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

create_icns() {
  local base_name="$1"
  local iconset_dir="${SCRIPT_DIR}/${base_name}.iconset"
  local icns_out="${SCRIPT_DIR}/${base_name}.icns"

  if [ ! -d "$iconset_dir" ]; then
    echo "ERROR: $iconset_dir not found. Run create_icons.py first."
    return 1
  fi

  echo "Creating .icns from $iconset_dir"
  iconutil -c icns -o "$icns_out" "$iconset_dir"
  echo "  ✓ Created $icns_out"
}

echo "Creating .icns files..."
echo

create_icns "pictcomp_bright"
create_icns "pictcomp_dark"

echo
echo "Done."
