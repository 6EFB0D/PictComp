# PictComp ヘルプ - MkDocs（Material for MkDocs）のビルド方法

## MkDocsについて

MkDocsは、Markdownから静的HTMLドキュメントを生成するツールです。Material for MkDocsテーマを使用することで、検索機能やレスポンシブデザイン、日本語対応の美しいドキュメントサイトを構築できます。

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements-docs.txt
```

または個別にインストール:

```bash
pip install mkdocs mkdocs-material
```

### 2. ドキュメントのプレビュー（開発サーバー）

```bash
mkdocs serve
```

ブラウザで http://127.0.0.1:8000 を開くと、リアルタイムでプレビューできます。ファイルを編集すると自動的にリロードされます。

### 3. 静的HTMLのビルド

```bash
mkdocs build
```

ビルド結果は `site/` フォルダに出力されます。このフォルダをWebサーバーに配置するか、GitHub Pagesなどで公開できます。

## ディレクトリ構成

```
PictComp/
├── mkdocs.yml              # MkDocs設定
├── requirements-docs.txt    # ドキュメント用依存関係
├── docs/
│   ├── index.md            # はじめに（ホーム）
│   └── help/
│       ├── getting_started.md
│       ├── compression.md
│       ├── presets.md
│       ├── file_selection.md
│       ├── exif.md
│       ├── batch.md
│       ├── viewer.md
│       ├── troubleshooting.md
│       └── license.md
│   └── assets/             # ヘッダロゴ・ファビコン（pictcomp_bright からコピー）
│       ├── logo.jpg
│       └── favicon.ico
└── site/                   # mkdocs build の出力先
```

アイコンを更新した場合は、`assets/icon/pictcomp_bright.jpg` と `pictcomp_bright.ico` を `docs/assets/` にコピーしてください。

## アプリ内ヘルプとの関係

- **MkDocs**: Web公開・開発時のプレビュー向け。`mkdocs build` で静的HTMLを生成。
- **アプリ内ヘルプ**: `docs/help/*.html` がPyInstallerで同梱され、「ヘルプを開く」でブラウザ表示されます。

Markdown（`docs/help/*.md`）はMkDocs用のソースです。
