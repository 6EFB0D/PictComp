# PictComp_Dev リポジトリ作成ガイド

ローカル Git リポジトリは初期化済みです。以下のいずれかの方法で GitHub にプッシュしてください。

---

## 方法A: GitHub CLI で作成（推奨）

### 1. GitHub にログイン

```bash
gh auth login
```

- 「GitHub.com」を選択
- 「HTTPS」を選択
- 「Login with a web browser」を選択
- 表示されたコードをブラウザで入力して認証

### 2. リポジトリを作成してプッシュ

```bash
cd d:\Users\admin_mak\project\PictComp
gh repo create PictComp_Dev --private --source=. --remote=origin --push
```

これで **Private** の `PictComp_Dev` リポジトリが作成され、コードがプッシュされます。

---

## 方法B: GitHub ウェブで手動作成

### 1. リポジトリを作成

1. https://github.com/new を開く
2. **Repository name**: `PictComp_Dev`
3. **Private** を選択
4. **「Add a README file」はチェックしない**（ローカルに既にあるため）
5. 「Create repository」をクリック

### 2. リモートを追加してプッシュ

GitHub に表示される URL を使って、以下を実行します。
（`YOUR_USERNAME` をあなたの GitHub ユーザー名に置き換えてください）

```bash
cd d:\Users\admin_mak\project\PictComp
git remote remove origin   # 既存の origin がある場合
git remote add origin https://github.com/YOUR_USERNAME/PictComp_Dev.git
git push -u origin master
```
