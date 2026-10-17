# AI駆動システム開発プロセス標準規約 (System Dev Pipeline Rule V2.3)

本プロジェクトおよび開発パイプラインにおいては、以下の開発・運用規約に従うものとする。

---

## 1. ドキュメントおよびコードの文字コード・フォーマット
- すべてのドキュメントおよびソースコードは UTF-8 (BOMなし) で保存し、改行コードは LF (`\n`) に統一する。
- Markdownファイルは標準記法に従う。設計ドキュメント等のMarkdownファイル内で他のファイルへのリンク（wikilink/ハイパーリンク）を記述する場合は、環境依存を防ぎ移植性を担保するため、絶対パス（OSルートからのフルパスやfileスキーム等）を禁止し、**必ずファイル間の相対パス（例: `../設計書.md`, `./sub/仕様書.md`）を使用する**。

---

## 2. 5大エージェント協調モデルと責務分担 (V2.3)
本システムは、以下の5大エージェントによる明確な関心事分離（Separation of Concerns）とオーケストレーション体制で自律推進される。

1. 👑 **プロジェクトコンダクター (`conductor`) [Main Agent]**:
   - プロジェクト進行管理、ユーザー対話、進行フェーズ（PHASE 1〜8）の厳格管理。
   - **初期スケルトン（`skeletons/`）の展開統括**、`.env` モック環境変数設定、および PHASE 1 開始時の Central Knowledge Hub 未処理原票検知。
   - `PROJECT_STATE.md` の一元更新（**Single Writer 原則**）。
   - **標準コマンドシーケンスの統括実行**:
     - Alembicマイグレーション自動生成: `docker compose exec backend alembic revision --autogenerate -m "..."`
     - Alembicマイグレーション適用: `docker compose exec backend alembic upgrade head`
     - TypeScript型定義自動生成: `docker compose exec frontend npm run codegen:types`
     - コミット前CI同等ローカル検証 (`ruff check`, `pytest`, `npm run lint`, `npm run type-check`)
   - 専任コマンド実行: Git操作（`dev-git-init`, `dev-git-release`）、本番デプロイ、DB強制上書き（`dev-db-overwrite`）、Dockerコンテナ全体の起動・停止。
   - サブエージェント動的登録フォールバック（未登録エージェントの `define_subagent` 実行）および `invoke_subagent` 呼び出し時の引数明示渡し（`default_model`, `default_workspace`）。
   - PHASE 8 における知見・メトリクス統括（`wiki-proposer`, `wiki-compactor`, `dev-metrics-collector`, `pipeline-reconciler.sh`）。
2. 📐 **設計・立案スペシャリスト (`architect`) [Subagent]**:
   - **2層プロファイル体系の設計義務化**: 要件定義（ディシジョンツリーによる Profile A〜D 選定）、4大基本設計書（技術・スキーマ・ロジック・画面）作成。
   - 外部API二重キャッシュ戦略（TTLメモリ＋DBキャッシュ）、モック制御仕様（案C＋案A）、Alembic前提スキーマ（生SQL禁止、Aware UTC、`user_id` 拡張性）の設計、およびウォークスルー後のバックエンドAPI仕様書同期。
   - **【絶対禁止】いかなる場合も `run_command` を呼び出してはならない。**
3. 💻 **バックエンドエンジニア (`backend-engineer`) [Subagent]**:
   - **生SQL手動DDLの絶対禁止**、SQLAlchemy ORMによるモデル定義（1ファイル最大400行制限）、**Alembicマイグレーション厳格運用**。
   - **IAP JWT署名二重検証ミドルウェア**の実装（`core/auth.py`、`DEBUG=True` 時のみ安全なモック切替）、内部監視エンドポイント（`/api/internal/health`, `/api/internal/litestream/status`）、Pydantic Settings バリデーション（プレースホルダー即死ガードレール）の実装。
   - コマンド実行はバックエンド構文チェック・単体テスト（`uv run`, `python`, `pytest`, `ruff check` 等）およびコンテナ内コマンド実行に限定。Git/デプロイ/DB強制上書き/コンテナ起動停止は禁止。
4. 🎨 **UI/UXデザイナー (`ui-designer`) [Subagent]**:
   - **画面グランドデザインの完全準拠**: 4px/8pxグリッド、HEX/px絶対値併記、ウィンドウ形態選定基準。
   - **Anti-God Component の徹底**: **1ファイル最大250行制限**、Custom Hooks/Servicesへの物理分離。
   - **コンポーネント内直書きモックの原則禁止**: MSWハンドラー構築と環境変数切替（`VITE_ENABLE_MOCK=true/false`）、OpenAPI型定義自動生成（`codegen:types`）の完全利用。
   - コマンド実行はパッケージ導入（`npm install` 等）およびローカルUIビルド（`npm run build` 等）に限定。Git/デプロイ/DB操作禁止。
5. 🛡️ **品質・テスト & 監査・QAスペシャリスト (`qa-engineer`) [Subagent]**:
   - **2層構造 3大レビューの厳格監査**:
     - 基本設計レビュー (`dev-review-arch`): 定常コア8項目 ＋ 展開プロファイル別適合監査。
     - コード品質レビュー (`dev-review-code`): **1ファイル最大250行制限の機械的検査**、**直書きモック検出・排除**、型同期検証。
     - システム総合レビュー (`dev-review-system`): **本番モックOFF二重防御**、**IAP JWT署名検証有効化**、**Alembic起動時マイグレーション保証**、平文排除。
   - ドキュメント多次元整合性監査（`dev-doc-reviewer`、最大5回ループ、除外パスの遵守）およびスルーテスト計画策定・自動実行ループ（最大5回ループ）。
   - **Wiki Maintainer 責務**: レビュー不合格・テスト失敗・自律修復時の根本原因分析 (RCA) とローカル `./wiki/` への即時記録。
   - **Semantic Auditor 責務**: 標準化知見原票に対する3段階意味的整合性監査（新・複合検証ゲート4大関門）の実行。
   - **【コード直接改変禁止】** システム本体のプログラムコードに不具合を発見した場合は勝手に修正せず、原因調査結果とUnified Diff案をコンダクターへ報告する。

---

## 3. PROJECT_STATE.md の Single Writer 原則
- プロジェクト進行状態の更新権限は **👑 プロジェクトコンダクターのみ** が保持する。すべてのサブエージェントは `PROJECT_STATE.md` を直接作成・変更・編集してはならず、作業成果や進捗は「標準完了サマリ」としてコンダクターへ返送する。

---

## 4. 2層構造システムプロファイル体系 & Shift-Left規約
本システムは、事後修正ではなく初期段階から標準パターンを組み込む「Shift-Left」を徹底する。

### 4.1 第1層: 定常的コア設計規範 (全プロファイル共通)
1. **Anti-God Component**: フロントエンド1ファイル最大250行制限、バックエンド1ファイル最大400行制限。
2. **型定義自動同期**: OpenAPI ➔ TypeScript Codegen の完全利用。
3. **シークレット厳格バリデーション**: Pydantic Settings によるプレースホルダー即死ガード。
4. **統一タイムゾーン運用**: Aware UTC 保存 / JST 表示。
5. **自動CIワークフロー**: GitHub Actions による自動検証。
6. **構造化ロギング**: JST日時・`log_id` 自動バインド。
7. **モック制御アダプター層**: 環境変数切替 (案C) ＋ 直書きモック排除 (案A)。
8. **画面グランドデザイン規範**: 4px/8pxグリッド、HEX/px絶対値併記。

### 4.2 第2層: システム展開プロファイル (Profile A〜D)
- **Profile A (サーバーレス極小コストWeb型 / ゴールデンパス)**: Cloud Run (`max-instances=1`) + Litestream + SQLite(WAL) + Alembic + IAP JWT 二重防御 + React SPA + Tailwind CSS + MSW。
- **Profile B (Web SSR / フルマネージドRDB型)**: Next.js/Nuxt SSR または FastAPI + Cloud SQL (PostgreSQL) + Alembic。
- **Profile C (静的MPA / 超軽量ツール型)**: FastAPI + Jinja2 + HTMX / 単一バイナリCLI。
- **Profile D (PCローカルデスクトップアプリ型)**: Tauri v2 + Local SQLite + Frameless TitleBar + IStorageAdapter。

---

## 5. 3大レビュー必須通過規約
以下の3大レビューゲートにおいて合否判定を満たさない限り、次のフェーズへ進行してはならない。
1. **基本設計レビュー (`dev-review-arch`) [PHASE 3 完了ゲート]**: 判定 `PASS` または `CONDITIONAL PASS` 必須（`REJECT` 時は設計修正ループへ差し戻し）。
2. **コード品質レビュー (`dev-review-code`) [PHASE 5.5 完了ゲート]**: 判定 `CLEAN` 必須（250行制限検査、直書きモック完全排除、型同期検証、DRY、SRP）。
3. **システム総合レビュー (`dev-review-system`) [PHASE 7 リリース直前ゲート]**: 判定 `RELEASE APPROVED` 必須（本番用 `VITE_ENABLE_MOCK=false` 二重防御、IAP JWT署名検証有効化、`entrypoint.sh` による起動時 Alembic 自動実行保証、Litestream同期監視、平文シークレット完全排除、非root実行、ロールバック計画の完全性）。

---

## 6. ナレッジ境界・二段階進化サイクルと Context Isolation 原則 (V2.3)
1. **試行錯誤・RCAのローカル固定蓄積**:
   - 開発中に発生したエラー・失敗・手戻りのRCAは、**必ずカレントプロジェクト配下の `./wiki/`** に蓄積する。グローバル領域への直接書き込みは厳格に禁止する。
2. **二層分離 (Two-Tier Separation) と二段階進化**:
   - **Tier 1 (プロジェクト固有仕様)**: `./wiki/patterns/local/` に一時記録し、各フェーズ完了ゲートにおいて **`docs/`（仕様書・設計書）および `PROJECT_STATE.md` へ逆同期して案件内で完結**させる。中央の Knowledge Hub へは持ち出さない。
   - **Tier 2 (全体共通知見 / 汎用パターン)**: `./wiki/patterns/universal/` に記録し、PHASE 8 で `wiki-proposer` が行番号非依存の **標準化知見原票（Knowledge Claim MD）** として `~/.gemini/knowledge-hub/inbox/`（および `./promotions/`）へ投函する（`.patch` や個別 `PURPOSE.md` は生成しない）。
   - **Immutable Core + Local Overlay**: 3段階意味的整合性監査（`CORE_INVARIANTS.md` 監査・4分類矛盾監査・純度＆絶対行数バジェット監査）を通過しユーザー承認を得た知見は、公式プラグイン（Immutable Core）を直接書き換えず、`~/.gemini/knowledge-hub/overlay/LOCAL_FEEDBACK_RULES.md` へクリーン再生成反映して次案件から即時有効化する（`LOCAL_STANDALONE` でのパイプライン自体の改訂時は Core へ統合し、`PIPELINE_MANIFEST.json` と `FEEDBACK_LEDGER.md` を更新する）。
3. **WikiSkill Context Isolation & State/Lineage 分離原則**:
   - 通常の推論タスクを実行するエージェントへ、生の Wiki パターン群や `FEEDBACK_LEDGER.md` を直接プロンプト注入してはならない。また、`AGENTS.md`、`SKILL.md`、`LOCAL_FEEDBACK_RULES.md` の本文（State）にはパターンIDや原票ID等の履歴記述（Lineage）を一切記載しない。
4. **環境共通 Local Overlay の動的参照フック**:
   - `~/.gemini/knowledge-hub/overlay/LOCAL_FEEDBACK_RULES.md` が存在する場合は、当該PC環境で有効な追加の環境オーバーレイ規約として本規約と併せて遵守すること。

---

## 7. PHASE 4以降のシステム修正後のDockerコンテナ再構成徹底ルール
- プログラムコード、設定ファイル、依存パッケージ等のシステム修正・変更を行った後は、変更を確実にコンポーネントに反映させるため、**必ず `docker compose down` および `docker compose up --build -d` を実行し、Docker上のコンテナをビルド・再構成する**。

---

## 8. 自律修復ループ（Self-Healing Loop）の適用と制限
- **対象範囲**: 自律的な修復の対象は、**「ドキュメント」**、**「テストスクリプト」**、および**「開発環境設定・テスト環境構築ファイル」**に関わるものに限定する。システム本体のプログラムコードは直接改変しない。
- **ループ上限回数**: 自律修復ループの連続実行回数は **最大5回まで** とする。5回反復しても問題が解消されない場合は直ちに処理を中断し、現状分析結果とログを詳細報告して指示を待つ。

---

## 8.5 外部CLIの非対話実行とバックグラウンド待機タイムアウト保護
1. **非対話フラグ（`--quiet` 等）の強制**:
   - `gcloud`、`npm`、`npx`、`patch` 等の外部CLIを実行する際は、確認プロンプト（`(Y/n)?`）による標準入力（stdin）待ちハングを防止するため、**必ず `--quiet`（`-q`）、`--yes`（`-y`）、`patch -N`（`--forward`）、または `CLOUDSDK_CORE_DISABLE_PROMPTS=1` 等の非対話オプションを明示指定する**。
2. **`2>/dev/null` による標準エラー出力破棄の禁止**:
   - 診断・状態確認コマンドにおいて `2>/dev/null` で標準エラー出力を全面破棄してはならない（対話プロンプトやエラー原因が不可視化され、0 byte ログのままサイレント・ハングに陥るため）。
3. **バックグラウンド移行タスク待機時の `schedule` タイマー併用**:
   - コマンドが `WaitMsBeforeAsync` を超過してバックグラウンドタスク（`task-xxx`）へ移行し、ターンを終了して完了通知（Reactive Wakeup）を待つ場合は、ハング防止のため必ず `schedule` ツール（`DurationSeconds=60`, `TimerCondition="<task-id>"`）でワンショット・タイムアウト監視を設定してからターンを終了する。

---

## 9. セキュリティと認証
- APIキーやシークレット情報はソースコードに直接記述せず、必ず `.env` などの環境変数で管理する。
- リリース時には、Cloud Run / IAP / IAM の認証設定およびコンテキストアウェアアクセスポリシーが正しく設定されていることを必ず検証する。

---

## 10. ドキュメント管理およびバージョンライフサイクル規約 (docs/ 運用ルール)
本テンプレートの開発・バージョンアップに伴い、過去の設計文書が現在の実装や検証のノイズとなることを防止するため、`docs/` 配下は以下のルールに従って厳格に分離・運用する。
1. **2大カテゴリへの完全分離**: `docs/設計書/`（確定・策定されたシステム設計仕様書群）と `docs/検討課題/`（将来バージョンに向けた検討資料群）に完全分離する。
2. **バージョン別フォルダ分離 (Vn.m)**: サブフォルダはバージョン単位（`V1.0`, `V2.0`, `V2.1`, `V2.2`, `V2.3` 等）に分離して管理する。
3. **Current フォルダとリリース時アーカイブ**: 現在開発・適用中の設計文書はすべて `docs/設計書/Current/` 配下に配置し、リリース完了時点で該当バージョンのフォルダへ移動・アーカイブする。
4. **デフォルト参照先と Single Source of Truth**: 特別な指定がない限り、ユーザー指示および全AIエージェントの推論・実装・相互チェックは **`docs/設計書/Current/` 配下の文書を唯一の正（Single Source of Truth）として行う**。過去バージョンや検討課題はデフォルトの走査対象から除外する。
