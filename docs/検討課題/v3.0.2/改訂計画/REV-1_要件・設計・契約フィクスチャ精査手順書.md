# REV-1: 要件・設計・契約フィクスチャ精査手順書 (v3.1.0)

- **改訂依頼番号**: `v3.1.0` (`PLAN-V310-001`)
- **フェーズ**: `REV-1` (6段階標準改訂パイプライン 第1段階)
- **親計画書**: [00_v3.1.0改訂基本計画書.md](./00_v3.1.0改訂基本計画書.md)
- **親検討文書**: [パイプライン死角分析に対する客観的検証と構造的再設計方針報告書](../パイプライン死角分析に対する客観的検証と構造的再設計方針報告書.md)

---

## 1. フェーズ目的

先行報告書で策定された「ブラックボックス実動不変条件（Live Readiness Invariant）の確立」と「環境適応耐性（Core-Absorbed Resilience）のスケルトン標準化」に関する差分要件定義（`[REQ-*]`）および基本設計仕様を確定し、スクリプト改修・スケルトン改修・規約更新の整合性を精査する。

---

## 2. 実施タスクリスト

- [x] **T1-1: 差分要件の定義と採番 (`[REQ-*]`)**
  - 以下の3大要件を定義し、要件定義書および本計画に反映する：
    - `[REQ-F-310-01]`: `verify-review-readiness` による完全分離サブプロセスでのバックエンド一時起動、および実DBクエリを伴う Deep Health HTTP プローブ（HTTP 200 OK・スキーマ一致）の機械検証・ハード遮断。
    - `[REQ-F-310-02]`: 共通スケルトンにおける `Smart Database URL & Path Resolver`（ホスト/コンテナ自動判定・ディレクトリ自動生成）および FastAPI `lifespan` での起動時フェイルファスト検証の実装。
    - `[REQ-F-310-03]`: テストステージ体系の 3ステージ統合（Stage 1: Unit & Contract / Stage 2: Readiness Live Probe / Stage 3: Full-Stack E2E）および「ホワイトボックス構文規制からブラックボックス実動不変条件へのパラダイムシフト」に伴う規約体系改訂。
- [x] **T1-2: 改修スクリプトおよびスケルトンの差分設計**
  - **`state_manager.py` (Live Probe エンジン)**:
    - サブプロセス起動制御ロジックの設計（ポート自動割当 / 衝突回避、タイムアウト 15 秒保護、確実なプロセス終了クリーンアップ）。
    - Deep Health Probe リクエストロジック（`urllib.request` または `httpx` による GET リクエスト、ステータス 200、レスポンス JSON の検証）。
    - 起動失敗時の `stderr` キャプチャとコンソール表示ロジックの設計。
  - **共通スケルトン (`skeletons/common/backend/`)**:
    - `app/core/config.py`: `resolved_database_url` プロパティの設計（`/app/data` 不在時の相対パス解決と `mkdir` 自動生成）。
    - `app/core/db.py`: エンジン生成の統一。
    - `app/main.py`: `lifespan` 起動フックでの DB 接続確認（`SELECT 1`）、および `/api/health?deep=true` エンドポイント設計。
  - **規約・運用基準書**:
    - `rules/AGENTS.md`、`templates/システム改訂運用基準書.md` の改定設計。
- [x] **T1-3: 基本設計レビュー (Approval Gate)**
  - 基本設計差分をレビューし、`traceability_checker.py --mode design` が 100% PASS することを確認する。

---

## 3. 完了判定条件（Exit Criteria）

- 差分要件（`REQ-F-310-01`〜`03`）が確定し、基本設計仕様が一意に定まっていること。
- 基本設計レビュー（`dev-review-arch`）が `PASS` であること。
