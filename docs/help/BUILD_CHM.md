# CHM形式について

CHM（Compiled HTML Help）は、以前はWindowsの標準ヘルプ形式として利用されていましたが、**Microsoft HTML Help Workshop のSDKは現在公開されていません**。

PictCompでは、CHMの代わりに以下の方法でヘルプを提供しています。

## アプリ内ヘルプ

「ヘルプ」→「ヘルプを開く」で、`docs/help/index.html` をブラウザで開きます。PyInstallerでビルドした実行ファイルには、このHTMLヘルプが同梱されます。

## Web公開・開発時プレビュー

Material for MkDocs を使用して、検索機能付きのドキュメントをビルドできます。詳細は [BUILD_MKDOCS.md](../BUILD_MKDOCS.md) を参照してください。
