# PictComp ページ実装ガイド（Office Go Plan HP）

GitHub Pages（Office Go Plan サイト）に PictComp の製品ページを追加する際の引き継ぎ用プロンプトです。

---

## 実装先

- **リポジトリ**: `office-goplan`（`https://6EFB0D.github.io/office-goplan/`）
- **参考**: 既存の `zipsearch.html` の構成・スタイルを踏襲する

---

## ページ構成（zipsearch.html をベースに）

### 1. ヒーロー・キャッチ
- ロゴ画像 + アプリ名「PictComp」
- キャッチコピー: 「画像を一括圧縮」
- 説明文: フォルダを選択するだけで、複数の画像を一括して圧縮・リサイズできるアプリケーションです。

### 2. 機能・特徴
- **多形式対応**: JPEG、PNG、HEIC、WebP
- **一括処理**: フォルダ内の画像を一度に処理
- **プリセット機能**: PowerPoint用、ブログ用、SNS用、Web用など用途別テンプレート
- **2つのインターフェース**: GUI版 / Web版（Streamlit）
- **EXIF対応**: メタデータの保持/削除を選択可能（Pro版・トライアル）
- **プレビュー機能**: 圧縮前後の比較表示

### 3. UI キャプチャ（スクリーンショット）
以下の画像を `assets/pictcomp/` に配置する。

| ファイル名 | 説明 | 撮影手順 |
|-----------|------|----------|
| `gui-main.png` | GUI メイン画面 | GUI版を起動し、プリセット・圧縮設定・フォルダ選択・ファイル一覧・圧縮開始ボタンが見える状態で撮影。左ペイン（設定）と右ペイン（ファイル一覧）が両方見えること。 |
| `gui-compressed.png` | 圧縮完了後の画面 | 圧縮実行後、プログレスバーが完了し、処理結果（成功件数など）が表示されている状態で撮影。 |
| `web-main.png` | Web版メイン画面 | Web版（Streamlit）を起動し、タブ（圧縮・使い方・アプリ情報）とメインの圧縮エリアが見える状態で撮影。 |

### 4. ダウンロード
- バージョンバッジ: v0.1.0
- リリースページへのリンク（GitHub Releases の URL を設定）
- プラットフォーム: Windows / macOS / Linux（リリース準備状況に応じて）

### 5. 無料版 vs Pro版（比較表）
| 項目 | 無料版 | Pro版・トライアル |
|------|--------|-------------------|
| 1回の処理枚数 | 20枚まで | 無制限 |
| EXIF保持 | ❌ | ✅ |
| レポートエクスポート | ❌ | ✅ |
| ファイル名変更（撮影日時） | ❌ | ✅ |
| 基本圧縮・プリセット・リサイズ | ✅ | ✅ |


- **プレリリース**: 初回起動から14日間は全機能を無料でお試しいただけます。

### 6. お問い合わせ
- support@office-goplan.com

---

## 必要な作業

### 1. office-goplan リポジトリでの作業

1. **pictcomp.html を作成**
   - `zipsearch.html` をコピーして `pictcomp.html` にリネーム
   - 上記の構成に合わせて内容を差し替え

2. **index.html を更新**
   - ナビゲーションに `<a href="pictcomp.html">PictComp</a>` を追加
   - 製品セクションに PictComp のカードを追加（ZipSearch の下に）

3. **assets/pictcomp/ フォルダを作成**
   - `assets/pictcomp/` にロゴ画像とスクリーンショットを配置

4. **footer のナビを更新**
   - PictComp へのリンクを追加

### 2. PictComp リポジトリでの作業

1. **version.py の PICTCOMP_PAGE_URL を更新**
   - 実装後の URL を設定（例: `https://6EFB0D.github.io/office-goplan/pictcomp.html`）

---

## アプリのキャプチャ仕様

### 共通
- **解像度**: 幅 800px 以上推奨（アスペクト比維持）
- **形式**: PNG
- **内容**: 個人情報や機密データが写り込まないよう、サンプル画像・フォルダで撮影

### gui-main.png
- **撮影対象**: GUI版メイン画面
- **必須で見える要素**:
  - ヘッダー（ロゴ・アプリ名）
  - 左ペイン: プリセット選択、目標サイズ、圧縮設定、EXIFチェック
  - 右ペイン: 入力/出力フォルダ、ファイル一覧、圧縮開始ボタン
- **推奨**: プリセットが選択され、入力フォルダに画像が表示されている状態

### gui-compressed.png
- **撮影対象**: 圧縮完了後の画面
- **必須で見える要素**:
  - プログレスバー（完了状態）
  - 処理結果メッセージ（成功件数など）
  - ステータスバー（トライアル残り日数など）

### web-main.png
- **撮影対象**: Web版（Streamlit）メイン画面
- **必須で見える要素**:
  - ヘッダー（ロゴ・アプリ名）
  - タブ（圧縮 / 使い方 / アプリ情報）
  - 圧縮タブの内容: フォルダ選択、設定、ファイル一覧

### ロゴ画像
- **assets/icon/pictcomp_bright.jpg** を `assets/pictcomp/` にコピーまたは配置
- または zipsearch と同様に PNG 形式で用意（例: `pictcomp_blue.png`）

---

## 引き継ぎ用プロンプト（コピー用）

```
Office Go Plan の GitHub Pages（office-goplan リポジトリ）に PictComp の製品ページを追加してください。

【参考】
- 既存の zipsearch.html の構成・スタイルを踏襲する
- docs/PICTCOMP_PAGE_IMPLEMENTATION.md に詳細な構成・キャプチャ仕様を記載済み

【実装内容】
1. pictcomp.html を作成（zipsearch.html をベースに）
2. index.html のナビ・製品カードに PictComp を追加
3. assets/pictcomp/ に必要な画像を配置

【画像】
- assets/pictcomp/gui-main.png: GUI版メイン画面
- assets/pictcomp/gui-compressed.png: 圧縮完了後の画面
- assets/pictcomp/web-main.png: Web版メイン画面
- ロゴ: PictComp/assets/icon/pictcomp_bright.jpg を参照

【PictComp の特徴】
- 画像一括圧縮（JPEG/PNG/HEIC/WebP）
- プリセット（PowerPoint用、ブログ用、SNS用など）
- GUI版・Web版
- 14日間トライアル（プレリリース）
- 無料版: 20枚/回、Pro版: 無制限（準備中）
```

---

## 補足

- **メールアドレス**: index.html の `support@office-gioplan.com` は typo の可能性あり。`support@office-goplan.com` を確認すること。
- **PictComp リリース**: GitHub Releases が未作成の場合は、ダウンロードセクションを「準備中」表示にするか、Python 実行の案内に変更する。
