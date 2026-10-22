---
name: dev-review-system
description: "PHASE 7 本番リリース直前ゲートにおいて、本番稼働耐性、セキュリティ、平文シークレット排除、本番モック排除二重防御、Alembic起動保証、ロールバック計画の完全性を総合監査するスキル。"
---

# システム総合レビュー (System Comprehensive Review) スキル V2.4

- **主担当エージェント**: 🛡️ 品質・テスト & 監査・QAスペシャリスト (`qa-engineer`) (Model: `pro`)
- **委譲元 / 統括**: 👑 プロジェクトコンダクター (`conductor`)
- **適用フェーズ**: PHASE 7 本番リリース直前ゲート
- **合否判定ゲート**: `RELEASE APPROVED` の場合のみ本番デプロイ実行可能。`RELEASE BLOCKED` の場合はデプロイを即時停止。

---

## 1. 入力成果物
監査対象として以下のドキュメント・構成ファイルを読み込みます：
- `docs/plans/本番適用作業手順書.md`
- `Dockerfile`, `docker-compose.yml`, `entrypoint.sh`, `litestream.yml`
- 環境変数設定雛形 (`.env.template`, 本番環境変数設定)
- デプロイ設定スクリプト / IaC定義 (Cloud Run設定, GCP IAM/IAPポリシー等)
- `docs/要件定義書.md`（システム展開プロファイル: 2層プロファイル体系）

---

## 2. 監査観点とゼロ・トレランス項目 (Zero Tolerance Items)

### 必須検証チェックリスト（1件でも違反があれば即座に `RELEASE BLOCKED`）
1. **平文シークレット完全排除 (Zero Secrets in Plaintext)**:
   - ソースコード、Dockerfile、`本番適用作業手順書.md` 内にAPIキー、パスワード、秘密鍵が平文で直接記載されていないか。
2. **本番モック無効化の二重防御 (Mock-Free Production Guarantee & Fail-Fast 監査 / V2.4)**:
   - 本番ビルド環境変数において `VITE_ENABLE_MOCK=false` が確実に注入されているか。
   - 本番JSバンドルから MSW (`browser.ts`, `handlers.ts`) がツリーシェイキング等で排除または不活性化され、本番実行時にモック通信が一切走らない二重防御策が講じられているか。
   - **サイレントモックフォールバック厳格禁止 (Fail-Fast原則)**: 通信エラーやIPC障害発生時にモックデータへサイレントフォールバックする記述がクライアント・サービスコード内に存在しないことを検証。エラー時は例外を即座にUI/ログへ伝播させること。
3. **コンテナセキュリティと非特権実行**:
   - rootユーザーによるコンテナ実行を禁止し、非特権ユーザー（`appuser` 等）で実行されているか。
   - 不要なポートが外部開放されていないか。
4. **起動時 Alembic マイグレーション保証**:
   - コンテナ起動スクリプト（`entrypoint.sh` 等）で `alembic upgrade head` が本番起動前に確実に実行され、マイグレーション失敗時にプロセスが安全に異常終了するようになっているか。
5. **ヘルスチェック・内部監視エンドポイントの存在**:
   - オーケストレータ/ロードバランサ用の `/internal/health` および `/internal/litestream`（Profile A適用時）エンドポイントが実装され、監視対象に含まれているか。
6. **ロールバック手順の完全性**:
   - `本番適用作業手順書.md` に、デプロイ失敗時、DBマイグレーション失敗時、およびLitestream復元時の具体的かつ実行可能なロールバック手順が記載されているか。
7. **DBマイグレーションの破壊防止**:
   - 不可逆なテーブルドロップやデータ喪失リスクがないか。

### 第2層: システム展開プロファイル別適合監査
- **Profile A (サーバーレス極小コストWeb型 / ゴールデンパス)**:
  - IAP認証有効時、JWT署名検証（Google公開鍵による署名検証、aud/iss検証）が有効化されているか。
  - Litestreamレプリケーション設定（バケット名、パス、同期監視 `/api/internal/litestream/status`）が正しく稼働しているか。
  - Cloud Run 最大インスタンス数1（`max-instances=1`）が保証され、単一ライター保護が保たれているか。
  - SQLite WALモードおよびバッチマイグレーション（`render_as_batch=True`）の稼働保証。
- **Profile B (Web SSR / フルマネージドRDB型)**:
  - Cloud SQL / PostgreSQL への接続プールおよびSSL暗号化接続設定。
  - Alembicマイグレーションの複数インスタンス競合防止（起動時排他ロックまたはCI/CDパイプライン事前実行）。
  - 水平オートスケール環境下でのセッション/キャッシュ外部化（Redis/Memorystore）。
- **Profile C (静的MPA / 超軽量ツール型)**:
  - 単一プロセス完結性および最小リソース設定の妥当性。
  - 単一バイナリまたは静的配信設定における権限・ポート設定。
- **Profile D (PCローカルデスクトップアプリ型)**:
  - デスクトップ用ストレージアダプター（SQLite/LocalStore）のローカルパス権限および暗号化設定。
  - OSネイティブAPI連携・配布パッケージ署名設定。

---

## 3. レビュー結果の作成と判定

監査結果を `docs/plans/システム総合レビュー結果報告書.md` に出力します。

### 合否判定基準:
- **`RELEASE APPROVED`**: ゼロ・トレランス項目全クリア、かつ高リスク指摘0件。本番デプロイへ進む。
- **`RELEASE BLOCKED`**: ゼロ・トレランス項目の違反、または重大なセキュリティ/稼働停止リスクが存在。デプロイを阻止し原因究明。

---

## 4. 標準完了サマリの返却

コンダクターへ以下の形式でサマリを返送してください。

```markdown
## 作業完了サマリ
- **担当エージェント**: qa-engineer
- **実施フェーズ / タスク**: PHASE 7 システム総合レビュー (`dev-review-system`)
- **判定結果**: RELEASE APPROVED / RELEASE BLOCKED
- **生成ファイル**: docs/plans/システム総合レビュー結果報告書.md
- **セキュリティ・稼働検証結果**:
  - 平文シークレット排除: PASS / FAIL
  - 本番モック排除二重防御 (VITE_ENABLE_MOCK=false): PASS / FAIL
  - 非rootコンテナ実行: PASS / FAIL
  - entrypoint起動時Alembic保証: PASS / FAIL
  - ヘルスチェック・内部監視設定 (/internal/health, /internal/litestream): PASS / FAIL
  - IAP JWT署名検証設定: PASS / FAIL / N/A
  - ロールバック手順完全性: PASS / FAIL
- **主な指摘事項**:
  - [指摘内容と修正必須要件（あれば）]
- **💡 獲得した知見・落とし穴 (Lessons Learned)**:
  - **事象**: [本番構成上の落とし穴やリスク]
  - **対策**: [推奨ルール]
  - **仕分け推奨**: Tier 1 / Tier 2
- **次のアクション**: [APPROVEDなら本番デプロイ実施、BLOCKEDなら是正作業]
```
