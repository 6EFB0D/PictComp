#!/bin/bash
# PictComp DMG作成スクリプト

set -e

VERSION="0.1.0"
APP_NAME="PictComp"
DMG_NAME="${APP_NAME}-${VERSION}-macOS"
DMG_DIR="dmg_temp"
DMG_OUTPUT="installer_output/${DMG_NAME}.dmg"

cd "$(dirname "$0")/.."

echo "========================================"
echo "Creating DMG for ${APP_NAME} ${VERSION}"
echo "========================================"

# 一時ディレクトリを作成
rm -rf "${DMG_DIR}"
mkdir -p "${DMG_DIR}"

# GUI版アプリをコピー（PyInstallerの出力パスは環境により異なる場合あり）
APP_SOURCE=""
if [ -d "dist/PictComp.app" ]; then
    APP_SOURCE="dist/PictComp.app"
elif [ -d "dist/PictComp/PictComp.app" ]; then
    APP_SOURCE="dist/PictComp/PictComp.app"
elif [ -d "dist/build_config/PictComp.app" ]; then
    APP_SOURCE="dist/build_config/PictComp.app"
fi

if [ -n "$APP_SOURCE" ]; then
    cp -R "$APP_SOURCE" "${DMG_DIR}/PictComp.app"
    echo "✓ Copied PictComp.app from $APP_SOURCE"
else
    echo "ERROR: PictComp.app not found in dist/"
    echo "Contents of dist/:"
    ls -laR dist/ 2>/dev/null || true
    exit 1
fi

# READMEをコピー
if [ -f "README_RELEASE.md" ]; then
    cp "README_RELEASE.md" "${DMG_DIR}/README.md"
    echo "✓ Copied README.md"
fi

# LICENSEをコピー
if [ -f "LICENSE" ]; then
    cp "LICENSE" "${DMG_DIR}/"
    echo "✓ Copied LICENSE"
fi

# アプリケーションフォルダへのシンボリックリンクを作成
ln -s /Applications "${DMG_DIR}/Applications"

# DMG出力ディレクトリを作成
mkdir -p installer_output

# DMGを作成
echo ""
echo "Creating DMG..."
hdiutil create -volname "${APP_NAME}" \
    -srcfolder "${DMG_DIR}" \
    -ov \
    -format UDZO \
    "${DMG_OUTPUT}"

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "DMG created successfully!"
    echo "========================================"
    echo "Output: ${DMG_OUTPUT}"
    echo ""
    
    # 一時ディレクトリを削除
    rm -rf "${DMG_DIR}"
    
    echo "✓ Cleanup completed"
else
    echo "ERROR: DMG creation failed!"
    exit 1
fi
