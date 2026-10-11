---
name: dev-phase4-env-build
description: "PHASE 4 開発環境・システム構築スキル。コンダクター統括のもと、バックエンド (BE) とフロントエンド (FE) を完全分離して並行委譲実装し、コンテナ構成・Git初期化を行う。"
---

# PHASE 4: 開発環境およびシステムの構築

- **統括・環境・Git専任**: 👑 プロジェクトコンダクター (`conductor`) (Model: `pro`)
- **バックエンド実装担当**: 💻 バックエンドエンジニア (`backend-engineer`) (Model: `pro`)
- **フロントエンド実装担当**: 🎨 UI/UXデザイナー (`ui-designer`) (Model: `flash`)
- **Git初期化**: ⚙️ `dev-git-init` (コンダクター専任)

基本設計書一式に基づき、開発環境の構築とシステムの初版実装を行ってください。

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
   - ディレクトリ構造整備、Docker構成ファイル（`Dockerfile`, `docker-compose.yml`）の策定。
   - コンテナ設定: `backend` および `frontend` サービスで `restart: "no"` を明示設定。
2. 💻 **`backend-engineer` への委譲 (`invoke_subagent`)**:
   - `docs/テーブルスキーマ定義書.md`, `docs/ビジネスロジック仕様書.md` をインプットとして渡し、APIエンドポイント、DBモデル、マイグレーション、ロジック実装を委譲。
3. 🎨 **`ui-designer` への委譲 (`invoke_subagent`)**:
   - `docs/画面仕様書.md` をインプットとして渡し、フロントエンド画面・UIコンポーネント実装を委譲（コンポーネント行数300行以下厳守）。

### 3. Dockerコンテナの生成と起動確認
- **事前チェック**: Docker デーモンが正常稼働していることを確認（`docker info`）。
- **コンテナ生成・起動**:
  ```bash
  docker compose up -d --build
  ```
- **起動状態確認**:
  `docker compose ps` または `docker compose logs` でエラーなく正常稼働していることを検証。
- **【重要】修正時のDockerコンテナ再構成徹底ルール**:
  PHASE 4以降、プログラムコードや設定ファイル等の修正を行った場合は、変更を確実に反映するため、**必ず `docker compose down` を実行した後に `docker compose up --build -d` を実行し、コンテナをビルド・再構成する**こと。

### 4. Git 管理設定 (`dev-git-init` の発動)
- プラグインの `templates/Git運用基準書.md` を `docs/Git運用基準書.md` へ配置。
- コンダクター専任で `dev-git-init` スキルを実行し、Git初期化（`main` ブランチ）、GitHub SSHリモート設定、初期コミット作成、および `feature` ブランチへの切り替えを行う。

### 5. 状態更新と報告
- サブエージェントからの完了サマリを集約し、`PROJECT_STATE.md` の PHASE 4 を完了に更新してユーザーへ報告。
