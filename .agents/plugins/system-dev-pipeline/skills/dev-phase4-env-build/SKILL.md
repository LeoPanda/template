---
name: dev-phase4-env-build
description: "PHASE 4 開発環境・システム構築スキル。コンダクター統括のもと、静的スケルトンを土台にBE/FE並行委譲実装、標準コマンドシーケンス自動実行 (Alembic/Codegen/CI検証)、コンテナ構成・Git初期化を行う。"
---

# PHASE 4: 開発環境およびシステムの構築 V2.2

- **統括・環境・標準コマンド・Git専任**: 👑 プロジェクトコンダクター (`conductor`) (Model: `pro`)
- **バックエンド実装担当**: 💻 バックエンドエンジニア (`backend-engineer`) (Model: `pro`)
- **フロントエンド実装担当**: 🎨 UI/UXデザイナー (`ui-designer`) (Model: `flash` / `pro`)
- **Git初期化**: ⚙️ `dev-git-init` (コンダクター専任)

基本設計書一式に基づき、初期スケルトンを土台として開発環境の構築とシステムの初版実装を行ってください。

---

## 作業手順

### 1. 仕様の確認
以下の設計書一式を確認します：
- `docs/技術要件定義書.md`
- `docs/テーブルスキーマ定義書.md`
- `docs/ビジネスロジック仕様書.md`
- `docs/画面仕様書.md`
- `docs/AI駆動ロギングシステム仕様書.md`, `docs/APIキー安全管理・一元化設計書.md`

### 2. 環境構築とBE/FE並行委譲（コンテキスト分離）
コンダクターは直接大量のコードを書かず、以下の分担でオーケストレーションします：

1. 👑 **コンダクター (環境統括)**:
   - スケルトン（`docker/`, `backend/`, `frontend/`）の配置確認。
   - コンテナ設定: `backend` および `frontend` サービスで `restart: "no"` を明示設定。
2. 💻 **`backend-engineer` への委譲 (`invoke_subagent`)**:
   - `docs/テーブルスキーマ定義書.md`, `docs/ビジネスロジック仕様書.md` をインプットとして渡し、SQLAlchemyモデル定義、APIエンドポイント、IAP JWT署名検証ミドルウェア、内部監視エンドポイントの実装を委譲。
   - **生SQL手動DDLの絶対禁止**、Aware UTC保存、`user_id` カラム配置を徹底。
3. 🎨 **`ui-designer` への委譲 (`invoke_subagent`)**:
   - `docs/画面仕様書.md` をインプットとして渡し、フロントエンド画面・UIコンポーネント実装を委譲。
   - **Anti-God Component の徹底**: **1ファイル最大250行制限**、Hooks/Services分離。
   - **直書きモックの原則禁止**: コンポーネント内へのダミーデータ直書きを排除し、MSWハンドラー（`src/mocks/handlers.ts`）へ集約。

### 3. 標準コマンドシーケンスの自動実行 (Standard Command Sequences)
実装完了後、コンダクターは以下の標準コマンドシーケンスをコンテナ内で順次自動実行します：

```bash
# 1. コンテナのビルドと起動
docker compose up -d --build

# 2. Alembic マイグレーション自動生成
docker compose exec backend alembic revision --autogenerate -m "Initial schema from models"

# 3. Alembic マイグレーション適用
docker compose exec backend alembic upgrade head

# 4. バックエンド OpenAPI スキーマから TypeScript 型定義自動同期
docker compose exec frontend npm run codegen:types

# 5. コミット前CI同等ローカル検証ゲート
docker compose exec backend ruff check .
docker compose exec backend pytest
docker compose exec frontend npm run lint
docker compose exec frontend npm run type-check
```

- **【重要】修正時のDockerコンテナ再構成徹底ルール**:
  プログラムコードや設定ファイル等の修正を行った場合は、変更を確実に反映するため、**必ず `docker compose down` を実行した後に `docker compose up --build -d` を実行し、コンテナをビルド・再構成する**こと。

### 4. Git 管理設定 (`dev-git-init` の発動)
- プラグインの `templates/Git運用基準書.md` を `docs/Git運用基準書.md` へ配置。
- コンダクター専任で `dev-git-init` スキルを実行し、Git初期化（`main` ブランチ）、GitHub SSHリモート設定、初期コミット作成、および `feature` ブランチへの切り替えを行う。

### 5. 状態更新と報告
- サブエージェントからの完了サマリを集約し、`PROJECT_STATE.md` の PHASE 4 を完了に更新してユーザーへ報告。
