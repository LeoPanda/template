# AI駆動システム開発プロセス標準規約 (System Dev Pipeline Rule V2.6.2)

本プロジェクトおよび開発パイプラインにおいては、以下の開発・運用規約に従うものとする。

---

## 0. 規約適用スコープ境界（Scope Guard）
- **適用対象**: 本規約は、システム開発プロジェクト（`project_state.json`, `PROJECT_STATE.md`、`docs/設計書/`、または初期スケルトン `skeletons/` が配備されたプロジェクト、あるいは明示的にシステム開発フェーズ `dev-phase1`〜`8` を実行する環境）に適用される。
- **非システム開発環境（PKM Vault / 単一ナレッジベース等）における自動委譲**:
  - `PROJECT_STATE.md` や `docs/設計書/` が存在せず、プロジェクト固有の基本規約が配備されている環境では、日常の知識管理タスクにおいて当該プロジェクトのローカル規範を最優先とし、Web/DBシステム固有の制約は適用除外（スリープ）とする。

---

## 1. ドキュメントおよびコードの文字コード・フォーマット
- すべてのドキュメントおよびソースコードは UTF-8 (BOMなし) で保存し、改行コードは LF (`\n`) に統一する。
- Markdownファイルは標準記法に従う。設計書等のMarkdown内リンクは環境依存を防ぎ移植性を担保するため、絶対パスを禁止し**必ずファイル間の相対パス（例: `../設計書.md`）を使用する**。
- **Mermaid 構文安全規約**: 設計書および Markdown 内で Mermaid ダイアグラムを記述する際、矢印ラベル（`-->|"..."|`）やノード名に特殊記号（丸括弧 `()`、角括弧 `[]`、波括弧 `{}`、隅付き括弧 `【】`、スラッシュ `/`、コロン `:` 等）を含める場合は、必ずラベル全体をダブルクォーテーション（`"`）で囲まなければならない（コミット前 `harness_guard.py` で機械遮断）。

---

## 2. 5大エージェント協調モデルと責務分担 (V2.6.2)
本システムは、以下の5大エージェントによる明確な関心事分離とオーケストレーション体制で自律推進される。

1. 👑 **プロジェクトコンダクター (`conductor`) [Main Agent]**:
   - プロジェクト進行管理、ユーザー対話、進行フェーズ（PHASE 1〜8）および改訂サイクルの厳格管理。
   - `scripts/state_manager.py` による `project_state.json` 一元更新（**Single Writer 原則**）および `PROJECT_STATE.md` の決定論的自動生成。
   - 初期スケルトン展開、環境変数設定、標準コマンドシーケンス（Alembic/Codegen/CI/Hard Gate）の統括実行。
   - 専任コマンド実行: Git操作（`dev-git-init`, `dev-git-release`）、本番デプロイ、DB強制上書き、コンテナ起動停止。
   - PHASE 8 における知見・メトリクス統括（`metrics_collector.py --all --sync-state`, `pipeline-reconciler.sh`）。
   - **【コード・設計書直接編集原則禁止】**: コンダクターが `docs/設計書/`、`backend/`、`frontend/` 配下のファイルを直接編集（`edit_file`, `write_file`）することを原則禁止する。設計変更は必ず `architect`、実装は `backend-engineer` または `ui-designer` へ `invoke_subagent` 経由で委譲しなければならない。
2. 📐 **設計・立案スペシャリスト (`architect`) [Subagent]**:
   - 2層プロファイル体系の設計、要件定義書での `[REQ-Fxx]` / `[REQ-NFxx]` 採番、4大基本設計書（技術・スキーマ・ロジック・画面）作成および対応要件ID明記。
   - 外部API二重キャッシュ戦略（TTLメモリ＋DBキャッシュ）、モック制御仕様（案C＋案A）、Alembic前提スキーマの設計。
   - **【絶対禁止】いかなる場合も `run_command` を呼び出してはならない。**
3. 💻 **バックエンドエンジニア (`backend-engineer`) [Subagent]**:
   - 生SQL手動DDL絶対禁止、SQLAlchemyモデル定義（最大400行制限）、Alembicマイグレーション厳格運用。
   - **AST アーキテクチャ適応度遵守**: DTO分離（`schemas/`）、レイヤーバイパス禁止（routersからmodels直接import禁止）、例外握りつぶし禁止（`except: pass` 排除）。
   - IAP JWT署名二重検証ミドルウェア（`core/auth.py`）、内部監視エンドポイント、Pydantic Settings の実装。
4. 🎨 **UI/UXデザイナー (`ui-designer`) [Subagent]**:
   - 画面グランドデザイン完全準拠（4px/8pxグリッド、HEX/px絶対値併記、デイライト視認性・明暗ペア指定）。
   - **Anti-God Component 徹底**: **1ファイル最大250行制限**、Hooks/Services物理分離、直書きモック排除（MSW集約）。
   - **Profile D 二段階ハイブリッド規約**: PHASE 4〜5 はブラウザモード（Vite dev）で感覚センサー検証を完遂し、PHASE 6 で実機ネイティブ（`cargo tauri dev`）へ切り替える。
5. 🛡️ **品質・テスト & 監査・QAスペシャリスト (`qa-engineer`) [Subagent]**:
   - **Hard Gate & 3大レビュー厳格監査**:
     - 基本設計レビュー (`dev-review-arch`): `traceability_checker.py --mode design` PASS 必須。
     - コード品質レビュー (`dev-review-code`): `harness_guard.py --all` PASS 必須（250/400行・直書きモック排除・機能等価性マトリクス監査）。
     - システム総合レビュー (`dev-review-system`): 本番モックOFF二重防御、IAP JWT有効化、`traceability_checker.py --mode full` PASS 必須（異常系比率20%以上、3階層深層アサーション監査、実データ一気通貫E2E検証）。
   - ブラウザ感覚センサー（Chrome DevTools MCP / A11y / コンソールエラーゼロ）検証、RCA即時記録（`wiki-maintainer`）。
   - **【コード直接改変禁止】** システムコードに不具合を発見した場合は勝手に修正せず、調査結果とDiff案をコンダクターへ報告する。

---

## 3. 構造化状態台帳と Single Writer 原則 (V2.6.2 Hybrid State Ledger)
- 状態管理は、機械正本 `project_state.json` と自動生成ビュー `PROJECT_STATE.md` を1対1同期する。
- 更新権限は **👑 プロジェクトコンダクター専任** とし、`state_manager.py` 経由で原子的・決定論的に更新する。サブエージェントによる直接編集や手動改ざんはハッシュ不一致により遮断される。

---

## 4. 2層構造システムプロファイル体系 & Shift-Left Hard Gate 規約
事後修正ではなくコミット前・ランタイムに規約を物理遮断する。

### 4.1 第1層: 定常的コア設計規範 (全プロファイル共通)
1. **Hard Gate 物理遮断**: Git `pre-commit` フックおよび CI ゲートで `harness_guard.py` を実行し、250/400行制限、直書きモック、生SQL、AST違反をコミット前に機械遮断する。
2. **要件トレーサビリティ機械検証 & 3階層深層アサーション**:
   - 要件定義 `REQ-*`（サブ要件ID `[REQ-F01-01]` 等を含む）から設計・テストコードまでの 100% カバレッジと異常系テスト比率（20%以上）を `traceability_checker.py` で機械検証する。
   - 単なるDOM存在確認やローカル変数自己アサート等の「自己完結型トートロジー・テスト（アリバイテスト）」をAST静的解析で機械遮断し、必ず実コード・API・DOM操作の返却値や副作用を検証する「第1層（構造検証）」「第2層（状態・属性遷移検証）」「第3層（副作用・連動描画検証）」を満たすテストのみを有効カウント対象とする。
   - 多言語・非同期テスト検出（Python `async def test_` / Rust `fn test_` / TS `it(`, `test(`）に対応し、実DB/ファイルIOテスト時はテンポラリディレクトリ＋UUIDでテスト間干渉を完全分離する。
3. **ブラウザ感覚センサー**: Chrome DevTools MCP により実ブラウザのコンソールエラー 0件、WCAG AA コントラスト比（4.5:1）、A11yツリーを自動計測・検証する。
4. **型定義自動同期**: OpenAPI ➔ TypeScript Codegen 完全利用。
5. **シークレット厳格バリデーション & Dual Provisioning 原則**:
   - Pydantic Settings による起動時即死ガード。
   - Git追跡用公開テンプレート `.env.example` とローカル実行用実体 `.env` を常にセットで同期・維持する。欠落時は自己修復（補完）または安全フォールバックを行う。
6. **統一タイムゾーン運用**: Aware UTC 保存 / JST 表示。
7. **モック制御アダプター層**: 環境変数切替 (案C) ＋ 直書きモック排除 (案A)。実結合モードでのサイレントモックフォールバック厳格禁止。
8. **画面グランドデザイン規範**: 4px/8pxグリッド、HEX/px絶対値併記、デイライト視認性（明暗ペア指定）。
9. **CI・静的解析・テスト実行ディレクトリ非依存**:
   - バックエンド静的解析（`pyproject.toml`）にはフレームワーク標準イディオム（FastAPI `Depends` 等）競合抑止（`B008`, `E402` ignore）および循環参照許容を初期配備。
   - リポジトリ除外設定（`.gitignore`）で `*.json` 等を広範除外する場合も `!package-lock.json` はホワイトリスト保護する。
   - シナリオテストコードは実行カレントディレクトリ非依存パス（`ROOT_DIR = Path(__file__).resolve().parent.parent.parent`）を使用する。

### 4.2 第2層: システム展開プロファイル (Profile A〜E)
- **5大適合性診断と2択提案プロトコル**: プロファイル選定時は、インフラ要件・UI要件・運用コスト等に基づき適合性診断を実施し、最適な主案と代替案の2択を提示して合意形成する。
- **Profile A (サーバーレス極小コストWeb型 / ゴールデンパス)**: Cloud Run (`max-instances=1`) + Litestream + SQLite(WAL) + Alembic + IAP JWT 二重防御 + React SPA + Tailwind CSS + MSW。
  - **Litestream スーパーバイザー起動構文**: コンテナ起動スクリプト（`entrypoint.sh`）では必ず正規構文 `exec litestream replicate -config /etc/litestream.yml -exec "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"` を使用すること（誤った `run` 構文の禁止）。
- **Profile B (Web SSR / フルマネージドRDB型)**: Next.js/Nuxt SSR または FastAPI + Cloud SQL (PostgreSQL) + Alembic。
- **Profile C (静的MPA / 超軽量ツール型)**: FastAPI + Jinja2 + HTMX / 単一バイナリCLI。
- **Profile D (PCローカルデスクトップアプリ型)**: Tauri v2 + Local SQLite + Frameless TitleBar + 二段階ハイブリッド運用。本番ビルド時は `VITE_ENABLE_MOCK=false` を二重防御し、結合テスト時はWALモード一時実ファイルDBを使用する。
- **Profile E (AI Agent Skill / PKM 自動化・CLI型)**: Zero-Dependency Python 3（標準ライブラリのみ） + アトミックI/O + 2系統分離設計 + テストコード必須。

---

## 5. 3大レビュー必須通過規約
以下の3大レビューゲートにおいて合否判定を満たさない限り、次のフェーズへ進行してはならない。
1. **基本設計レビュー (`dev-review-arch`) [PHASE 3 完了ゲート]**: 判定 `PASS` または `CONDITIONAL PASS` 必須。
2. **コード品質レビュー (`dev-review-code`) [PHASE 5.5 完了ゲート]**: 判定 `CLEAN` 必須（`harness_guard.py` PASS 必須）。設計書との機能等価性マトリクスを監査し、プレースホルダーや縮退実装（機能オミット・空実装）を検出した場合は即座に `BLOCKED` 判定とする。
3. **システム総合レビュー (`dev-review-system`) [PHASE 7 リリース直前ゲート]**: 判定 `RELEASE APPROVED` 必須（本番モックOFF二重防御、IAP JWT有効化、`traceability_checker.py` PASS 必須）。PHASE 6/7 においてはモックOFF・実データ一気通貫E2Eユーザージャーニー検証を必須とする。

---

## 6. ナレッジ境界・二段階進化サイクルと Context Isolation 原則 (V2.6.2)
1. **試行錯誤・RCAのローカル固定蓄積**: エラー・手戻りのRCAは、**必ずカレントプロジェクト配下の `./wiki/`** に蓄積する。
2. **二層分離 (Two-Tier Separation) と二段階進化**:
   - **Tier 1 (プロジェクト固有仕様)**: `./wiki/patterns/local/` に記録し、各ゲートで `docs/` および台帳へ逆同期して完結。
   - **Tier 2 (全体共通知見 / 汎用パターン)**: `./wiki/patterns/universal/` に記録し、PHASE 8 で `wiki-proposer` が標準化知見原票（`CLAIM-*.md`）として `~/.gemini/knowledge-hub/inbox/` へ投函。
   - **Immutable Core + Local Overlay**: 3段階意味的監査を通過した知見は `~/.gemini/knowledge-hub/overlay/LOCAL_FEEDBACK_RULES.md` へクリーン再生成反映する。
3. **2系統分離原則**: 決定論的バグ（Hard Gate）は Linter / テストコード（Executable Specs）へ直接吸収し、セマンティック事象（Soft Engine）のみ Wiki パターンとして起票する。
4. **Context Isolation**: 通常エージェントへ生の Wiki パターン群をプロンプト注入せず、本文に Lineage 履歴を記載しない。
5. **Local Overlay の動的参照フック**: `~/.gemini/knowledge-hub/overlay/LOCAL_FEEDBACK_RULES.md` が存在する場合は併せて遵守する。

---

## 7. システム修正後のDockerコンテナ再構成徹底ルール
- システム修正後は、確実に変更を反映させるため、**必ず `docker compose down` および `docker compose up --build -d` を実行し、コンテナをビルド・再構成する**。

---

## 8. 自律修復ループ（Self-Healing Loop）の適用と制限
- 自律修復の対象は「ドキュメント」「テストスクリプト」「環境設定ファイル」に限定し、システム本体コードは直接改変しない。
- 連続実行回数は **最大5回まで** とする。

---

## 8.5 外部CLIの非対話実行、タイムアウト保護、およびフェーズ境界遵守
- 外部CLI実行時は `--quiet`、`--yes` 等の非対話オプションを明示指定する。`2>/dev/null` による標準エラー出力破棄は禁止。
- バックグラウンドタスク待機時は必ず `schedule` ツールでワンショット・タイムアウト監視を設定する。
- **Stage/Phase 境界の厳格遵守**: たとえ「終端処理」「クローズ」等の語句が含まれていても、次の Stage / Phase（特に GitHub push、タグ公開、本番デプロイ等の外部影響を伴う不可逆操作）をユーザーの明示的指示・承認なしに先走って実行してはならない。

---

## 9. セキュリティと認証
- APIキー等のシークレットはソースコードに直書きせず、`.env` 等の環境変数で管理する。
- リリース時は Cloud Run / IAP / IAM 認証設定およびアクセス制御を厳格に検証する。

---

## 10. ドキュメント管理および改訂ライフサイクル規約 (Revision Lifecycle)
1. **docs/ 運用ルール**:
   - `docs/設計書/` と `docs/検討課題/` に完全分離し、`docs/設計書/Current/` を唯一の正（Single Source of Truth）とする。
   - 正本設計書タイトルからは個別バージョン番号（`V1.x`）を排除し、システム SemVer（`APP_VERSION`）で一元管理する。
   - 改訂運用方針および詳細手順は `docs/システム改訂運用基準書.md` を参照する。
2. **改訂ライフサイクル (REV-1〜REV-5 標準パイプライン)**:
   - 初期開発完了後の機能追加・Hotfixは、`state_manager.py start-revision` による計画スケルトン自動展開を出発点とし、以下の5段階標準改訂パイプラインを厳守する:
     - `REV-1`: 要件・設計精査（差分要件 `REQ-*` & RTM設計カバレッジ 100%）
     - `REV-2`: 実装・静的検証（Hard Gate `harness_guard.py --all` PASS）
     - `REV-3`: テスト・視認レビュー（RTM full、深層アサーション、感覚センサー検証）
     - `REV-4`: 本番総合監査・成果物ビルド（コード/システム総合レビュー合格、本番成果物ビルド）
     - `REV-5`: メトリクス・知見昇格・リリース（定量メトリクス集計、知見昇格、Invariants Gate 通過確認）
   - 改訂クローズ時、`state_manager.py complete-revision` の Invariants Gate（成果物実在、メトリクス算出済み、未処理知見ゼロ、ブランチ整合性）を機械検証し、未達時は自動遮断する。
