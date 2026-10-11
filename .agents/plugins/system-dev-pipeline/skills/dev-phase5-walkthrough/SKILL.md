---
name: dev-phase5-walkthrough
description: "PHASE 5 ウォークスルー検証、コードを正としたAPI仕様書同期、およびPHASE 5.5 コード品質レビュー (dev-review-code) ゲートへ接続するスキル。"
---

# PHASE 5: ウォークスルー検証・ドキュメント同期とコードレビュー連携

- **対話・修正統括**: 👑 プロジェクトコンダクター (`conductor`) (Model: `pro`)
- **API仕様書同期**: 📐 設計・立案スペシャリスト (`architect`) (Model: `pro`)
- **BE修正担当**: 💻 バックエンドエンジニア (`backend-engineer`) (Model: `pro`)
- **UI修正担当**: 🎨 UI/UXデザイナー (`ui-designer`) (Model: `flash`)
- **コード品質監査**: 🛡️ 品質・テスト & 監査・QAスペシャリスト (`qa-engineer`) (Model: `pro`)
- **承認ゲート**: 👤 ユーザーによる明示的承認必須

ウォークスルー（動作確認）完了後のソースコードを正としてドキュメントを同期し、PHASE 5.5 コード品質レビューゲートへ接続してください。

---

## 作業手順

### 1. ユーザーによる画面操作ウォークスルー
- ユーザーが画面操作や疎通検証を行い、不具合や要望を提示します。
- コンダクターが修正をオーケストレーションします：
  - バックエンド起因の不具合: 💻 `backend-engineer` へ委譲。
  - 画面・CSS・UI挙動の不具合: 🎨 `ui-designer` へ委譲。
- **修正後のコンテナ再構成徹底ルール**:
  コード修正後は必ず `docker compose down` および `docker compose up --build -d` を実行して反映してください。

### 2. ソースコードを正としたバックエンドAPI仕様書の作成・同期（📐 architect 連携）
- ウォークスルー修正後のソースコードを正とし、📐 `architect` に委譲して `docs/バックエンドAPI仕様書.md` を作成・最新同期します。

### 3. ドキュメント相互整合性チェック (`dev-doc-reviewer` / 🛡️ qa-engineer)
- 🛡️ `qa-engineer` に `dev-doc-reviewer` を実行させ、`docs/` 配下の仕様書間矛盾を自律修復（最大5回ループ）します。

### 4. PHASE 5.5: コード品質・整合性レビュー (`dev-review-code`) ゲートへの接続
- ドキュメント同期完了後、🛡️ `qa-engineer` に `dev-review-code` を委譲します。
- 全ソースコードの DRY原則、ファイル行数制限（全体400行、UI300行）、型安全性を監査し、`docs/plans/コード品質レビュー及びリファクタリング提案書.md` を作成。
- **判定結果に応じたフロー**:
  - `CLEAN`: 次フェーズ（PHASE 6 スルーテスト）へ進行。
  - `REFACTOR RECOMMENDED` / `BLOCKED`: コンダクターが指摘内容（Unified Diff）を確認し、BE/UIサブエージェントへ修正を委譲して是正。

### 5. 状態更新と承認ゲート提示
- `PROJECT_STATE.md` を更新し、ウォークスルーおよびコードレビュー完了の明示的承認をユーザーに要請してください。
