# アンケート・要望フォームの設定

Web版の「アプリ情報」タブに、開発してほしい機能や要望を送信するアンケートフォームへのリンクを表示できます。

## 実装方法

### 方法1: version.py で設定

`version.py` の `FEEDBACK_FORM_URL` にフォームのURLを設定してください。

```python
FEEDBACK_FORM_URL = "https://forms.google.com/your-form-id"
```

### 方法2: 環境変数で設定

デプロイ時に環境変数 `PICTCOMP_FEEDBACK_FORM_URL` を設定すると、`version.py` より優先されます。

```bash
export PICTCOMP_FEEDBACK_FORM_URL="https://forms.google.com/your-form-id"
```

## 推奨フォームサービス

| サービス | 特徴 | 無料枠 |
|----------|------|--------|
| **Google Forms** | 簡単、回答はスプレッドシートに蓄積 | 無制限 |
| **Typeform** | デザイン性が高い | 月10回答まで |
| **Tally** | シンプル、埋め込み可能 | 無制限 |
| **Microsoft Forms** | Office 365 と連携 | 無料枠あり |

## Google Forms の作成手順（例）

1. [Google Forms](https://forms.google.com/) で新しいフォームを作成
2. 質問例：「追加してほしい機能はありますか？」「改善してほしい点はありますか？」
3. フォームを「リンクを送信」で公開
4. 発行されたURLを `FEEDBACK_FORM_URL` に設定

## URL未設定時

URLが設定されていない場合、「お問い合わせはメールでお願いします」と表示され、メールリンクが表示されます。
