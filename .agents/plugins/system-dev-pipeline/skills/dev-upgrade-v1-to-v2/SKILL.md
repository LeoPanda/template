---
name: dev-upgrade-v1-to-v2
description: "V1.0で開発・本番リリースされたプロジェクトをV2.1開発パイプライン（WikiSkill永続ナレッジ、3大レビューゲート、状態管理機構）へ非破壊アップグレード・環境整備するスキル（コンダクター主担当・QA監査協調）。"
---

# V1.0プロジェクトアップグレード指示書 (Upgrade V1.0 to V2.1 Pipeline)

- **主担当エージェント**: 👑 プロジェクトコンダクター (`conductor`)
- **協調・監査エージェント**: 🛡️ QAエンジニア (`qa-engineer`)

本スキルは、V1.0テンプレート（グローバルプラグイン運用前提）を用いて本番リリースを完了したプロジェクトに対し、既存のコードやドキュメント資産を損なうことなく、V2.1の**「ナレッジフィードバックシステム（WikiSkill）」**、**「3大レビューシステム」**、および**「状態管理機構（`PROJECT_STATE.md`）」**を導入し、次期システム改訂プロセス（REVISION LIFECYCLE）へのスムーズな合流を可能にする環境整備を自律実行します。

---

## 0. 基本原則と安全ガードレール

1. **非破壊原則 (Non-Destructive Principle)**:
   - 既存のソースコード、Docker構成、`.env`、既存の `docs/` 配下の仕様書本文は**絶対に上書き・削除・改変しない**。
   - 本スキルの処理対象は「受皿ディレクトリの新設」「状態管理票の自動生成」「規約ファイルの最新配置」「`.gitignore` への追記」に厳格に限定する。
2. **グローバルプラグイン運用の純度維持**:
   - プロジェクト直下に `.agents/` ディレクトリを複製・作成しない。
   - `EXECUTION_MODE` は常に `GLOBAL_PLUGIN`、テンプレートソースは `~/.gemini/config/plugins/system-dev-pipeline` を正とする。
3. **Single Writer 原則**:
   - `PROJECT_STATE.md` の作成および更新は、👑 プロジェクトコンダクター専任で実行する。

---

## 1. Phase 0: 事前調査 & 健全性診断 (Inspection & Health Check)

👑 コンダクターは、環境整備を開始する前にプロジェクトの現況を調査・診断します。

### (1) Gitワーキングツリーの検証
1. `git status --porcelain` を実行し、未コミットの変更が存在しないことを確認してください。
   - **未コミット変更がある場合**: 処理を中断し、「作業中の変更があります。コミットまたは `git stash` してから再実行してください」とユーザーに警告して停止してください。
2. 現在のブランチ（通常 `main` または `master`）および直近のタグ（例: `v1.0.0`）を取得・記録してください。

### (2) 既存資産のスキャン
1. `docs/` 配下の仕様書を走査し、以下が存在することを確認します：
   - `docs/要件定義書.md`
   - `docs/技術要件定義書.md`
   - `docs/テーブルスキーマ定義書.md`（存在する場合）
   - `docs/ビジネスロジック仕様書.md`（存在する場合）
   - `docs/画面仕様書.md`（存在する場合）
2. `.env` を読み込み、`APP_VERSION` を抽出します（未定義の場合は最新Gitタグまたは `1.0.0` を採用）。
3. プロジェクト直下に `./.agents/plugins/` が存在しないことを確認し、動作モードを `GLOBAL_PLUGIN` と確定します。

---

## 2. Phase 1: 受皿環境の非破壊展開 (Scaffolding)

プロジェクトルート直下に、V2.1パイプラインが要求する受皿ディレクトリおよび初期台帳ファイルを展開します。

### (1) 受皿ディレクトリの自動生成
以下のディレクトリが存在しない場合、作成してください (`mkdir -p`)：
- `./docs/plans/`
- `./docs/plans/scenario-test/`
- `./docs/plans/metrics/`
- `./wiki/patterns/local/` (Tier 1: プロジェクト固有仕様パターン)
- `./wiki/patterns/universal/` (Tier 2: テンプレート共通知見パターン)
- `./wiki/patterns/rejected/` (検証不合格・ロールバック知見)
- `./wiki/archive/` (Compactorによる陳腐化パターン退避先)
- `./metrics/turns/` (ターン別メトリクス一次受皿)
- `./metrics/phases/` (フェーズ別メトリクス集計受皿)
- `./rules/` (プロジェクト適用規約領域)

### (2) `.gitignore` への除外登録
プロジェクトルートの `.gitignore` を確認し、以下の行が含まれていない場合は末尾に追記してください：
```gitignore
# Antigravity Metrics Raw Turns
metrics/turns/
```

### (3) Wiki台帳・昇格バッファの初期配置
テンプレート参照先（グローバル: `~/.gemini/config/plugins/system-dev-pipeline/templates/`、またはローカル）から取得して初期配置します：
- `./wiki/logs.md`（未存在時）:
  ```markdown
  # Wiki Pattern & Revision Logs

  | 日時 | パターンID | 分類 | 契機 | 概要 | 状態 |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  ```
- `./wiki/skill-impact.md`（未存在時）:
  ```markdown
  # Skill & Knowledge Impact Map

  | パターンID | 影響スキル / ファイル | 改善種別 | 効果測定 / メトリクス寄与 |
  | :--- | :--- | :--- | :--- |
  ```
- `./TEMPLATE_PROMOTIONS.md`（未存在時）:
  テンプレート `TEMPLATE_PROMOTIONS.md.template` を元に初期配置。

### (4) 開発運用ルールの最新化
最新の規約ファイルを `./rules/` 配下に展開します（既存の独自ルールがある場合はバックアップまたは共存）：
- `./rules/dev-process-standards.md`: プラグイン側の最新規約を配置。
- `./rules/システム改訂ルール.md`: テンプレート側の改訂ルールを配置。

---

## 3. Phase 2: 状態管理票のリバースエンジニアリング (State Reconstruction)

V1.0プロジェクトには `PROJECT_STATE.md` が存在しないため、既存ドキュメントから情報を読み取り、V2.1標準の `./PROJECT_STATE.md` を高精度に復元・生成します。

### (1) システム展開プロファイル（Profile A〜D）の自動推定
`docs/要件定義書.md` および `docs/技術要件定義書.md` の記述を解析し、以下の基準でプロファイルを判定します：
* **Profile A: クラウド公開 (Cloud-Native Web Service)**: Cloud Run, GCP, AWS, Docker公開, 不特定多数アクセス等
* **Profile B: ローカル常駐 (Local Daemon / Agent)**: バックグラウンド常駐, SQLite, OSローカル連携等
* **Profile C: 個人・小規模 (Solo Tool / CLI)**: CLIツール, 開発補助スクリプト, 単一ユーザー向け等
* **Profile D: モバイル・クライアント (Mobile / Client App)**: モバイルアプリ, PWA, クライアント完結等

※ 判定に迷う場合は、要件定義書のインフラ記述に基づき最も安全・標準的なプロファイル（例: Cloud Run環境ならProfile A）を選択してください。

### (2) `PROJECT_STATE.md` の生成
グローバルプラグインの `templates/PROJECT_STATE.md.template` を元に、以下の通りパラメータを埋め込んでプロジェクトルート直下に生成します：
* **プロジェクト名**: プロジェクトフォルダ名
* **現在のステータス**: `PRODUCTION_ACTIVE` (本番稼働中 / 改訂待機中)
* **システム展開プロファイル**: 推定されたプロファイル
* **現行バージョン**: 取得したバージョン（例: `v1.0.0`）
* **EXECUTION_MODE**: `GLOBAL_PLUGIN`
* **TEMPLATE_SOURCE**: `~/.gemini/config/plugins/system-dev-pipeline`
* **現在の作業ブランチ**: 現在のブランチ名（`main` 等）
* **新規開発フェーズ（PHASE 1〜8）進捗**: **全フェーズを完了（`[x]`）**としてチェック。
* **システム改訂管理**:
  - 現在の改訂ステータス: `IDLE`
  - 進行中の改訂依頼番号: なし
  - 現行改訂ターン番号: なし
  - 知見昇格ステータス: `未昇格`
  - コード品質レビュー判定: `CLEAN`

---

## 4. Phase 3: 移行検証 & 整合性ゲート (Validation & Gating)

👑 コンダクターは、🛡️ QAエンジニア（`qa-engineer`）に適合性監査を委譲します（サブエージェントが使用できない環境ではコンダクターが自ら実行）。

### (1) 監査内容
1. **ドキュメント相互整合性チェック**:
   - `dev-doc-reviewer` を実行し、既存 `docs/` 配下の仕様書間のリンクに絶対パス（`file:///` 等）が混入していないか、ファイル参照が壊れていないかを確認。
2. **受皿ディレクトリ充足性の検証**:
   - `wiki/patterns/{local,universal,rejected}` が存在すること。
   - `metrics/turns/` が存在し、`.gitignore` に登録されていること。
   - `PROJECT_STATE.md` のフォーマットがV2.1準拠であること。

### (2) 移行診断レポートの作成
`docs/plans/v1_to_v2_upgrade_report.md` を作成し、以下の項目を記録します：
- 移行実施日時
- 対象プロジェクト名および現行バージョン
- 判定されたシステム展開プロファイル
- 展開されたディレクトリ・受皿ファイル一覧
- 検出された警告・留意事項（0件であることを確認）
- 総合判定: `UPGRADE SUCCESSFUL`

---

## 5. Phase 4: 移行コミット & 改訂スタンバイ (Finalization)

1. **移行コミットの作成（👑 コンダクター専任）**:
   新設された受皿ファイル群をステージングし、Gitコミットを作成します：
   ```bash
   git add docs/plans/ wiki/ metrics/ rules/ .gitignore PROJECT_STATE.md TEMPLATE_PROMOTIONS.md
   git commit -m "chore: upgrade project environment to V2.1 pipeline standard (GLOBAL_PLUGIN)"
   ```
2. **ユーザーへの完了報告**:
   - 整備完了サマリおよび診断レポートのリンクを表示。
   - 「本プロジェクトはV2.1パイプラインへのアップグレードが完了し、`PRODUCTION_ACTIVE`（改訂待機状態）になりました。次回の改訂依頼（例: `改訂依頼: 1.1.001 〇〇の修正`）から、V2.1のコード品質レビュー（PHASE 5.5）およびWikiSkillナレッジフィードバックが自律発動します」とアナウンスしてください。
