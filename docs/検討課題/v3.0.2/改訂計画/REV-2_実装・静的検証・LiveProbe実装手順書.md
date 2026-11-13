# REV-2: 実装・静的検証・LiveProbe実装手順書 (v3.1.0)

- **改訂依頼番号**: `v3.1.0` (`PLAN-V310-001`)
- **フェーズ**: `REV-2` (6段階標準改訂パイプライン 第2段階)
- **親計画書**: [00_v3.1.0改訂基本計画書.md](./00_v3.1.0改訂基本計画書.md)
- **前フェーズ**: [REV-1_要件・設計・契約フィクスチャ精査手順書.md](./REV-1_要件・設計・契約フィクスチャ精査手順書.md)

---

## 1. フェーズ目的

REV-1 で策定された設計仕様に基づき、`state_manager.py` への Live Invariant Probe エンジン実装、共通スケルトン（`skeletons/common/backend/`）への環境適応・フェイルファスト機構の実装、規約ドキュメントの改訂、およびコミット前ハードゲート（`harness_guard.py --all`）の完全通過を達成する。

---

## 2. 実施タスクリスト

- [x] **T2-1: `scripts/state_manager.py` の Live Invariant Probe 改修**
  - `verify-review-readiness` サブコマンドに、バックエンドサーバー一時起動および Deep Health Probe ロジックを実装する：
    - 一時ポート（8999 等）の空き状況確認、バックグラウンドでの `subprocess.Popen` 起動。
    - 最大 15 秒間のポーリング（1 秒間隔）で `http://127.0.0.1:8999/api/health?deep=true` に HTTP GET。
    - レスポンス 200 OK かつ JSON 妥当性の確認。
    - 成功・失敗を問わず、テストプロセス終了時に必ず `process.terminate()` または `process.kill()` を実行する `finally` 句による確実なプロセス回収。
    - 異常終了時は `process.stderr.read()` のエラーログを出力し、`sys.exit(1)` でハード遮断。
- [x] **T2-2: 共通スケルトン (`skeletons/common/backend/`) の環境耐性改修**
  - `app/core/config.py`:
    - `Settings` クラスに `resolved_database_url` プロパティを追加。
    - SQLite パスが `/app/data/` でかつ実在しない場合、プロジェクトルート直下の `data/` へフォールバックし、ディレクトリを自動作成（`mkdir(parents=True, exist_ok=True)`）。
  - `app/core/db.py`:
    - `create_engine(settings.resolved_database_url, ...)` を使用するように改修。
  - `app/main.py`:
    - FastAPI `lifespan` 内で `engine.connect()` による初期DB疎通確認を実装（Fail-Fast）。
    - `/api/health` エンドポイントを拡張し、`?deep=true` 時は `SELECT 1` を実行して健全性を確認するロジックを実装。
- [x] **T2-3: スケルトンスクリプトへの同報同期**
  - `scripts/state_manager.py` の変更を `skeletons/common/scripts/state_manager.py` へ完全コピー同期する。
- [x] **T2-4: 規約ドキュメント・運用の改訂**
  - `.agents/plugins/system-dev-pipeline/rules/AGENTS.md`:
    - §2 コンダクター責務、§4.1 コア規範に「ブラックボックス実動不変条件（Live Readiness Invariant）」および「環境適応耐性（Core-Absorbed Resilience）」を追加。
    - §4.1 Testing Gate を「洗練された 3ステージ体系」へ書き換え。
  - `templates/システム改訂運用基準書.md`:
    - REV-3 完了条件および REV-4 前ゲートにおける Live Invariant Probe の必須通過を明記。
- [x] **T2-5: コミット前静的検証 (Hard Gate)**
  - `python3 scripts/harness_guard.py --all` を実行し、全規約（形式、行数、モック混入、文書衛生等）違反 0 件（PASS）を確認する。

---

## 3. 完了判定条件（Exit Criteria）

- `state_manager.py`、共通スケルトン、規約文書の改修が完了していること。
- `skeletons/common/scripts/` への同期が完了していること。
- `python3 scripts/harness_guard.py --all` がオールクリア（PASS）であること。
