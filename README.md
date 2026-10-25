# Antigravity AI-Driven System Dev Pipeline V2.5 🚀

Google Antigravity のマルチエージェントオーケストレーション、カスタムスキル（Skills）、およびプラグインアーキテクチャを活用し、**新規プロジェクトの環境準備から要件定義、基本設計、環境構築、ウォークスルー、自動テスト、本番リリース、そしてマルチプロジェクト・マルチ環境を跨ぐ自己進化・改訂運用に至る全開発ライフサイクルを自律的に統制・自動化する開発基盤テンプレート**です。

---

## 📌 概要

V1.0（単一エージェント）、V2.0（Conductor ＋ 3エージェント分業）、V2.1（5大エージェント協調、3大レビューゲート、WikiSkill自己進化ループ、定量測定機構）、V2.2（Shift-Left 静的スケルトン基盤、2層構造プロファイル体系 Profile A〜E、画面グランドデザイン、MSWモック制御）、V2.3（Central Knowledge Hub、3段階意味的整合性監査、Immutable Core / Local Overlay 二層プラグイン機構）、V2.4（SemVer 2.0.0 完全準拠、開発手順書・設計書群再編、DTO/パーサー物理分離・デイライトUI等の6大知見本流統合）を経て、**Version 2.5 (V2.5)** では実稼働プロジェクトの運用成果を結集し、以下の **3大ピラー** を軸に抜本的な進化を遂げました：

1. **Central Knowledge Hub 蓄積知見の公式本流統合 (Core Integration)**:
   先行運用されてきた 5 件の高品質な汎用知見原票（PAT-SYS-002: メトリクス即時反映、PAT-SYS-003: JSON出力パス統一、PAT-SYS-004: フェーズ推移レポート生成、PAT-SYS-005: レビューパーサー正規表現堅牢化、PAT-SYS-006: グローバル pattern_id 一意性保証）を公式パイプライン（Immutable Core）へ本流統合し、Local Overlay の行数バジェット（上限80行）を完全解放。
2. **定量測定エンジン (`dev-metrics-collector`) のアーキテクチャ刷新**:
   旧来の 972 行の一枚岩スクリプトを、Profile E（Zero-Dependency Python 3）制約を維持したまま 4 つの責務別モジュール（`metrics_types.py`, `parsers.py`, `scoring.py`, `reporters.py`, `metrics_collector.py`）へ物理分割。`start_time` 基準二段時系列ソート、動的ターン予算モデル、実測自律修復追跡を導入し、全モジュール 400 行以内厳守（Anti-God Module 解消）と測定精度の飛躍的向上を両立。
3. **パイプライン全域多次元総点検と設計書・基盤コード V2.5 全面同期**:
   全19スキル、全5エージェント、基盤スクリプト、設計書、規約の4大監査軸（齟齬・重複・不足・純度）を網羅監査。`pipeline-reconciler.sh` のコアロジックを `scripts/reconciler_core.py` へ分離、Profile A スケルトンの `litestream run` スーパーバイザー起動方式移行、Profile D スケルトンの `temp_db` 一時実ファイル動的プロビジョニング実装、および `docs/設計書/Current/` 配下の全10設計書を V2.5 仕様へ刷新。

---

## ✨ V2.5 の主な新機能と進化ポイント（3大ピラー）

```mermaid
flowchart TD
    subgraph P1["Pillar 1: Central Knowledge Hub 知見本流統合 (Core Integration)"]
        P1_1["PAT-SYS-002: メトリクス集計後の PROJECT_STATE.md 即時反映・同期義務化"]
        P1_2["PAT-SYS-003: メトリクス成果物出力先の metrics/ への完全集約・統一"]
        P1_3["PAT-SYS-004: フェーズ・改訂ターン別推移レポート (development_phase_report.md) 標準成果物化"]
        P1_4["PAT-SYS-005: レビュー報告書パーサー堅牢化と修復ターン数正規化"]
        P1_5["PAT-SYS-006: Central Knowledge Hub 全域 pattern_id 一意性保証・昇格時Fail-Fast"]
        P1_6["知見原票の archive/upstreamed/ 移管 & Overlay バジェット解放"]
    end

    subgraph P2["Pillar 2: 定量測定エンジン (dev-metrics-collector) アーキテクチャ刷新"]
        P2_1["4モジュール物理分割 (Anti-God Module 解消 / 全ファイル400行以内)"]
        P2_2["start_time 基準二段時系列ソート (mtime 依存脱却)"]
        P2_3["動的ターン予算モデル & 実測自律修復ターン追跡"]
        P2_4["dataclass 型スキーマ導入 (Zero-Dependency 型安全)"]
        P2_5["例外捕捉限定化と詳細診断ロギング"]
    end

    subgraph P3["Pillar 3: パイプライン全域多次元総点検 & 基盤コード V2.5 全面同期"]
        P3_1["全域多次元総点検: 全19スキル・エージェント・スクリプト・設計書のクロスチェック"]
        P3_2["scripts/reconciler_core.py: pipeline-reconciler.sh の Python コア分離 (379行)"]
        P3_3["Profile A: entrypoint.sh の litestream run スーパーバイザー起動方式移行"]
        P3_4["Profile D: conftest.py の temp_db 一時実ファイルDB動的プロビジョニング"]
        P3_5["docs/設計書/Current/: 全10設計書を V2.5 規格へ全面改訂・v2.4アーカイブ退避"]
    end

    P1 & P2 & P3 --> V25["AI駆動システム開発テンプレート V2.5.0"]
```

### 1. 本流統合された 5 大知見の詳細仕様（Pillar 1）
- **`PROJECT_STATE.md` 定量メトリクス同期義務化 (PAT-SYS-002)**:
  `dev-metrics-collector` 実行後、コンダクターはレポート確認と不可分な一連処理として、`metrics/system_health_report.md` の主要指標（総合スコア、グレード、各カテゴリスコア、トークン数、ツール呼出数）を `PROJECT_STATE.md` へ即時同期し、ヘッダー更新日時を更新する。
- **メトリクス成果物出力先の `metrics/` への完全集約・統一 (PAT-SYS-003)**:
  集計サマリJSON（`development-metrics-summary.json`）、総合レポート（`system_health_report.md`）、推移レポート（`development_phase_report.md`）の出力先を `metrics/` に統一。旧来の `docs/plans/metrics/` への分散出力を完全廃止し、ドキュメント・規約・スキルの参照パスを一元化。
- **フェーズ・改訂ターン別推移レポートの標準成果物化 (PAT-SYS-004)**:
  全セッション通算の健全性スコアに加え、PHASE 1〜8 および各改訂ターン別の所要時間・エラー数・会話ターン数の推移を自動集計し、`metrics/development_phase_report.md` を標準成果物として自動生成・配備。
- **レビューパーサー堅牢化と修復ターン数正規化 (PAT-SYS-005)**:
  レビュー報告書解析において Markdown 太字記号（`**`）、表記揺れ（`総合判定`/`総合合否判定`/`判定結果`/`合否判定`）、各種括弧を包括許容。通算集計時の自律修復ターン数はセッション数で正規化した平均値を算出。
- **Central Knowledge Hub pattern_id 一意性保証 (PAT-SYS-006)**:
  起票時（`wiki-proposer`）に Knowledge Hub 全域を走査して未使用最新連番を一意採番。昇格時（`reconciler_core.py`）および Semantic Auditor（Gate 1）において重複衝突を Fail-Fast 検出し、ID衝突を未然に防止。

### 2. 定量測定エンジン物理分割構成（Pillar 2）
単一の `metrics_collector.py`（972行）を、Profile E（Zero-Dependency Python 3）制約を維持したまま、以下の4つの責務別モジュールへ物理分割。全モジュールは最大400行制限を厳守：
- `metrics_types.py` (114行): dataclasses 型スキーマ定義
- `parsers.py` (386行): `start_time` 基準二段時系列ソート、自律修復実測追跡、Git空ツリーLOC取得
- `scoring.py` (174行): 動的ターン予算モデル、実測修復ターン反映、12指標スコアリング
- `reporters.py` (230行): Markdown総合・推移レポート生成、JSON出力（`metrics/` 集約）
- `metrics_collector.py` (136行): CLIオーケストレーション

---

## 👥 エージェント体制と役割分担 (5大エージェント協調モデル V2.5)

```
                    ┌────────────────────────────────────────┐
                    │               👤 ユーザー              │
                    │  (要求提示 / 承認ゲート決裁 / 実機検証)│
                    └──────────────────┬─────────────────────┘
                                       │ 対話 / 指示 / 承認
                                       ▼
                    ┌────────────────────────────────────────┐
                    │ 👑 1. プロジェクトコンダクター (Main)    │
                    │      (全体進行 / Single Writer /       │
                    │       標準コマンド統括 / Git・デプロイ)│
                    │      [Model: pro / Workspace: main]    │
                    └──────────────────┬─────────────────────┘
                                       │ 委譲 (invoke_subagent)
         ┌───────────────┬─────────────┴─────────────┬───────────────┐
         ▼               ▼                           ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ 📐 2. 設計立案   │ │ 💻 3. BE実装     │ │ 🎨 4. FE/UI     │ │ 🛡️ 5. 品質監査  │
│    スペシャリスト│ │    スペシャリスト│ │    デザイナー     │ │  & Semantic監査 │
│ (architect)     │ │ (backend-       │ │ (ui-designer)   │ │ (qa-engineer)   │
│                 │ │  engineer)      │ │                 │ │                 │
│ [Model: pro]    │ │ [Model: pro]    │ │ [Model: flash]  │ │ [Model: pro]    │
│ ※ run_command   │ │ ※ コンテナ起動・│ │ ※ UIビルド・   │ │ ※ コード・Core  │
│   完全禁止      │ │   Git操作禁止   │ │   npm限定       │ │   直接改変禁止  │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │                   │
         └───────────────────┴─────────┬─────────┴───────────────────┘
                                       ▼
                         ┌──────────────────────────┐
                         │ ⚙️ 決定論的ツール / スキル │
                         │ ・Git管理 (dev-git-*)    │
                         │ ・デプロイ (dev-db-*)    │
                         │ ・Hub調停 (reconciler_core)
                         │ ・標準コマンド統括実行   │
                         └──────────────────────────┘
```

| ロール | 種別 / 推奨モデル | 主な担当スコープ (V2.5) | 権限・ガードレール (`CORE_INVARIANTS.md`) |
| :--- | :--- | :--- | :--- |
| 👑 **Conductor** | メイン / `pro` | 全体進行管理、`PROJECT_STATE.md` 一元更新（**Single Writer**）、**メトリクス即時同期 (PAT-SYS-002)**、PHASE 1 Hub検知・スケルトン展開、標準コマンド統括実行、Git・デプロイ専任実行、PHASE 8 知見投函・Overlay再生成 | 全ツール利用可能（**非対話CLIフラグ強制・`schedule` タイマー保護: `INV-06`**） |
| 📐 **Architect** | サブ / `pro` | 要件定義書（Profile A〜E選定）、4大基本設計書作成、外部API二重キャッシュ・Fail-Fastモック仕様設計、Alembic前提スキーマ設計、API仕様書同期 | `enable_write_tools: true`（**`run_command` は厳格禁止: `INV-02`**） |
| 💻 **Backend Engineer** | サブ / `pro` | バックエンドAPI、SQLAlchemyモデル（400行制限）、**DTO・パーサー物理分離（PAT-CODE-001）**、Alembicマイグレーション、IAP JWT署名二重検証ミドルウェア、内部監視エンドポイント実装 | 単体テスト・構文検証のみ許可（**生SQL禁止: `INV-05`、Git/デプロイ/DB上書き/コンテナ起動停止は禁止: `INV-02`**） |
| 🎨 **UI Designer** | サブ / `flash` または `pro` | 画面仕様書（グランドデザイン新規格準拠）、モダンフロントエンド画面実装、**1ファイル最大250行制限（`INV-03`）**、**デイライト視認性明暗ペア担保（PAT-UI-001）**、**MSWモックハンドラー構築（`INV-04`）** | パッケージ導入・UIビルドのみ許可（**Git/デプロイ/DB操作禁止: `INV-02`**） |
| 🛡️ **QA Engineer** | サブ / `pro` | ドキュメント多次元整合性監査（`dev-doc-reviewer`）、3大レビュー（基本設計/コード品質/システム総合: `INV-07`）、スルーテスト自動修復、障害RCA記録（`wiki-maintainer`）、**3段階意味的整合性監査（Semantic Auditor / pattern_id一意性検証）** | テスト・静的解析・バジェット監査のみ許可（**アプリ本体コードおよび Immutable Core 直接改変禁止: `INV-02`/`INV-09`**） |

---

## 📂 ディレクトリ構成

### 1. ワークスペースおよびプラグイン領域
```text
.
├── .agents/
│   ├── skills/
│   │   └── template-pipeline-sync/      # 🔄 テンプレート改訂専用 Global⇔Workspace 同期スキル
│   └── plugins/
│       └── system-dev-pipeline/         # 🔒 開発自動化プラグイン正本 (Immutable Core v2.5.0)
│           ├── plugin.json              # プラグインマニフェスト（agents 5件, skills 19件）
│           ├── PIPELINE_MANIFEST.json   # 📜 バージョン・公式吸収済みパターンID（13件）の機械可読正本
│           ├── FEEDBACK_LEDGER.md       # 📖 人間監査用の知見適合履歴・系譜台帳
│           ├── scripts/
│           │   ├── pipeline-reconciler.sh # ⚙️ 軽量シェルディスパッチャ (43行)
│           │   └── reconciler_core.py     # ⚙️ Hub管理・Overlay再生成・Upgrade Reconciler コア (379行)
│           ├── agents/                  # 👥 エージェント定義（conductor, architect, backend, ui, qa）
│           ├── rules/                   # 📜 開発プロセス標準規約 (AGENTS.md) & コア不変原則 (CORE_INVARIANTS.md)
│           ├── skeletons/               # 🧱 プロファイル別初期コードスケルトン (common, profile-a, profile-d)
│           │   ├── profile-a/docker/entrypoint.sh # litestream run スーパーバイザー起動
│           │   └── profile-d/backend/tests/conftest.py # temp_db 一時実ファイル動的プロビジョニング
│           ├── skills/                  # ⚙️ カスタムスキル群（全19種）
│           │   └── dev-metrics-collector/scripts/ # 📊 4モジュール分割された定量測定エンジン
│           │       ├── metrics_collector.py (CLI)
│           │       ├── metrics_types.py     (型スキーマ)
│           │       ├── parsers.py           (パーサー)
│           │       ├── scoring.py           (スコアリング)
│           │       └── reporters.py         (レポーター)
│           └── templates/               # 📄 V2.5 標準ドキュメント・設定ファイル雛形
├── docs/                                # 仕様書・設計書・レポート
│   ├── 設計書/
│   │   ├── Current/                     # ★現在の正本（Single Source of Truth: V2.5 正本設計書 全10文書）
│   │   └── v2.4/ v2.3/ v2.2/ v2.1/ v2.0/# 過去バージョン設計書アーカイブ
│   ├── 検討課題/                        # バージョン別検討課題・評価レポート群 (v2.5配下に総点検報告書)
│   └── reports/                         # 各種調査・監査報告書
├── metrics/                             # 📊 定量測定成果物集約ディレクトリ (PAT-SYS-003)
│   ├── system_health_report.md          # 総合健全性診断レポート
│   ├── development_phase_report.md      # フェーズ・改訂推移レポート (PAT-SYS-004)
│   └── development-metrics-summary.json # 定量サマリJSON
├── rules/
│   └── AGENTS.md                        # ワークスペース共通ルール + 第11節(パイプライン改訂同期規約)
└── README.md
```

### 2. PC環境共通 ナレッジハブ領域（`~/.gemini/knowledge-hub/`）
```text
~/.gemini/knowledge-hub/
├── inbox/                               # 📥 全案件から投函された未処理の標準化知見原票 (CLAIM-*.md)
├── pending_approval/                    # 🗂️ バックグラウンド監査時の承認待ちステージング
├── overlay/                             # 🧩 Immutable Core を一切汚さず次案件から即時有効化される拡張層
│   └── LOCAL_FEEDBACK_RULES.md          # active_claims からクリーン再生成される追加規約 (上限 80行)
├── active_claims/                       # 現在 overlay/ に反映されている有効原票の実体保管庫
├── archive/upstreamed/                  # 📦 新Ver Upgrade Reconciler で Core 吸収済みと判定され退役した原票
├── suspended/                           # ⏸️ 一時保留された原票
├── rejected/                            # 🚫 意味的監査で棄却された原票の永続記録
└── LOCAL_HUB_STATE.json                 # ベースCoreバージョンと適用中Claim IDの状態マニフェスト
```

---

## 🛠 全19スキル（Skills）一覧

| フェーズ / 用途 | スキル名 | 主担当 | 概要・実行内容 (V2.5仕様) |
| :--- | :--- | :--- | :--- |
| **PHASE 1** | `dev-phase1-setup` | 👑 Conductor | **Knowledge Hub 検知**、ディレクトリ構造展開、静的スケルトン基盤（`skeletons/`）配置、`.env`、`PROJECT_STATE.md`（SemVer 3桁 `v1.0.0`）。 |
| **PHASE 2** | `dev-phase2-requirements` | 📐 Architect | `docs/要件定義書.md` 精査、**2層プロファイル体系（Profile A〜E）選定**、定常コア8項目の非機能要件自動バインド。 |
| **PHASE 3** | `dev-phase3-design` | 📐 Architect<br>└ 🎨 UI | **Shift-Left基本設計4書**（技術/スキーマ/ロジック/画面仕様）策定。グランドデザイン新規格準拠、Alembic前提、二重キャッシュ、デイライト視認性。 |
| **PHASE 3 ゲート** | `dev-review-arch` | 🛡️ QA | **基本設計レビュー**。定常コア8項目および展開プロファイル別適合アーキテクチャ監査（`PASS` 必須）。 |
| **PHASE 4** | `dev-phase4-env-build` | 👑 Conductor<br>├ 💻 BE<br>└ 🎨 UI | 静的スケルトンを土台にDocker環境構築、💻 BE ＋ 🎨 UI 並行実装、**DTO・パーサー物理分離**、**標準コマンドシーケンス**自動実行、Git初期化。 |
| **PHASE 4** | `dev-git-init` | ⚙️ Conductor | `Git運用基準書.md` 配置、`.gitignore` 設定、Git初期化（`main`）、`feature` ブランチ作成。 |
| **PHASE 5** | `dev-phase5-walkthrough` | 👑 Conductor<br>└ 📐 Architect | 画面ウォークスルー動作確認統括、**モック透過切替検証 (Fail-Fast原則)**、不具合修正、最新コードを正としたAPI仕様書同期。 |
| **PHASE 5.5 ゲート**| `dev-review-code` | 🛡️ QA | **コード品質・整合性レビュー**。**250行/400行制限検査**、**直書きモック排除**、**DTO・パーサー分離検査**、**デイライト視認性検査**、型同期（`CLEAN` 必須）。 |
| **PHASE 6** | `dev-phase6-testing` | 🛡️ QA | シナリオテスト計画書作成、自動テストコード構築、**Profile D一時実ファイルDB動的プロビジョニング (PAT-TEST-001/temp_db)**、自動修復ループ（最大5回）。 |
| **PHASE 6 / RCA** | `wiki-maintainer` | 🛡️ QA | **障害時RCA即時記録**。テスト失敗・手戻り発生時に根本原因を分析し `./wiki/patterns/` へ即時記録。 |
| **PHASE 7 ゲート** | `dev-review-system` | 🛡️ QA | **システム総合レビュー**。**本番モックOFF二重防御 & Fail-Fast 監査**、**IAP JWT署名検証有効化**、**Profile A litestream run スーパーバイザー起動保証**、平文排除（`RELEASE APPROVED` 必須）。 |
| **PHASE 7** | `dev-phase7-release` | 👑 Conductor | システム総合レビュー合格確認、本番適用作業手順書作成、**非対話CLIガードレール（`--quiet` 強制・`schedule` タイマー監視）** による安全デプロイ。 |
| **PHASE 8** | `dev-phase8-rules` | 👑 Conductor<br>└ 🛡️ QA | メトリクス集計、原票クラスタリング、**知見原票投函 ➔ 3段階意味的監査 ➔ `ask_question` 承認 ➔ Local Overlay 再生成**、Git本番リリース。 |
| **PHASE 8 / 起案** | `wiki-proposer` | 👑 Conductor | **標準化知見原票起案・投函**。Tier 2 知見から `CLAIM-*.md` を生成して `inbox/` へ投函。**Hub全域走査による未使用連番一意採番 (PAT-SYS-006)**。 |
| **PHASE 8 / 整理** | `wiki-compactor` | 👑 Conductor | **Wiki整理・原票クラスタリング・Overlay圧縮**。Hub `inbox/` 原票集約および `LOCAL_FEEDBACK_RULES.md` 圧縮。 |
| **定量測定** | `dev-metrics-collector` | 👑 Conductor | **定量メトリクス集計 (4モジュール構成)**。**metrics/ パス集約 (PAT-SYS-003)**、**PROJECT_STATE 即時同期 (PAT-SYS-002)**、**フェーズ推移レポート生成 (PAT-SYS-004)**。 |
| **PHASE 8 / リリース** | `dev-git-release` | ⚙️ Conductor | **先頭サニタイズ処理**、Gitタグ付与（`vMAJOR.MINOR.PATCH`）、`main` への Squash Merge、Push、次期 `feature` 切り直し。 |
| **保守** | `dev-db-overwrite` | ⚙️ Conductor | 本番適用後DBのローカル同期、DBを含むコンテナの本番上書きデプロイ（二重防御ガードレール保護）。 |
| **共通監査** | `dev-doc-reviewer` | 🛡️ QA | `docs/` 配下の要件定義・設計書間の矛盾、誤植、相対パスリンク切れを多次元クロスチェックし自動修復。 |

---

## 🚦 開発パイプラインの実行フロー (PHASE 1〜8)

開発の具体的な手順、ユーザーが行うべきアクション、およびAIの自律動作の詳細は、[AI駆動システム開発手順書V2.5.md](./docs/設計書/Current/AI駆動システム開発手順書V2.5.md) および [AI駆動システム開発フェーズ定義書V2.5.md](./docs/設計書/Current/AI駆動システム開発フェーズ定義書V2.5.md) を参照してください。

```mermaid
flowchart TD
    P1["PHASE 1: プロジェクトの準備<br/>dev-phase1-setup"] --> P2["PHASE 2: 要件定義<br/>dev-phase2-requirements"]
    P2 -->|"★ ユーザー承認ゲート"| P3["PHASE 3: 基本設計書の作成<br/>dev-phase3-design"]
    P3 --> R3["PHASE 3 ゲート: 基本設計レビュー<br/>dev-review-arch (PASS)"]
    R3 -->|"★ ユーザー承認ゲート"| P4["PHASE 4: 開発環境とシステム構築<br/>dev-phase4-env-build"]
    P4 --> P5["PHASE 5: ウォークスルー動作確認<br/>dev-phase5-walkthrough"]
    P5 -->|"★ ユーザー承認ゲート"| R5["PHASE 5.5 ゲート: コード品質レビュー<br/>dev-review-code (CLEAN)"]
    R5 --> P6["PHASE 6: スルーテスト環境構築 & 自動テスト<br/>dev-phase6-testing"]
    P6 -->|"★ ユーザー承認ゲート"| R7["PHASE 7 ゲート: システム総合レビュー<br/>dev-review-system (APPROVED)"]
    P7["PHASE 7: 本番リリース作業<br/>dev-phase7-release"]
    R7 -->|"★ ユーザー承認ゲート"| P7
    P7 -->|"★ ユーザー承認ゲート"| P8["PHASE 8: ルール化と自己進化<br/>dev-phase8-rules"]
    P8 -->|"★ ユーザー知見裁定ゲート"| ACTIVE["本番稼働 (PRODUCTION_ACTIVE)"]
```

---

## 🛡️ コア不変原則 (Core Invariants: `INV-01` 〜 `INV-10`)

[CORE_INVARIANTS.md](./.agents/plugins/system-dev-pipeline/rules/CORE_INVARIANTS.md) により、いかなる改変や個別案件ルールであっても絶対に緩和・バイパスされない10の不変原則が定義されています。

| ID | 原則名 | 絶対不可侵の制約内容 |
| :--- | :--- | :--- |
| **`INV-01`** | **Single Writer 原則** | `PROJECT_STATE.md` の更新権限は 👑 `conductor` のみが保持し、サブエージェントによる直接編集を禁止する。 |
| **`INV-02`** | **責務分離とツール実行制限** | 📐 `architect` の `run_command` 禁止、🛡️ `qa-engineer` のアプリコード直接改変禁止、サブエージェントの Git/デプロイ/DB上書き/Docker全体起動停止の禁止。 |
| **`INV-03`** | **Anti-God Component / Module 制限** | フロントエンド 1 コンポーネントファイル最大 250 行制限、バックエンド 1 モジュールファイル最大 400 行制限（DTO分離必須）の厳守。 |
| **`INV-04`** | **本番モックOFF・直書きモック禁止** | コンポーネント内のダミーデータ直書き禁止（MSW 集約必須）、および本番ビルド時の `VITE_ENABLE_MOCK=false` 二重防御の厳守。 |
| **`INV-05`** | **Alembic 厳格運用・生SQL禁止** | 手動 DDL（生 SQL）によるテーブル作成・変更を禁止し、SQLAlchemy ORM と Alembic マイグレーションによる確定管理を徹底する。 |
| **`INV-06`** | **IAP JWT 検証・平文排除・非対話CLI保護** | 本番認証検証の強制、シークレット平文コミット禁止、外部 CLI 実行時の `--quiet` 等非対話フラグ強制・`2>/dev/null` 禁止・バックグラウンド待機時の `schedule` タイマー保護。 |
| **`INV-07`** | **3大レビューゲート必須通過** | 基本設計（`dev-review-arch`）・コード品質（`dev-review-code`）・システム総合（`dev-review-system`）の合格なしに次フェーズへ進行することを禁じる。 |
| **`INV-08`** | **自律修復ループの上限保護** | テスト失敗や不整合の放置を禁じるとともに、無限ループ防止のため自律修復は最大 5 回上限を維持する。 |
| **`INV-09`** | **Context Isolation とナレッジ境界** | Tier 1（案件固有仕様）の環境共通領域への持ち出し禁止、プロンプトへの生 Wiki 履歴注入禁止、およびルール本文（State）への履歴ID（Lineage）混入禁止。 |
| **`INV-10`** | **ドキュメント内相対パス強制** | Markdown 設計文書・仕様書内のファイルリンクに絶対パス（`file:///` 等）を使用することを禁止し、必ず対象ファイル間の相対パスを使用する。 |

---

## 📚 正本設計ドキュメント一覧（`docs/設計書/Current/`）

開発・適用の唯一の正（Single Source of Truth）として `docs/設計書/Current/` 配下で管理されている設計書群（全10文書）です。

- [V2.5改変計画書.md](./docs/設計書/Current/V2.5改変計画書.md) - V2.5 正式改訂計画書
- [セマンティックバージョニング仕様書.md](./docs/設計書/Current/セマンティックバージョニング仕様書.md) - バージョニング統一仕様書
- [AI駆動システム開発フェーズ定義書V2.5.md](./docs/設計書/Current/AI駆動システム開発フェーズ定義書V2.5.md) - ライフサイクルフェーズ定義正本
- [AI駆動システム開発手順書V2.5.md](./docs/設計書/Current/AI駆動システム開発手順書V2.5.md) - ユーザー＆AI協調開発実践手順書
- [エージェント設計書V2.5.md](./docs/設計書/Current/エージェント設計書V2.5.md) - 5大エージェント協調モデル仕様書
- [レビューシステム設計書V2.5.md](./docs/設計書/Current/レビューシステム設計書V2.5.md) - 3大レビュー＆3段階意味的監査仕様書
- [状態管理機構設計書V2.5.md](./docs/設計書/Current/状態管理機構設計書V2.5.md) - PROJECT_STATE 状態遷移仕様書
- [定量測定・フィードバック設計書V2.5.md](./docs/設計書/Current/定量測定・フィードバック設計書V2.5.md) - 定量測定エンジン・評価指標仕様書
- [ProfileA詳細設計書.md](./docs/設計書/Current/ProfileA詳細設計書.md) - Profile A (Cloud Run + Litestream run + SQLite) 設計仕様書
- [ProfileD詳細設計書.md](./docs/設計書/Current/ProfileD詳細設計書.md) - Profile D (Tauri v2 + Desktop + temp_db) 設計仕様書

※過去バージョンの設計文書は `docs/設計書/v2.4/`, `docs/設計書/V2.3/` 配下等にアーカイブ退避されています。

---

## 📄 ライセンス

MIT License
