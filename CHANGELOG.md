# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/lang/ja/).

## [Unreleased]

## [2.0.0] - 2026-03-15

### Added
- GUI版を追加（gui_main.py）
- Web版（Streamlit）を追加（app_streamlit.py）
- PNG、WebP形式に対応
- リサイズ機能（長辺ピクセル指定）
- プリセット機能（用途別テンプレート）
- プレビュー機能
- EXIF保持オプション
- 前回フォルダの復元機能
- ユニットテスト（tests/test_image_compressor.py）

### Changed
- プロジェクト構造を整理
- バージョン管理を追加

## [1.0.0] - 初回リリース

### Added
- JPEG/HEIC形式の圧縮に対応
- コマンドライン版（legacy/PictComp.py）
