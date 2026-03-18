# PictComp ライセンス仕様書

Supabase（ライセンス管理）＋ Stripe（決済）を前提とした仕様。  
**pdf-handler** のライセンスコード形態を参照・改変しています。

---

## 1. ライセンスコード形式（pdf-handler 参照）

### 基本形式

```
<プレフィックス>-<形態4文字>-<シリアル28文字>
```

### PictComp 用の例

```
PICT-P101-A1B2C3D4E5F6G7H8I9J0K1L2M3
```

| 要素 | 内容 |
|------|------|
| **プレフィックス** | `PICT-`（固定） |
| **形態4文字** | 種別2文字 + バージョン2文字 |
| **シリアル部** | 28文字（0-9, A-F の16進数大文字） |

---

## 2. 形態コード（4文字）

### 2.1 種別（先頭2文字）

| コード | 意味 |
|--------|------|
| P1 | 買い切り（Purchased） |
| S1 | サブスクリプション |

### 2.2 バージョンコード（後ろ2文字）

| コード | 意味 |
|--------|------|
| 01 | メジャーバージョン 1（買い切り v1.x 用） |
| 02 | メジャーバージョン 2（将来用） |
| 00 | 全バージョン（サブスクリプション用） |

### 2.3 形態コード一覧

| 4文字 | 種別 | バージョン制限 |
|-------|------|----------------|
| P101 | 買い切り v1 | v1.x まで |
| P102 | 買い切り v2 | v2.x まで（将来） |
| S100 | サブスク | 全バージョン |

---

## 3. バリデーション

### 正規表現

```
^PICT-[P1S1][0-9]{2}-[0-9A-F]{28}$
```

### 形態からの情報取得

- **種別**: P1 → 買い切り、S1 → サブスク
- **利用可能メジャーバージョン**: P1→1, P2→2, S1→全バージョン（00）

---

## 4. 料金プラン（案）

| プラン | 価格 | 形態コード |
|--------|------|------------|
| 14日間トライアル | 無料 | （ライセンスキー不要） |
| 買い切り | ¥2,750（税込） | P101 |
| サブスク | ¥220/月（税込） | S100 |

---

## 5. アーキテクチャ（pdf-handler 準拠）

### 5.1 構成

```
[PictComp アプリ] 
    ↓ ライセンスキー検証
[Supabase Edge Function: verify-license]
    ↓ 照会
[Supabase: licenses テーブル]

[Stripe Checkout] 
    ↓ 決済完了
[Stripe Webhook]
    ↓ 呼び出し
[Supabase Edge Function: stripe-webhook]
    ↓ ライセンス作成
[Supabase: licenses テーブル]
```

### 5.2 Supabase テーブル（licenses）

| カラム | 型 | 説明 |
|--------|------|------|
| id | UUID | 主キー |
| license_key | TEXT | ライセンスキー（PICT-XXXX-28文字） |
| plan | TEXT | purchased / subscription_standard |
| user_email | TEXT | 購入者メール |
| stripe_customer_id | TEXT | Stripe 顧客ID |
| stripe_subscription_id | TEXT | サブスク用 |
| stripe_payment_intent_id | TEXT | 決済ID |
| purchased_version | TEXT | 買い切り時のメジャーバージョン（1, 2...） |
| subscription_renewal_date | TIMESTAMPTZ | サブスク更新日 |
| activation_count | INTEGER | アクティベーション数 |
| is_active | BOOLEAN | 有効フラグ |
| created_at, updated_at | TIMESTAMPTZ | 作成・更新日時 |

### 5.3 license_activations（デバイス数制限用）

| カラム | 型 | 説明 |
|--------|------|------|
| id | UUID | 主キー |
| license_id | UUID | licenses への参照 |
| hardware_id | TEXT | マシン固有ID |
| device_name | TEXT | PC名（任意） |
| activation_date | TIMESTAMPTZ | アクティベーション日時 |
| is_active | BOOLEAN | 有効フラグ |

### 5.4 環境変数

| 変数名 | 説明 | デフォルト |
|--------|------|------------|
| LICENSE_PURCHASED_MAJOR_VERSION | 買い切り発行時のメジャーバージョン | 1 |
| SUPABASE_URL | Supabase プロジェクトURL | - |
| SUPABASE_SERVICE_ROLE_KEY | サービスロールキー | - |
| STRIPE_SECRET_KEY | Stripe シークレットキー | - |
| STRIPE_WEBHOOK_SECRET | Webhook 署名検証用 | - |
| RESEND_API_KEY | ライセンスメール送信用（任意） | - |

---

## 6. 生成元（stripe-webhook）

| 決済内容 | 形態コード |
|----------|------------|
| 買い切り | P1 + 現在のメジャーバージョン（01, 02...） |
| サブスク | S100 |

### キー生成SQL（手動発行例）

```sql
-- 買い切り v1 の例
SELECT 'PICT-P101-' || UPPER(SUBSTRING(REPLACE(gen_random_uuid()::TEXT, '-', ''), 1, 28));

-- サブスクの例
SELECT 'PICT-S100-' || UPPER(SUBSTRING(REPLACE(gen_random_uuid()::TEXT, '-', ''), 1, 28));
```

---

## 7. verify-license リクエスト/レスポンス

### リクエスト（POST）

```json
{
  "licenseKey": "PICT-P101-A1B2C3D4E5F6G7H8I9J0K1L2M3",
  "hardwareId": "マシン固有ID",
  "deviceName": "PC名（任意）",
  "appVersion": "2.0.0"
}
```

### レスポンス（成功時）

```json
{
  "isValid": true,
  "plan": "purchased",
  "purchasedVersion": "1",
  "subscriptionRenewalDate": null,
  "lastVerificationDate": "...",
  "nextVerificationDate": null
}
```

### レスポンス（サブスク失敗時）

```json
{
  "isValid": false,
  "errorMessage": "サブスクリプションの有効期限が切れています"
}
```

---

## 8. バージョン制限のロジック

- **買い切り（P101）**: purchased_version が "1" のとき、アプリ v1.x のみ利用可能。v2.0 以降はアップグレード料金が必要。
- **サブスク（S100）**: 全バージョン利用可能。
- **下取り**: 買い切り→サブスク移行時、旧ライセンスを `is_active = false` で失効する。

---

## 9. 参照元

- **pdf-handler**: `docs/specs/license-code-specification.md`
- **pdf-handler**: `supabase/functions/verify-license/index.ts`
- **pdf-handler**: `supabase/functions/stripe-webhook/index.ts`
- **pdf-handler**: `docs/supabase-setup/01_database-schema.sql`
