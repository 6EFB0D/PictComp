# 圧縮・形式変換

## 形式変換のみ

「形式変換のみ（圧縮・リサイズなし）」にチェックを入れると、画質を維持したまま形式だけを変更します。例：HEIC→JPEG、BMP→PNG。

## 対応形式

| 入力 | 出力 |
|------|------|
| JPEG, PNG, HEIC, WebP, TIFF, BMP | JPEG, PNG, WebP, TIFF, BMP |

## 主な形式変換の例

- **HEIC→JPEG**: iPhone写真をWindowsで扱いやすい形式に
- **BMP→JPEG/PNG**: スキャン画像の保存形式を変更
- **TIFF→PNG**: 印刷用画像をWeb用に
- **PNG→WebP**: Web用に軽量化

## 出力形式の設定

- **auto**: 入力形式に合わせて自動判定
- **jpg**: JPEG形式で出力
- **png**: PNG形式（透過を保持）
- **webp**: WebP形式
- **tiff**: TIFF形式（LZW圧縮）
- **bmp**: BMP形式
