# 開発ガイド

## バージョン管理

- バージョンは `version.py` と `pyproject.toml` で管理
- 変更時は両方を同期して更新
- 変更内容は `CHANGELOG.md` に記録（[Keep a Changelog](https://keepachangelog.com/ja/1.0.0/) 形式）

## バージョンアップ手順

1. `version.py` の `__version__` を更新
2. `pyproject.toml` の `version` を更新
3. `CHANGELOG.md` に変更内容を追記
4. コミット＆プッシュ

```bash
git add version.py pyproject.toml CHANGELOG.md
git commit -m "Bump version to x.x.x"
git tag vx.x.x
git push origin master --tags
```

## Git ワークフロー

- `master` ブランチをメインに使用
- 機能追加・修正はブランチを切って開発後、マージ
- タグはリリース時のみ付与（例: `v2.0.0`）

## テスト実行

```bash
python -m unittest tests.test_image_compressor -v
```

## コードスタイル

- `.editorconfig` に従う（UTF-8, LF, 4スペースインデント）
- Python は PEP 8 を基本とする
