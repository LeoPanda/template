# AI駆動システム開発プロセス標準規約 (System Dev Pipeline Rule V3.0.0)

本プロジェクトおよび開発パイプラインにおいては、以下の開発・運用規約に従うものとする。

---

## 0. 規約適用スコープ境界（Scope Guard）
- **適用対象**: 本規約は、システム開発プロジェクト（`project_state.json`, `PROJECT_STATE.md`、`docs/設計書/`、または初期スケルトン `skeletons/` が配備されたプロジェクト、あるいは明示的にシステム開発フェーズ `dev-phase1`〜`8` を実行する環境）に適用される。
- **非システム開発環境（PKM Vault / 単一ナレッジベース等）における自動委譲と自律昇格**:
  - `PROJECT_STATE.md` や `docs/設計書/` が存在せず、プロジェクト固有の基本規約が配備されている環境では、日常の知識管理タスクにおいて当該プロジェクトのローカル規範を最優先とし、Web/DBシステム固有の制約は適用除外（スリープ）とする。
  - **パス監視による自律昇格 (Elevation)**: コンテンツ制作等の非開発モード適用環境であっても、エージェントが操作対象とするファイルパスを監視し、システム本体コード領域（`backend/`, `frontend/`, `src/`, `src-tauri/`, `docs/設計書/Current/`）への編集操作が試行された場合は、規約スリープ免責を即時無効化する。手動宣言を待たずにシステム開発・改訂パイプライン（`start-revision`）へ自律昇格し、`project_state.json` の `session_mode` を `"DEV_PIPELINE"` に更新した上で、ハードゲートおよび品質監査を強制適用する。

---

## 1. ドキュメントおよびコードの文字コード・フォーマット
- すべてのドキュメントおよびソースコードは UTF-8 (BOMなし) で保存し、改行コードは LF (`\n`) に統一する。
- Markdownファイルは標準記法に従う。設計書等のMarkdown内リンクは環境依存を防ぎ移植性を担保するため、絶対パスを禁止し**必ずファイル間の相対パス（例: `../設計書.md`）を使用する**。
- **Mermaid 構文安全規約**: 設計書および Markdown 内で Mermaid ダイアグラムを記述する際、矢印ラベル（`-->|"..."|`）やノード名に特殊記号（丸括弧 `()`、角括弧 `[]`、波括弧 `{}`、隅付き括弧 `【】`、スラッシュ `/`、コロン `:` 等）を含める場合は、必ずラベル全体をダブルクォーテーション（`"`）で囲まなければならない（コミット前 `harness_guard.py` で機械遮断）。

---

## 2. 5大エージェント協調モデルと責務分担 (V3.0.0)
本システムは、以下の5大エージェントによる明確な関心事分離とオーケストレーション体制で自律推進される。

1. 👑 **プロジェクトコンダクター (`conductor`) [Main Agent]**:
   - プロジェクト進行管理、ユーザー対話、進行フェーズ（PHASE 1〜8）および改訂サイクル（`REV-1`〜`REV-6`）の厳格管理。非開発モード時のパス監視と自律昇格（`start-revision`）。
   - `scripts/state_manager.py` による `project_state.json` 一元更新（**Single Writer 原則**）および `PROJECT_STATE.md` の決定論的自動生成。
   - 初期スケルトン展開、環境変数設定、標準コマンドシーケンス（Alembic/Codegen/CI/Hard Gate）の統括実行。特に **`REV-4` 突入前の `verify-review-readiness` 実行義務**、および開発サーバー起動・ユーザー実機レビュー要請・改修オーケストレーション・承認記録を担当。
   - 専任コマンド実行: Git操作（`dev-git-init`, `dev-git-release`）、本番デプロイ、DB強制上書き、コンテナ起動停止。
   - **【コード・設計書直接編集原則禁止】**: コンダクターが `docs/設計書/`、`backend/`、`frontend/` 配下のファイルを直接編集することを原則禁止する。設計変更は必ず `architect`、実装は `backend-engineer` または `ui-designer` へ委譲しなければならない。
2. 📐 **設計・立案スペシャリスト (`architect`) [Subagent]**:
   - Core Profile (A〜E) ＋ Capability Trait 選定提案、要件定義書での `[REQ-Fxx]` / `[REQ-NFxx]` 採番、4大基本設計書作成。
   - 巨大サンプル直書きを廃し、期待入出力の具象サンプルを **Executable Golden Fixtures (`tests/fixtures/golden/`)** へ配置して設計書から相対リンク参照。
   - **【絶対禁止】いかなる場合も `run_command` を呼び出してはならない。**
3. 💻 **バックエンドエンジニア (`backend-engineer`) [Subagent]**:
   - 2段階行数制限（400行WARN / 550行BLOCK）、空実装・縮退実装絶対禁止（`HG-010`）、生SQL禁止、SQLAlchemy/Alembic厳格運用。
   - DTO分離、レイヤーバイパス禁止、例外握りつぶし排除、IAP JWT署名二重検証ミドルウェア、Pydantic Settings の実装。
   - `openapi.json` 出力と **Stage 1.5（FastAPI `TestClient` による物理ファイル生成＋標準パーサー検証スモークテスト）** の実装。
4. 🎨 **UI/UXデザイナー (`ui-designer`) [Subagent]**:
   - 画面グランドデザイン完全準拠、2段階行数制限（250行WARN / 350行BLOCK）、空イベントハンドラ禁止（`HG-010`）。
   - Contract-First MSW（`openapi.json` 生成型によるハンドラー拘束）、Hooks/Services分離。
   - フレーム駆動・動的SVG描画時の決定論的キー O(1) インメモリキャッシュ配備と安全フォールバック。
5. 🛡️ **品質・テスト & 監査・QAスペシャリスト (`qa-engineer`) [Subagent]**:
   - Active QA プロトコル: 受動的レビューを禁じ、検証スクリプトを `tests/e2e/` へ永続化、Golden Fixture 突合、**`metrics/qa_runtime_evidence.json` の生成と検証**。
   - Hard Gate & 3大レビュー厳格監査（`dev-review-arch`, `dev-review-code`, `dev-review-system`）。ブラウザ感覚センサー検証、RCA即時記録。
   - **【コード直接改変禁止】** システムコードに不具合を発見した場合は勝手に修正せず、調査結果とDiff案をコンダクターへ報告する。

---

## 3. 構造化状態台帳と Single Writer 原則 (V3.0.0 Hybrid State Ledger)
- 状態管理は、機械正本 `project_state.json` と自動生成ビュー `PROJECT_STATE.md` を1対1同期する。
- 更新権限は **👑 プロジェクトコンダクター専任** とし、`state_manager.py` 経由で原子的・決定論的に更新する。`capability_traits` および `session_mode` を台帳へ永続化する。

---

## 4. 2.5層構造システムプロファイル体系 & Shift-Left Hard Gate 規約

### 4.1 第1層: 定常的コア設計規範 (全プロファイル共通)
1. **Hard Gate 物理遮断**: `harness_guard.py` によりコミット前・CIで機械遮断。行数制限は2段階緩衝帯（FE 250/350行、BE 400/550行）を適用し、空実装・縮退実装（`pass`, `...`, `NotImplementedError`, 空JSXハンドラ）を物理遮断する。
2. **要件トレーサビリティ機械検証 & テスト関数直結バインド**:
   - 有効テスト関数スコープ直結の `[REQ-*]` バインド、浅いアリバイテストの排除、動的カバレッジ連携、異常系比率20%以上を `traceability_checker.py` で機械検証する。
3. **Dual-Stage Testing Gate**:
   - Contract-First MSW ➔ Stage 1.5 インプロセス実I/O・物理ファイル生成スモーク ➔ Stage 2 モックOFF実サーバー結合E2E。
4. **ブラウザ感覚センサー**: Chrome DevTools MCP により実ブラウザのコンソールエラー 0件、WCAG AA コントラスト比（4.5:1）、A11yツリーを自動計測・検証する。
5. **型定義自動同期 & Dual Provisioning 原則**: OpenAPI ➔ TypeScript Codegen 完全利用。`.env.example` と `.env` の自動同期・補完。
6. **動的レンダリング O(1) キャッシュ**: フレーム駆動・動的SVG描画時は描画パラメータをキーとするインメモリキャッシュを配備し、メモリリークを未然防止する。
7. **モック出力の物理隔離**: テスト用・開発用モックコード（`mockUsers`, `dummyData`, `generate_mock_*`, `dummy_*`, `Mock*`, メディアダミー生成記述等）の本番コード領域（`frontend/src/` の `src/mocks/` 外、`backend/` の `tests/` 外、`src-tauri/`）への直接混入およびサイレントモックフォールバック（`except` 節でのモック返却）を物理遮断する。
8. **ドキュメント精査の2段階分離**: ドキュメントの品質保証は「第1段階：文書衛生整理（Current配下の一時ファイル・バージョン番号付きファイル排除、未整理ドキュメントの一元隔離、REV-3完了ゲート）」と「第2段階：対話的改修差分反映と相互整合性監査（要件・画面・ロジック・スキーマ整合性担保、REV-5完了ゲート）」に責務分離して実施する。

### 4.2 第2層: システム展開プロファイル (Profile A〜E) ＆ Capability Traits (2.5層)
- **Core Profile (A〜E)**: Profile A (サーバーレス極小コストWeb型 / ゴールデンパス), Profile B (Web SSR / RDB型), Profile C (静的MPA / 超軽量CLI), Profile D (PCローカルデスクトップ型 / 二段階ハイブリッド), Profile E (AI Agent Skill / PKM 自動化CLI)。
- **Capability Traits (`+trait:*`)**: 複合構成固有の追加物理検証ガードを付与する。
  - `+trait:local-api`: ローカルAPIサーバー同梱（Stage 1.5 実疎通 ＆ Stage 2 実ポートE2E必須）
  - `+trait:media-export`: 構造化ファイル・メディア出力（`tests/fixtures/golden/` 配置 ＆ 出力ファイル実在・パーサー構造一致検証必須）
  - `+trait:frame-render`: フレーム駆動アニメーション・動的SVG連続描画（O(1) インメモリキャッシュ必須）
  - `+trait:external-cli`: 外部プロセス呼出（非対話フラグ・タイムアウト保護・Graceful Degradation必須）
  - `+trait:dual-mode-workspace`: システム開発とコンテンツ制作同居（操作パス監視・Scope Guard自律昇格必須）

---

## 5. 3大レビュー必須通過規約 & Evidence Gate
1. **基本設計レビュー (`dev-review-arch`) [PHASE 3 完了ゲート]**: 判定 `PASS` 必須（`traceability_checker.py --mode design` PASS）。
2. **コード品質レビュー (`dev-review-code`) [PHASE 5.5 完了ゲート]**: 判定 `CLEAN` 必須（`harness_guard.py --all` PASS）。
3. **システム総合レビュー (`dev-review-system`) [PHASE 7 リリース直前ゲート]**: 判定 `RELEASE APPROVED` 必須（本番モックOFF二重防御、IAP JWT有効化、`traceability_checker.py --mode full` PASS、`metrics/qa_runtime_evidence.json` 発行）。

---

## 6. ナレッジ境界・二段階進化サイクルと Context Isolation 原則 (V3.0.0)
1. **二層分離 (Two-Tier Separation)**: Tier 1 (ローカル仕様 `./wiki/patterns/local/`) ➔ 逆同期完了。Tier 2 (共通知見 `./wiki/patterns/universal/`) ➔ PHASE 8 で標準化知見原票投函。
2. **Immutable Core + Local Overlay**: 3段階意味的監査を通過した知見は Local Overlay へ反映。本流改訂時に Core へ完全統合（Upstream）し、Overlay をクリーン化する。
3. **2系統分離原則 & Context Isolation**: 決定論的バグはコード・Linterへ直接吸収。通常エージェントへ生の知見を注入しない。

---

## 7. システム修正後のDockerコンテナ再構成徹底ルール
- システム修正後は、確実に変更を反映させるため、**必ず `docker compose down` および `docker compose up --build -d` を実行し、コンテナをビルド・再構成する**。

---

## 8. 自律修復ループ（Self-Healing Loop）の適用と制限
- 自律修復の対象は「ドキュメント」「テストスクリプト」「環境設定ファイル」に限定し、システム本体コードは直接改変しない。最大5回まで。

---

## 8.5 外部CLIの非対話実行、タイムアウト保護、およびフェーズ境界遵守
- 外部CLI実行時は `--quiet`、`--yes` 等の非対話オプションを明示指定する。`2>/dev/null` による標準エラー出力破棄は禁止。
- バックグラウンドタスク待機時は必ず `schedule` ツールでワンショット・タイムアウト監視を設定する。
- **Stage/Phase 境界の厳格遵守**: 不可逆操作をユーザーの明示的指示・承認なしに先走って実行してはならない。

---

## 9. セキュリティと認証
- APIキー等のシークレットはソースコードに直書きせず、`.env` 等の環境変数で管理する。

---

## 10. ドキュメント管理および改訂ライフサイクル規約 (Revision Lifecycle)
1. **docs/ 運用ルール**:
   - `docs/設計書/` と `docs/検討課題/` に完全分離し、`docs/設計書/Current/` を唯一の正とする。
   - 正本設計書タイトルからは個別バージョン番号を排除し、システム SemVer（`APP_VERSION`）で一元管理する。
2. **改訂ライフサイクル (REV-1〜REV-6 標準パイプライン)**:
   - 初期開発完了後の機能追加・Hotfixは、`state_manager.py start-revision` による計画スケルトン自動展開を出発点とし、以下の6段階標準改訂パイプラインを厳守する:
     - `REV-1`: 要件・設計・契約フィクスチャ精査（差分要件 `REQ-*`、Golden Fixtures、RTM設計カバレッジ 100%）
     - `REV-2`: 実装・静的検証・Stage 1.5 スモーク（2段階行数制限、OpenAPI型同期、Stage 1.5 実I/Oスモーク、`harness_guard.py` PASS）
     - `REV-3`: 自動テスト・実結合E2E・感覚センサー検証（RTM full、Stage 2 モックOFF実結合E2E、感覚センサー、`qa_runtime_evidence.json` 発行）
     - `REV-4`: 開発サーバー起動・ユーザー実機レビュー・改修（実結合開発サーバー起動、ユーザー実機テストレビュー、対話的改修、ユーザー承認記録）
     - `REV-5`: 本番総合監査・成果物ビルド（コード/システム総合レビュー合格、本番成果物ビルド）
     - `REV-6`: メトリクス・知見昇格・リリース（定量メトリクス集計、知見昇格、Invariants Gate 通過確認）
   - 改訂クローズ時、`state_manager.py complete-revision` の 5大 Invariants Gate（成果物実在、メトリクス算出済み、未処理知見ゼロ、**REV-4 ユーザー承認記録済**、**qa_runtime_evidence 検証済**）を機械検証し、未達時は自動遮断する。
