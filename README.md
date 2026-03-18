# PictComp - 画像一括圧縮アプリ

フォルダを選択するだけで、複数の画像ファイルを一括して圧縮・リサイズできるデスクトップアプリケーションです。

## 主な機能

- **多形式対応**: JPEG、PNG、HEIC、WebP形式に対応
- **一括処理**: フォルダ内の画像を一度に処理
- **リサイズ機能**: 長辺ピクセル指定による自動リサイズ（アスペクト比維持）
- **EXIF保持**: メタデータの保持/削除を選択可能
- **プリセット機能**: 用途別の圧縮設定テンプレート（PowerPoint用、ブログ用、SNS用など）
- **プレビュー機能**: 圧縮前後の画像を比較表示
- **プログレス表示**: 処理状況をリアルタイムで表示
- **ログ機能**: 処理結果をログファイルに記録

## インストール

### 必要な環境

- Python 3.8以上
- Windows 10/11 または macOS 10.14以上

### セットアップ

1. リポジトリをクローンまたはダウンロード
```bash
git clone <repository-url>
cd PictComp
```

2. 依存パッケージをインストール
```bash
pip install -r requirements.txt
```

## 使用方法

### GUI版（推奨）

```bash
python gui_main.py
```

1. 「入力フォルダ」と「出力フォルダ」を選択
2. 必要に応じて圧縮設定を調整、またはプリセットを選択
3. 「プレビュー」ボタンで圧縮結果を確認（オプション）
4. 「圧縮開始」ボタンをクリック

### Web版（Streamlit）

**前提条件**: Streamlitがインストールされている必要があります。

1. **Streamlitのインストール確認**
   ```bash
   pip install streamlit pandas
   ```
   または、requirements.txtからすべての依存関係をインストール：
   ```bash
   pip install -r requirements.txt
   ```

2. **プロジェクトフォルダに移動**
   ```bash
   cd PictComp
   ```
   （Windowsの場合、プロジェクトフォルダのパスに移動してください）

3. **Web版を起動**
   ```bash
   streamlit run app_streamlit.py
   ```
   または、Pythonから直接実行：
   ```bash
   python -m streamlit run app_streamlit.py
   ```

4. **ブラウザでアクセス**
   - コマンド実行後、自動的にブラウザが開きます
   - 開かない場合は、表示されたURL（通常は `http://localhost:8501`）をブラウザで開いてください

**トラブルシューティング**:
- `'streamlit'は、内部コマンドまたは外部コマンド...` というエラーが出る場合：
  - Pythonのパスが正しく設定されているか確認
  - `python -m streamlit run app_streamlit.py` を試してください
  - 仮想環境を使用している場合は、仮想環境が有効になっているか確認

### コマンドライン版（旧版・Legacy）

```bash
python legacy/pictcomp_legacy.py
```

フォルダ選択ダイアログが表示されるので、入力フォルダと出力フォルダを選択してください。新規利用は GUI版 または Web版 を推奨します。

## 設定オプション

- **目標サイズ**: 目標とするファイルサイズ（KB）
- **最大サイズ**: リサイズ時の長辺ピクセル数（0=リサイズなし）
- **JPEG品質**: 圧縮品質（20-100）
- **出力形式**: auto（自動）、jpg、png、webp
- **EXIF保持**: メタデータの保持/削除
- **WebP設定**: WebP出力時の品質と可逆/非可逆圧縮の選択

## プリセット

以下の用途別プリセットが用意されています：

- **PowerPoint用**: 300KB目標、1920px、高品質
- **ブログ用**: 200KB目標、1600px、標準品質
- **SNS用**: 500KB目標、2048px、高品質
- **Web用（高品質）**: 500KB目標、2400px、WebP形式
- **Web用（軽量）**: 100KB目標、1200px、WebP形式
- **メール添付用**: 150KB目標、1280px、標準品質
- **アーカイブ用**: 1000KB目標、リサイズなし、EXIF保持
- **PNG透過保持**: PNG形式で透過情報を保持

## 対応形式

### 入力形式
- JPEG (.jpg, .jpeg)
- PNG (.png)
- HEIC (.heic) - iPhoneで撮影した写真
- WebP (.webp)

### 出力形式
- JPEG (.jpg)
- PNG (.png)
- WebP (.webp)

## ファイル構成

```
PictComp/
├── gui_main.py              # GUI版メインアプリ（推奨）
├── app_streamlit.py         # Web版アプリ（Streamlit）
├── image_compressor.py      # 圧縮エンジン
├── config_manager.py        # 設定管理
├── presets.py               # プリセット管理
├── exif_viewer.py           # EXIF情報閲覧
├── image_viewer.py          # 画像ビューア
├── license_manager.py       # ライセンス管理
├── version.py               # バージョン情報
├── requirements.txt         # 依存関係
├── pyproject.toml           # プロジェクトメタデータ
├── CHANGELOG.md             # 変更履歴
├── legacy/                  # 旧版（v1.x）
│   ├── pictcomp_legacy.py   # コマンドライン版
│   └── README.md
├── tests/                   # ユニットテスト
│   └── test_image_compressor.py
├── docs/                    # ドキュメント
│   └── GIT_SETUP.md
└── README.md
```

## ログファイル

処理ログは以下の場所に保存されます：
- Windows: `C:\Users\<ユーザー名>\.pictcomp\logs\app.log`
- macOS/Linux: `~/.pictcomp/logs/app.log`

## トラブルシューティング

### HEIC形式が読み込めない場合

`pillow-heif`パッケージが正しくインストールされているか確認してください：
```bash
pip install pillow-heif
```

macOSの場合、追加のライブラリが必要な場合があります：
```bash
brew install libheif
```

### メモリ不足エラー

大量の画像を処理する場合、メモリ不足になることがあります。その場合は、一度に処理するファイル数を減らすか、バッチ処理に分割してください。

## 連絡先

- **ホームページ**: [Office Go Plan](https://6EFB0D.github.io/office-goplan/)
- **お問合せ先**: support@office-goplan.com

## ライセンス

© 2026 Office Go Plan

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能要望は、GitHubのIssuesでお願いします。プルリクエストも歓迎します。

## 更新履歴

詳細は [CHANGELOG.md](CHANGELOG.md) を参照してください。