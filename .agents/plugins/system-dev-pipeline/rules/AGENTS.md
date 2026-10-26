# AI駆動システム開発プロセス標準規約 (System Dev Pipeline Rule V2.6)

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

---

## 2. 5大エージェント協調モデルと責務分担 (V2.6)
本システムは、以下の5大エージェントによる明確な関心事分離とオーケストレーション体制で自律推進される。

1. 👑 **プロジェクトコンダクター (`conductor`) [Main Agent]**:
   - プロジェクト進行管理、ユーザー対話、進行フェーズ（PHASE 1〜8）および改訂サイクルの厳格管理。
   - `scripts/state_manager.py` による `project_state.json` 一元更新（**Single Writer 原則**）および `PROJECT_STATE.md` の決定論的自動生成。
   - 初期スケルトン展開、環境変数設定、標準コマンドシーケンス（Alembic/Codegen/CI/Hard Gate）の統括実行。
   - 専任コマンド実行: Git操作（`dev-git-init`, `dev-git-release`）、本番デプロイ、DB強制上書き、コンテナ起動停止。
   - PHASE 8 における知見・メトリクス統括（`metrics_collector.py --all --sync-state`, `pipeline-reconciler.sh`）。
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
     - コード品質レビュー (`dev-review-code`): `harness_guard.py --all` PASS 必須（250/400行・直書きモック排除）。
     - システム総合レビュー (`dev-review-system`): 本番モックOFF二重防御、IAP JWT有効化、`traceability_checker.py --mode full` PASS 必須（異常系比率20%以上）。
   - ブラウザ感覚センサー（Chrome DevTools MCP / A11y / コンソールエラーゼロ）検証、RCA即時記録（`wiki-maintainer`）。
   - **【コード直接改変禁止】** システムコードに不具合を発見した場合は勝手に修正せず、調査結果とDiff案をコンダクターへ報告する。

---

## 3. 構造化状態台帳と Single Writer 原則 (V2.6 Hybrid State Ledger)
- 状態管理は、機械正本 `project_state.json` と自動生成ビュー `PROJECT_STATE.md` を1対1同期する。
- 更新権限は **👑 プロジェクトコンダクター専任** とし、`state_manager.py` 経由で原子的・決定論的に更新する。サブエージェントによる直接編集や手動改ざんはハッシュ不一致により遮断される。

---

## 4. 2層構造システムプロファイル体系 & Shift-Left Hard Gate 規約
事後修正ではなくコミット前・ランタイムに規約を物理遮断する。

### 4.1 第1層: 定常的コア設計規範 (全プロファイル共通)
1. **Hard Gate 物理遮断**: Git `pre-commit` フックおよび CI ゲートで `harness_guard.py` を実行し、250/400行制限、直書きモック、生SQL、AST違反をコミット前に機械遮断する。
2. **要件トレーサビリティ機械検証**: 要件定義 `REQ-*` から設計・テストコードまでの 100% カバレッジと異常系テスト比率（20%以上）を `traceability_checker.py` で機械検証する。
3. **ブラウザ感覚センサー**: Chrome DevTools MCP により実ブラウザのコンソールエラー 0件、WCAG AA コントラスト比（4.5:1）、A11yツリーを自動計測・検証する。
4. **型定義自動同期**: OpenAPI ➔ TypeScript Codegen 完全利用。
5. **シークレット厳格バリデーション**: Pydantic Settings による起動時即死ガード。
6. **統一タイムゾーン運用**: Aware UTC 保存 / JST 表示。
7. **モック制御アダプター層**: 環境変数切替 (案C) ＋ 直書きモック排除 (案A)。実結合モードでのサイレントモックフォールバック厳格禁止。
8. **画面グランドデザイン規範**: 4px/8pxグリッド、HEX/px絶対値併記、デイライト視認性（明暗ペア指定）。

### 4.2 第2層: システム展開プロファイル (Profile A〜E)
- **Profile A (サーバーレス極小コストWeb型 / ゴールデンパス)**: Cloud Run (`max-instances=1`) + Litestream (`litestream run`) + SQLite(WAL) + Alembic + IAP JWT 二重防御 + React SPA + Tailwind CSS + MSW。
- **Profile B (Web SSR / フルマネージドRDB型)**: Next.js/Nuxt SSR または FastAPI + Cloud SQL (PostgreSQL) + Alembic。
- **Profile C (静的MPA / 超軽量ツール型)**: FastAPI + Jinja2 + HTMX / 単一バイナリCLI。
- **Profile D (PCローカルデスクトップアプリ型)**: Tauri v2 + Local SQLite + Frameless TitleBar + 二段階ハイブリッド運用。
- **Profile E (AI Agent Skill / PKM 自動化・CLI型)**: Zero-Dependency Python 3（標準ライブラリのみ） + アトミックI/O + 2系統分離設計 + テストコード必須。

---

## 5. 3大レビュー必須通過規約
以下の3大レビューゲートにおいて合否判定を満たさない限り、次のフェーズへ進行してはならない。
1. **基本設計レビュー (`dev-review-arch`) [PHASE 3 完了ゲート]**: 判定 `PASS` または `CONDITIONAL PASS` 必須。
2. **コード品質レビュー (`dev-review-code`) [PHASE 5.5 完了ゲート]**: 判定 `CLEAN` 必須（`harness_guard.py` PASS 必須）。
3. **システム総合レビュー (`dev-review-system`) [PHASE 7 リリース直前ゲート]**: 判定 `RELEASE APPROVED` 必須（本番モックOFF二重防御、IAP JWT有効化、`traceability_checker.py` PASS 必須）。

---

## 6. ナレッジ境界・二段階進化サイクルと Context Isolation 原則 (V2.6)
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

## 8.5 外部CLIの非対話実行とバックグラウンド待機タイムアウト保護
- 外部CLI実行時は `--quiet`、`--yes` 等の非対話オプションを明示指定する。`2>/dev/null` による標準エラー出力破棄は禁止。
- バックグラウンドタスク待機時は必ず `schedule` ツールでワンショット・タイムアウト監視を設定する。

---

## 9. セキュリティと認証
- APIキー等のシークレットはソースコードに直書きせず、`.env` 等の環境変数で管理する。
- リリース時は Cloud Run / IAP / IAM 認証設定およびアクセス制御を厳格に検証する。

---

## 10. ドキュメント管理および改訂ライフサイクル規約 (Revision Lifecycle)
1. **docs/ 運用ルール**: `docs/設計書/` と `docs/検討課題/` に完全分離し、`docs/設計書/Current/` を唯一の正（Single Source of Truth）とする。
2. **改訂ライフサイクル (5段階)**:
   - 初期開発完了後の機能追加・Hotfixは、`state_manager.py start-revision`（起票）➔ 差分要件/設計（`REQ-*` ＆ RTM）➔ 差分実装（Hard Gate pre-commit）➔ 回帰/感覚センサー検証（RTM full）➔ `state_manager.py complete-revision`（完了）のサイクルを厳守する。
