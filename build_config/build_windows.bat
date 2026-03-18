@echo off
REM PictComp Windows ビルドスクリプト
REM 実行前に: pip install pyinstaller
REM アイコン作成: python assets\icon\create_icons.py

echo ========================================
echo PictComp Windows Build Script
echo ========================================

cd /d "%~dp0\.."

echo.
echo [0/2] Creating icon files...
python assets\icon\create_icons.py
if errorlevel 1 (
    echo WARNING: Icon creation failed. Ensure pictcomp_bright.jpg exists.
    echo Continuing anyway...
)

echo.
echo [1/2] Building GUI (PyInstaller)...
pyinstaller --clean --noconfirm build_config\pictcomp_gui.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Output: dist\PictComp.exe
echo.
echo Next step: Open build_config\installer.iss in Inno Setup
echo            and compile to create setup.exe
echo.
pause
