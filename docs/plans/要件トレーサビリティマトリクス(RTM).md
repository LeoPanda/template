# 要件トレーサビリティマトリクス (RTM: Requirements Traceability Matrix)

- **生成ツール**: `scripts/traceability_checker.py` (V3.0.0 Executable Contract)
- **要件総数**: 3 件
- **総テストケース数**: 6 件 (うち異常系・境界値: 3 件, 異常系比率: 50.0%)
- **動的カバレッジ検証**: カバレッジファイル未検出 (スキップ)

| 要件ID | 分類 | 要件概要 | 基本設計反映 | テスト関数直結反映 | 充足ステータス |
| :--- | :---: | :--- | :--- | :--- | :---: |
| REQ-F-310-01 | Functional | [x] 差分要件定義書の策定（`` Live Probe、`[REQ-F-310-02]` 環境適応スケルトン、`[REQ-F-310-03]` 3ステージ体系統合） | AI駆動システム開発フェーズ定義書.md, AI駆動システム開発手順書.md, ProfileA詳細設計書.md, ProfileD詳細設計書.md, レビューシステム設計書.md | test_v310_pipeline.py:test_req_f_310_01_live_probe_abnormal_immediate_crash, test_v310_pipeline.py:test_req_f_310_01_live_probe_skip_when_no_backend | ✅ PASS |
| REQ-F-310-02 | Functional | [x] 差分要件定義書の策定（`[REQ-F-310-01]` Live Probe、`` 環境適応スケルトン、`[REQ-F-310-03]` 3ステージ体系統合） | AI駆動システム開発フェーズ定義書.md, ProfileA詳細設計書.md, ProfileD詳細設計書.md | test_v310_pipeline.py:test_req_f_310_02_smart_resolver_abnormal_validation, test_v310_pipeline.py:test_req_f_310_02_smart_resolver_fallback_and_mkdir | ✅ PASS |
| REQ-F-310-03 | Functional | [x] 差分要件定義書の策定（`[REQ-F-310-01]` Live Probe、`[REQ-F-310-02]` 環境適応スケルトン、`` 3ステージ体系統合） | AI駆動システム開発フェーズ定義書.md | test_v310_pipeline.py:test_req_f_310_03_abnormal_rejection_of_invalid_stages, test_v310_pipeline.py:test_req_f_310_03_three_stage_architecture_rule | ✅ PASS |
