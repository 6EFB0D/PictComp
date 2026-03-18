# PictComp アイコン

## ファイル一覧

| ファイル | 用途 |
|----------|------|
| `pictcomp_bright.jpg` | 元画像（明るい版） |
| `pictcomp_dark.jpg` | 元画像（暗い版） |
| `pictcomp_bright.ico` | Windows用アイコン（明るい版） |
| `pictcomp_dark.ico` | Windows用アイコン（暗い版） |
| `pictcomp_bright.icns` | macOS用アイコン（明るい版） |
| `pictcomp_dark.icns` | macOS用アイコン（暗い版） |

## アイコンの作成方法

### 1. Windows用 .ico と macOS用 .iconset の作成

```bash
python assets/icon/create_icons.py
```

- `pictcomp_bright.ico`, `pictcomp_dark.ico` が生成されます
- `pictcomp_bright.iconset/`, `pictcomp_dark.iconset/` が生成されます

### 2. macOS用 .icns の作成

`create_icons.py` 実行時に .icns も自動生成されます（Windows/macOS/Linux 対応）。

macOS で `iconutil` を使う場合は、別途 `create_icns.sh` を実行することも可能です。

## 使い分け

- **pictcomp_bright**: 通常・ライトモード向け
- **pictcomp_dark**: ダークモード向け
