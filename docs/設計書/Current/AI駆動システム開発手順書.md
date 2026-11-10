# AI駆動システム開発手順書（軽量・実行契約駆動・6段階改訂パイプライン準拠版）

文書バージョン: 3.0.1  
改定日: 2026-11-10  
対象バージョン: AI駆動システム開発ライフサイクルテンプレート V3.0.1 (`APP_VERSION=3.0.1`)  
ステータス: 正式改訂版 (Current 正本)  
関連文書:
- [AI駆動システム開発フェーズ定義書.md](./AI駆動システム開発フェーズ定義書.md)
- [定量測定・フィードバック設計書.md](./定量測定・フィードバック設計書.md)
- [ProfileA詳細設計書.md](./ProfileA詳細設計書.md)
- [ProfileD詳細設計書.md](./ProfileD詳細設計書.md)
- [レビューシステム設計書.md](./レビューシステム設計書.md)
- [エージェント設計書.md](./エージェント設計書.md)
- [状態管理機構設計書.md](./状態管理機構設計書.md)

---

## 1. はじめに

### 1.1 本書の目的
本書は、ユーザー（開発者・プロダクトオーナー）が `system-dev-pipeline` を利用して、迷うことなくスムーズにシステム開発を推進できるようにするための**実践的オペレーションガイド**である。

`project_state.json` / `PROJECT_STATE.md`（プロジェクト進行状態管理票）に定義されたフェージング（新規開発 PHASE 1〜8、および本番リリース後の継続改訂管理 `REV-1`〜`REV-6`）と作業工程をベースに、**「各フェーズでユーザー自身が行うべきこと（User Action）」** を明確に示し、その裏で **「AI（コンダクターおよび専門サブエージェント）が自律実行する作業内容（AI Execution）」** を要約・可視化して作業工程の流れを説明する。

### 1.2 5大エージェント協調体制と役割分担 (V3.0.0)
本パイプラインでは、以下の役割分担に基づいて作業が自律推進される。ユーザーは基本的に **メインエージェントである「👑 プロジェクトコンダクター」と対話するだけ** で全工程をコントロールできる。

| エージェント | 役割と責務 | 主な担当作業 |
| :--- | :--- | :--- |
| 👑 **コンダクター** (`conductor`)<br>*[メインエージェント]* | **プロジェクト進行管理・統括**<br>・`scripts/state_manager.py` 一元更新（Single Writer）<br>・標準コマンドシーケンス＆Hard Gate統括実行<br>・Docker/Git/デプロイ専任実行<br>・REV-4 実機レビュー要請・改修統括 | ユーザーとの対話窓口、サブエージェントへの作業委譲、環境構築、Git運用、リリース作業、台帳自動同期、自律昇格（Elevation） |
| 📐 **アーキテクト** (`architect`)<br>*[専門サブエージェント]* | **要件定義・アーキテクチャ・基本設計**<br>・2.5層プロファイル選定（Core A〜E ＋ Traits）<br>・要件ID採番 (`REQ-Fxx`/`REQ-NFxx`)<br>・4大基本設計書策定<br>・Executable Golden Fixtures配置<br>※ `run_command` は絶対禁止 | 要件定義書、技術要件定義書、テーブル定義書、ロジック仕様書、Golden Fixtures (`tests/fixtures/golden/`)、API仕様同期 |
| 💻 **バックエンドエンジニア** (`backend-engineer`)<br>*[専門サブエージェント]* | **サーバーサイド実装・マイグレーション**<br>・SQLAlchemy 2.0 / Alembic マイグレーション<br>・2段階行数制限 (400/550行) ＆ 空実装遮断<br>・OpenAPI型同期、Stage 1.5 実I/Oスモークテスト | FastAPI/Rust実装、マイグレーションコード、Stage 1.5 スモークテスト、単体テスト、構文チェック |
| 🎨 **UIデザイナー** (`ui-designer`)<br>*[専門サブエージェント]* | **UI/UX設計・フロントエンド実装**<br>・グランドデザイン新規格準拠<br>・Anti-God (250/350行) ＆ 空ハンドラ禁止<br>・Contract-First MSW、動的描画 O(1) キャッシュ | 画面仕様書、React/Vue/Tauriフロント実装、Tailwind明暗ペア指定、MSWモック制御 |
| 🛡️ **QAエンジニア** (`qa-engineer`)<br>*[専門サブエージェント]* | **品質監査・多次元レビュー・テスト自動化**<br>・Active QA プロトコル（プローブ永続化）<br>・3大レビューゲート監査<br>・RTMテスト関数直結バインド＆動的カバレッジ<br>・実結合E2E＆qa_runtime_evidence.json発行 | 基本設計レビュー、コード品質レビュー、システム総合レビュー、シナリオテスト、Wiki Maintainer、Semantic Auditor |

---

## 2. 全体作業フロー概要

```mermaid
flowchart TD
    subgraph P0_Sub["【事前準備】"]
        P0["事前準備 (Pre-Setup):<br/>プロジェクトフォルダ作成<br/>＆ Antigravityワークスペース追加"]
    end

    subgraph P1_3["【設計フェーズ】"]
        P1["PHASE 1: プロジェクトの準備<br/>(AIが基盤自動展開)"]
        P2["PHASE 2: 要件定義<br/>★ ユーザー承認ゲート 1"]
        P3["PHASE 3: 基本設計書の作成 & レビュー<br/>★ ユーザー承認ゲート 2"]
    end

    subgraph P4_5["【実装・検証フェーズ】"]
        P4["PHASE 4: 開発環境とシステム構築<br/>(AIがBE/FE並行実装・Git初期化)"]
        P5["PHASE 5: ウォークスルー動作確認<br/>★ ユーザーによる画面操作 & 承認ゲート 3"]
        P55["PHASE 5.5: コード品質レビュー<br/>(AIが250行/モック排除/DTO分離を検査)"]
    end

    subgraph P6_8["【テスト・リリース・自己進化フェーズ】"]
        P6["PHASE 6: スルーテスト自動実行<br/>★ ユーザー承認ゲート 4"]
        P7["PHASE 7: 本番リリース作業<br/>★ ユーザー承認ゲート 5"]
        P8["PHASE 8: ルール化・知見自己進化<br/>★ ユーザー知見裁定ゲート (ask_question)"]
    end

    P0 --> P1 --> P2 --> P3 --> P4 --> P5 --> P55 --> P6 --> P7 --> P8
```

---

## 3. 各フェーズの開発手順（新規開発 PHASE 1〜8）

### 3.0 事前準備: プロジェクトフォルダの作成とAntigravityワークスペース設定 (Pre-Setup)
新規にシステム開発をスタートする際、**PHASE 1 の初期化コマンドを実行する前に、ユーザー自身がローカルPC上で新規プロジェクト用の作業ディレクトリ（フォルダ）を用意し、Antigravity のワークスペースとして開く（追加する）必要があります。**

#### 👤 ユーザーが行うべきこと (User Action)
1. **新規プロジェクト用フォルダの作成**:
   ```bash
   mkdir -p ~/workspace/my-new-app
   cd ~/workspace/my-new-app
   ```
2. **Antigravity でプロジェクトフォルダを開く（ワークスペース追加）**:
   メニューから `File` > `Open Folder...` を選択し、上記フォルダを開きます。
3. **プラグインの確認**:
   Antigravity 上で `system-dev-pipeline` プラグインが有効であることを確認します。
4. **新規チャットの開始**:
   Antigravity 上で新規チャットセッションを開始します。

---

### 3.1 PHASE 1: プロジェクトの準備 (Project Setup)
- **ユーザー指示**: 「PHASE 1 プロジェクトの準備を開始してください。」
- **AI自律実行**: 静的スケルトン展開、`.env` 初期化、`PROJECT_STATE.md` 生成、Knowledge Hub 未処理原票確認。

### 3.2 PHASE 2: 要件定義 (Requirements Definition)
- **ユーザー指示**: 「PHASE 2 要件定義を開始してください。」
- **AI自律実行**: プロファイル（Profile A〜E）選定、`要件定義書.md` 策定。
- **承認ゲート 1**: ユーザーによる要件定義書・選定プロファイルの承認。

### 3.3 PHASE 3: 基本設計 (Basic Design)
- **ユーザー指示**: 「PHASE 3 基本設計を開始してください。」
- **AI自律実行**: 4大基本設計書策定、ドキュメント相互整合性チェック、基本設計レビュー（`dev-review-arch`）。
- **承認ゲート 2**: ユーザーによるレビュー結果（`PASS` / `CONDITIONAL PASS`）の承認。

### 3.4 PHASE 4: 開発環境構築 & システム実装
- **ユーザー指示**: 「PHASE 4 開発環境構築とシステム実装を開始してください。」
- **AI自律実行**: `dev-git-init` による Git 初期化、BE/FE 並行実装、標準コマンドシーケンス（Alembic, Codegen, Lint, Pytest）、コンテナビルド・起動。

### 3.5 PHASE 5: ウォークスルー検証 & コード品質レビュー
- **ユーザー指示**: 「PHASE 5 ウォークスルー検証を開始してください。」
- **AI自律実行**: モック有効/実結合両モード検証（Fail-Fast 遵守）、API 仕様書同期、`dev-review-code` による 250行制限・直書きモック排除・DTO 分離監査。
- **承認ゲート 3**: ユーザーによるウォークスルー動作およびコード品質レビュー（`CLEAN`）の承認。

### 3.6 PHASE 6: 結合・シナリオテスト & 自律修復
- **ユーザー指示**: 「PHASE 6 シナリオテストを実行してください。」
- **AI自律実行**: シナリオテスト自動実行、自律修復ループ（最大5回）、Profile D での一時実ファイルDB動的プロビジョニング（`temp_db` / PAT-TEST-001）、Wiki Maintainer による RCA 記録。
- **承認ゲート 4**: ユーザーによるテスト成功率 100% の承認。

### 3.7 PHASE 7: 本番リリース (Production Release)
- **ユーザー指示**: 「PHASE 7 本番リリース作業を開始してください。」
- **AI自律実行**: `本番適用作業手順書.md` 策定、`dev-review-system` 総合レビュー（Profile A では正規スーパーバイザー起動 `exec litestream replicate ... -exec` 確認）、本番デプロイ実行（`--quiet` ＋ `schedule` 監視）。
- **承認ゲート 5**: ユーザーによる本番稼働確認の承認。

### 3.8 PHASE 8: ルール化と Central Knowledge Hub 自己進化 (Knowledge & Handover)
- **ユーザー指示**: 「dev-phase8-rules スキルを実行し、メトリクス集計、知見の Central Knowledge Hub 投函、および Git 本番リリースを実行してください。」
- **AI自律実行**:
  1. **メトリクス集計 (`dev-metrics-collector`)**:
     - 4モジュールエンジンにより、`metrics/system_health_report.md`、`metrics/development_phase_report.md`、`metrics/development-metrics-summary.json` を一括出力（PAT-SYS-003, 004）。
  2. **`PROJECT_STATE.md` 定量サマリ即時同期 (PAT-SYS-002)**:
     - 診断レポートの主要数値を `PROJECT_STATE.md` の「プロジェクト定量メトリクスサマリ」へ即時反映し、ヘッダー更新日時を更新。
  3. **Wiki 集約と原票投函 (`wiki-proposer`)**:
     - `./wiki/patterns/universal/` から標準化知見原票（`CLAIM-*.md`）を生成。
     - **Knowledge Hub 全域を走査して未使用最新連番を採番 (PAT-SYS-006)**。
  4. **3段階意味的整合性監査**:
     - QAが新・複合検証ゲート Gate 1〜4（Invariants、矛盾、過剰適合排除、純度＆行数バジェット、**pattern_id 重複衝突排除**）を実行。
  5. **知見昇格裁定**: `ask_question` モーダルによるユーザー承認。
  6. **Local Overlay 反映**: `pipeline-reconciler.sh`（`reconciler_core.py`）により `LOCAL_FEEDBACK_RULES.md` をクリーン再生成。
  7. **Git 本番リリース (`dev-git-release`)**:
     - 先頭サニタイズ処理を経て `git tag "v1.0.0"` を付与し、`main` へ Squash Merge して Push。
     - 次期改訂用の `feature` ブランチを新規作成。
  8. **改訂運用ルールの配備 (`dev-phase8-rules`)**: `PROJECT_STATE.md` を `PRODUCTION_ACTIVE` へ移行。

---

## 4. 本番リリース後のシステム改訂手順 (REVISION: REV-1 〜 REV-6)

本番リリース（PHASE 8 完了）以降の追加開発・バグ修正は、[システム改訂運用基準書.md](../../../.agents/plugins/system-dev-pipeline/templates/システム改訂運用基準書.md) に基づき以下の6段階改訂サイクルで安全に実施します。

```mermaid
flowchart LR
    R1["REV-1: 要件・設計・契約精査<br/>(Golden Fixtures & RTM設計)"] --> R2["REV-2: 実装・静的検証<br/>(Stage 1.5 スモーク & Hard Gate HG-002)"]
    R2 --> R3["REV-3: テスト・実結合E2E<br/>(モックOFF & 証跡自動生成 & 衛生整理)"]
    R3 --> R4["REV-4: 実機レビュー・改修<br/>★ 事前検査PASS & ユーザー実機承認ゲート"]
    R4 --> R5["REV-5: 総合監査・ビルド<br/>(第2段階精査 & 3大レビュー & 成果物実在)"]
    R5 --> R6["REV-6: 知見昇格・リリース<br/>(Hub昇格 & 証跡検証 INV-QA-01 & Git Release)"]
```

1. **REV-1: 要件・設計・契約フィクスチャ精査**:
   - `state_manager.py start-revision` で起票。差分要件定義、4大基本設計書更新、`tests/fixtures/golden/` 配置、`dev-review-arch` PASS。
2. **REV-2: 実装・静的検証・Stage 1.5 スモーク**:
   - 2段階行数制限（250/350行、400/550行）、本番コードモック完全排除（`HG-002`）、空実装遮断（`HG-010`）、OpenAPI型同期、Stage 1.5 実I/Oスモークテスト、`harness_guard.py` PASS。
3. **REV-3: 自動テスト・実結合E2E・感覚センサー検証**:
   - テスト関数直結 RTM 検証、Stage 2 モックOFF実データ一気通貫E2E検証、感覚センサー検証、署名付き動的証跡（`metrics/qa_runtime_evidence.json`）自動生成。第1段階ドキュメント衛生・構造整理を実施し、`state_manager.py verify-review-readiness` PASS を確認。
4. **REV-4: 開発サーバー起動・ユーザー実機レビュー・対話的改修**:
   - 前提条件として事前検査ゲート（`state_manager.py verify-review-readiness`）PASS を確認後、実結合開発サーバーを起動し、ユーザーへ実機テストレビューを要請。対話的改修ループを経て、ユーザー実機承認（`state_manager.py record-approval --phase REV_4`）を記録。
5. **REV-5: 本番総合監査・成果物ビルド**:
   - 第2段階ドキュメント意味的相互整合性精査、コード品質レビュー（`dev-review-code`: CLEAN）、システム総合レビュー（`dev-review-system`: RELEASE APPROVED）、本番成果物の物理ビルド。
6. **REV-6: メトリクス・知見昇格・リリース**:
   - 定量メトリクス集計、Knowledge Hub 知見昇格、5大 Invariants Gate 自動検証（`state_manager.py complete-revision` による `[INV-QA-01]` 証跡実在＆改ざん検証）、`dev-git-release`。

---

## 5. ドキュメント改定履歴

| 対象バージョン | 改定日 | 改訂依頼番号 | 改定内容 |
| :--- | :--- | :--- | :--- |
| 2.6.0 | 2026-10-26 | - | 初回Current正本化 |
| 3.0.0 | 2026-11-10 | PLAN-V300-001 | 軽量・実行契約駆動パイプライン手順化 (Golden Fixtures、Stage 1.5/2、6段階改訂 REV-1〜REV-6、自律昇格) |
| 3.0.1 | 2026-11-10 | PLAN-V301-001 | 本番コードモック完全排除(HG-002)、署名付き動的証跡生成・状態台帳改ざん検証(REQ-F-301-02)、2段階ドキュメント精査・REV-4事前物理検査ゲート(REQ-F-301-03) |
