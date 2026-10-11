---
name: dev-metrics-collector
description: "開発プロセスにおけるターン・フェーズ別の定量メトリクスを集計し、健全性スコアの算出および診断レポートを出力するスキル。"
---

# 定量測定・メトリクス集計 (dev-metrics-collector) スキル

- **主担当エージェント**: 👑 プロジェクトコンダクター (`conductor`) (Model: `pro`)
- **適用契機**: 各フェーズ完了時、改訂ターン完了時、PHASE 8 総合診断

---

## 1. 収集・集計対象メトリクス

1. **ターン別メトリクス (`metrics/turns/turn_{N}.json`)**:
   - ターン開始・終了時刻、経過時間（秒）
   - トークン消費量（Prompt / Completion）
   - ツール呼出回数（`run_command`, `write_to_file` 等）
   - エラー・リトライ発生回数
   - ※ `metrics/turns/` は一次データのため、`.gitignore` でGit管理から除外される。
2. **フェーズ別メトリクス (`metrics/phases/phase_{N}.json`)**:
   - フェーズ内総ターン数、所要時間
   - レビュー合否履歴および指摘件数（Critical / High / Medium）
   - テスト自動修復反復回数 (1〜5)
   - 獲得Wikiパターン件数 (Tier 1 / Tier 2)
3. **プロジェクト統合サマリ (`docs/plans/metrics/development-metrics-summary.json`)**:
   - 全フェーズを通じた総合所要時間、総合トークン消費
   - 1st Pass Test Pass Rate（初回テスト合格率）
   - レビュー合格率、手戻り回数

---

## 2. 処理手順

### Step 1: ターン/フェーズ データの収集とJSON出力
各フェーズ完了時に、該当フェーズ内の実行ログや完了サマリから実績値を抽出し、`metrics/phases/phase_{N}.json` を出力・更新する。

### Step 2: 健全性スコア (System Health Score) の算出
以下の4大カテゴリに基づいてスコア（各25点満点、計100点）およびグレード（A: 90+, B: 75-89, C: 60-74, D: <60）を算出する：
1. **プロセス効率性 (Process Efficiency)**: 計画工数・ターン数に対する実績比率
2. **レビュー品質 (Review Robustness)**: 3大レビューでの指摘消化率、手戻り回数
3. **テスト信頼性 (Test Reliability)**: シナリオテスト合格率、修復ループ収束速度
4. **知見蓄積度 (Knowledge Capitalization)**: Wikiパターンの蓄積数および昇格率

### Step 3: PHASE 8 総合健全性診断レポートの生成
PHASE 8 実行時、プロジェクト全体のメトリクスを統合した `metrics/system_health_report.md` を作成する。
- 総合グレード (Grade A〜D) とスコア内訳
- ボトルネックとなったフェーズの分析
- 次期開発または他プロジェクトへの改善推奨事項
