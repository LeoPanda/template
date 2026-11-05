---
name: dev-phase5-walkthrough
description: "PHASE 5 ウォークスルー検証、モック透過切替検証 (VITE_ENABLE_MOCK=true/false)、コードを正としたAPI仕様書同期、およびPHASE 5.5 コード品質レビュー (dev-review-code) ゲートへ接続するスキル。"
---

# PHASE 5: ウォークスルー検証・モック切替検証とドキュメント同期

- **対話・修正・モック切替統括**: 👑 プロジェクトコンダクター (`conductor`) (Model: `pro`)
- **API仕様書同期**: 📐 設計・立案スペシャリスト (`architect`) (Model: `pro`)
- **BE修正担当**: 💻 バックエンドエンジニア (`backend-engineer`) (Model: `pro`)
- **UI修正担当**: 🎨 UI/UXデザイナー (`ui-designer`) (Model: `flash` / `pro`)
- **コード品質監査**: 🛡️ 品質・テスト & 監査・QAスペシャリスト (`qa-engineer`) (Model: `pro`)
- **承認ゲート**: 👤 ユーザーによる明示的承認必須

ウォークスルー（動作確認）およびモック透過切替検証を実施し、ソースコードを正としてドキュメントを同期し、PHASE 5.5 コード品質レビューゲートへ接続してください。

---

## 作業手順

### 0. 自動ブラウザ感覚センサー検証 (Chrome DevTools MCP / Visual & DOM Sensor)
ユーザー提示前に、AIエージェント自身が実ブラウザ描画状態を計測・自己検証します：
1. **コンソール & ネットワーク検査**: `navigate_page` ➔ `list_console_messages` で `console.error`、未捕捉例外、React Hydration Error が **0件** であることを確認。
2. **デイライト/ダーク実測コントラスト比 (HG-006)**: `evaluate_script` で文字色と背景色を実測し、WCAG AA (4.5:1 以上) を満たすことを確認。
3. **A11y & DOM 健全性**: `take_snapshot` で全ボタンのアクセシブル名解決とレイアウト崩れ・要素重なりがないことを確認。
※UIなし（Profile E等）はスキップ。MCP未接続時は Playwright ヘッドレス検査へ自動フォールバック。
※**Profile D (Tauri) 二段階ハイブリッド規約**: PHASE 4〜5 はブラウザモード（`npm run dev` ＋ MSW）で本ブラウザセンサー検証を完遂し、PHASE 6 で実機ネイティブ（`cargo tauri dev`）へ切り替えること。

### 1. ユーザーによる画面操作ウォークスルー & 不具合修正
- ユーザーが画面操作や機能検証を行い、不具合や要望を提示します。
- コンダクターが修正をオーケストレーションします：
  - バックエンド起因の不具合: 💻 `backend-engineer` へ委譲。
  - 画面・CSS・UI挙動の不具合: 🎨 `ui-designer` へ委譲。
- **修正後のコンテナ再構成徹底ルール**:
  コード修正後は必ず `docker compose down` および `docker compose up --build -d` を実行して反映してください。

### 2. モック透過切替検証 (Mock Interception Verification & Fail-Fast 監査)
開発用モックと実API結合の整合性を担保するため、以下の透過切替検証をコンダクター統括のもと実施します：
1. **モックモード動作確認 (`VITE_ENABLE_MOCK=true`)**:
   - MSW (Mock Service Worker) による擬似レスポンスが正常に返却され、UIが破綻なく描画されることを確認。
2. **実API結合モード動作確認 (`VITE_ENABLE_MOCK=false`)**:
   - `.env` で `VITE_ENABLE_MOCK=false` に変更後、コンテナを再起動（またはフロントエンドHMR反映）。
   - 実FastAPIバックエンドおよび SQLite データベースと直接疎通し、実データによる登録・取得・更新が正常動作することを確認。
   - **サイレントモックフォールバック厳格禁止 (Fail-Fast原則)**: 実結合モードにおいて、通信エラー、API未検出、IPC例外が発生した際に絶対にモックデータへフォールバックしてはならず、例外を即座にスローしてUIやログに明確にエラーが顕在化することを確認。
3. **モード間整合性確認**:
   - モックと実API間でリクエスト/レスポンススキーマの乖離やタイポがないことを検証。

### 3. ソースコードを正としたバックエンドAPI仕様書の作成・同期（📐 architect 連携）
- ウォークスルー修正後のソースコードを正とし、📐 `architect` に委譲して `docs/設計書/Current/バックエンドAPI仕様書.md` を作成・最新同期します。

### 4. ドキュメント相互整合性チェック (`dev-doc-reviewer` / 🛡️ qa-engineer)
- 🛡️ `qa-engineer` に `dev-doc-reviewer` を実行させ、`docs/` 配下の仕様書間矛盾を自律修復（最大5回ループ）します。

### 5. PHASE 5.5: コード品質・整合性レビュー (`dev-review-code`) ゲートへの接続
- ドキュメント同期完了後、🛡️ `qa-engineer` に `dev-review-code` を委譲します。
- **1ファイル最大250行制限の機械的検査**、**コンポーネント内直書きモックの機械的検出・完全排除**、機能等価性マトリクス監査（プレースホルダー/縮退実装検出で即BLOCKED）、型同期検証、DRY原則、SRPを監査し、`docs/plans/コード品質レビュー及びリファクタリング提案書.md` を作成。
- **判定結果に応じたフロー**:
  - `CLEAN`: コンダクターは `python3 scripts/state_manager.py record-review --type code --verdict CLEAN` を記録し、次フェーズ（PHASE 6 スルーテスト）へ進行。
  - `REFACTOR RECOMMENDED` / `BLOCKED`: コンダクターが指摘内容（Unified Diff）を確認し、BE/UIサブエージェントへ修正を委譲して是正。

### 6. 状態更新と承認ゲート提示
- `python3 scripts/state_manager.py complete-task --id P5-T01` 等を実行し、ウォークスルーおよびコードレビュー完了の明示的承認をユーザーに要請してください。承認後は `python3 scripts/state_manager.py record-approval --phase PHASE_5` および `set-phase PHASE_6_TESTING` を実行します。
