# PictComp ビルド手順

Windows用インストーラとmacOS用DMGの作成手順です。

## 📋 必要なツール

### 1. Python 環境
- Python 3.8以上
- pip

### 2. PyInstaller
```powershell
pip install pyinstaller
```

### 3. Inno Setup（Windows インストーラ作成用）
- ダウンロード: https://jrsoftware.org/isdl.php
- Inno Setup 6.x をインストール

---

## 🪟 Windows ビルド

### ステップ1: 依存パッケージのインストール

```powershell
cd C:\path\to\PictComp
pip install -r requirements-gui.txt
pip install pyinstaller
```

### ステップ2: アイコンの作成

```powershell
python assets\icon\create_icons.py
```

`pictcomp_bright.jpg` から `.ico` と `.icns` を生成します。  
（`pictcomp_bright.jpg` が `assets/icon/` に存在する必要があります）

### ステップ3: exe の作成

```powershell
.\build_config\build_windows.bat
```

または個別に実行：

```powershell
pyinstaller --clean --noconfirm build_config\pictcomp_gui.spec
```

### ステップ4: 動作確認

```powershell
.\dist\PictComp.exe
```

### ステップ5: インストーラの作成

1. Inno Setup Compiler を起動
2. `build_config\installer.iss` を開く
3. **Build** → **Compile** (または Ctrl+F9)
4. `installer_output\PictComp-0.1.0-setup.exe` が生成される

---

## 🍎 macOS ビルド

### ローカルでビルドする場合

```bash
cd /path/to/PictComp
pip install -r requirements-gui.txt
pip install pyinstaller

# アイコン作成
python assets/icon/create_icons.py

# ビルド
chmod +x build_config/build_macos.sh
./build_config/build_macos.sh

# DMG作成
chmod +x build_config/create_dmg.sh
./build_config/create_dmg.sh
```

### GitHub Actions でビルドする場合

`main` ブランチへの push またはリリース公開時に、`.github/workflows/build-macos.yml` が自動実行されます。  
生成された DMG は Artifacts またはリリースにアップロードされます。

---

## 📁 出力ファイル

```
PictComp/
├── dist/
│   └── PictComp.exe          # Windows: 単体実行ファイル
│   └── PictComp.app          # macOS: アプリケーションバンドル
└── installer_output/
    └── PictComp-0.1.0-setup.exe   # Windows: インストーラ
    └── PictComp-0.1.0-macOS.dmg   # macOS: DMG
```

---

## ⚠️ トラブルシューティング

### アイコンが見つからない

`pictcomp_bright.ico` または `pictcomp_bright.icns` が無い場合：
```powershell
python assets\icon\create_icons.py
```

### PyInstaller でエラー

```powershell
# キャッシュをクリア
pyinstaller --clean --noconfirm build_config\pictcomp_gui.spec

# build, dist を削除して再試行
rmdir /s /q build
rmdir /s /q dist
```

### HEIC が動作しない

`pillow-heif` が正しくバンドルされない場合、spec の `hiddenimports` に `pillow_heif` が含まれているか確認してください。

### アンチウイルスに検出される

PyInstaller で作成した exe は、一部のアンチウイルスで誤検出されることがあります。  
Windows Defender の除外設定を追加するか、コード署名（有料）を検討してください。

---

## 📝 バージョン更新時の変更箇所

1. `version.py` の `__version__`
2. `build_config/installer.iss` の `MyAppVersion`
3. `build_config/create_dmg.sh` の `VERSION`
4. `build_config/pictcomp_gui_mac.spec` の `version` と `CFBundleShortVersionString`
