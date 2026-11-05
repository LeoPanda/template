# **APIキー安全管理・一元化設計書 (API_KEY_MANAGEMENT.md)**

本ドキュメントは、「<プロジェクト名>」において、Google Cloud Storage (GCS) や Litestream バックアップ、Cloud Run IAP 認証等に必要な API キーや認証資格情報（サービスアカウントキー / ADC）、内部 AI 制御トークン等を、PC（ローカル Docker 環境）および本番環境の双方から安全かつ一元的に扱うためのセキュリティ設計および実装・運用方針を定義する。

---

## **1. 基本セキュリティ方針（グランドルール）**

### **1.1. フロントエンド（クライアント側）の完全隠蔽**
React（Vite）等でビルドされたフロントエンドコード内、およびブラウザ/端末のローカル領域には、GCP サービスアカウントキーやストレージシークレット情報を一切ハードコードまたは保持してはならない。

### **1.2. バックエンド（FastAPI）プロキシ通信の徹底**
すべての外部 Cloud API（Google Cloud Storage 等）との通信は、バックエンド（FastAPI）が仲介（プロキシ）する。GCS 内の特定プレフィックスからの画像取得・降順ソート処理や参照 URL 変換もすべてバックエンド側で一括処理する。

### **1.3. ソースコード管理（Git）からの完全排除**
API キーや認証鍵が記載された `.env` などの構成ファイル、サービスアカウントの JSON 鍵ファイル、および SQLite データベースファイル (`app.db`) は、絶対に Git リポジトリにコミットしてはならない（`.gitignore` で完全除外）。

---

## **2. シークレット厳格バリデーション & Dual Provisioning 原則 ([REQ-NF05])**

### **2.1. Pydantic Settings による起動時即死ガード**
- バックエンド設定クラス（`app.core.config.Settings`）は `pydantic-settings` を用いて構築する。
- 必須環境変数が欠落している場合、または未置換プレースホルダー（`[YOUR_KEY]`, `CHANGE_ME` 等）が含まれている場合、コンテナ起動時に即座にバリデーションエラーを発生させてプロセスを停止（Fail-Fast）する。

### **2.2. Dual Provisioning 原則**
- **Git追跡用公開テンプレート (`.env.example`)**: プレースホルダー形式で必要な環境変数キーの一覧をGit追跡対象として常時維持する。
- **ローカル実行用実体 (`.env`)**: 実シークレット値を保持し、`.gitignore` で厳格に除外する。
- **自動補完・同期**: パイプライン実行時、`.env` が存在しない場合は `.env.example` から自動生成・自己修復する。

---

## **3. 環境に応じた環境変数注入仕様およびバケット命名規則**

- **開発環境 (ローカルDocker)**: `docker-compose.yml` で `backend/.env` から環境変数 (`GOOGLE_APPLICATION_CREDENTIALS`, `GCS_BUCKET_NAME_IMAGES`, `GCS_LITESTREAM_BACKUP_BUCKET`, `INTERNAL_AI_TOKEN`, `DATABASE_URL` 等) をコンテナ内へマウントして注入する。
- **本番環境 (Google Cloud / Cloud Run)**: GCP `Secret Manager` 上にシークレット（サービスアカウントキーやトークン等）やAPI認証資格情報（`CLIENT_ID`,`CLIENT_SECRET`,`REFRESH_TOKEN`等）を安全に登録し、Cloud Run のサービス起動時に動的に環境変数として単一統合コンテナにバインドする。
- **Litestream バックアップ用 GCS バケット命名規約**: 同一 GCP プロジェクト上で複数のサービスを稼働させる運用環境において、バケット名の衝突を防止するため、Litestream のバックアップ用 GCS バケット名には Docker コンテナ名を含めてユニーク化を図る（例: `<project-id>-litestream-<container-name>`）。

---

## **4. ドキュメント改定履歴**

| 改訂依頼番号 | 対象バージョン | ターン | 改定者 | 改定概要 | 完了日 |
| :--- | :--- | :---: | :--- | :--- | :--- |
| - | v1.0.0 | - | 💻 backend-engineer | 初期シークレット管理設計策定（Dual Provisioning・Pydantic Settings即死ガード準拠） | 2026-11-05 |
