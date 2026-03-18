#!/bin/bash
# PictComp macOS ビルドスクリプト
# 実行前に: pip install pyinstaller
#
# アイコン作成: python assets/icon/create_icons.py

set -e

cd "$(dirname "$0")/.."

echo "========================================"
echo "PictComp macOS Build Script"
echo "========================================"

# 既存の dist をクリア
rm -rf dist
mkdir -p dist

echo ""
echo "[0/2] Creating icon files..."
python assets/icon/create_icons.py || true

echo ""
echo "[1/2] Building GUI..."
pyinstaller --clean --noconfirm --distpath dist build_config/pictcomp_gui_mac.spec
if [ $? -ne 0 ]; then
    echo "ERROR: PyInstaller build failed!"
    exit 1
fi

echo ""
echo "========================================"
echo "Build completed successfully!"
echo "========================================"
echo ""
echo "Output: dist/PictComp.app"
echo ""
echo "Next step: Run build_config/create_dmg.sh to create DMG"
echo ""
