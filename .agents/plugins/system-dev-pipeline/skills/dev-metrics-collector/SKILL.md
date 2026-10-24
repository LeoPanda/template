---
name: dev-metrics-collector
description: "開発プロセスにおける定量メトリクス（Token/時間/ツール/レビュー/テスト）を機械集計し、健全性スコアおよび診断レポートを出力するスキル。"
---

# 定量測定・メトリクス集計 (dev-metrics-collector) スキル V2.4

- **主担当エージェント**: 👑 プロジェクトコンダクター (`conductor`) (Model: `pro`)
- **適用契機**: 各フェーズ完了時、改訂ターン完了時、PHASE 8 総合診断
- **正本設計書**: [docs/設計書/Current/定量測定・フィードバック設計書V2.4.md](../../../../../docs/設計書/Current/定量測定・フィードバック設計書V2.4.md)

---

## 1. 概要と実行方針

本スキルは、Antigravity 会話トランスクリプト（`transcript.jsonl`）およびワークスペース成果物（Git、レビュー報告書、Wiki）から、**100% 決定論的かつ機械的にデータを集計**し、総合健全性スコア（100点満点・Grade S〜Critical）および診断レポートを出力します。

LLM による手作業での推測・捏造（ハルシネーション）を完全に排除するため、**必ず専用の Python スクリプト（Profile E 準拠 / Zero-Dependency）を実行して集計を行ってください。**

---

## 2. 実行手順

### Step 1: 集計スクリプトの実行

コンダクターは、ローカルまたはグローバルのプラグインディレクトリを自動解決し、以下の標準コマンドシーケンスを実行してください。

```bash
# 基本実行: プロジェクトに紐づく過去の全会話セッションを通算集計 (ローカル/グローバル自動解決)
PLUGIN_DIR="$([ -d "./.agents/plugins/system-dev-pipeline" ] && echo "./.agents/plugins/system-dev-pipeline" || echo "${HOME}/.gemini/config/plugins/system-dev-pipeline")"

python3 "${PLUGIN_DIR}/skills/dev-metrics-collector/scripts/metrics_collector.py"
```

#### 用途別実行オプション
- **直近の 1 セッションのみを集計したい場合**:
  ```bash
  python3 "${PLUGIN_DIR}/skills/dev-metrics-collector/scripts/metrics_collector.py" --single-session
  ```
- **過去プロジェクト（V2.3以前等）でトランスクリプトがない場合の遡及分析**:
  ```bash
  python3 "${PLUGIN_DIR}/skills/dev-metrics-collector/scripts/metrics_collector.py" --retroactive
  ```

---

### Step 2: 出力成果物の確認

スクリプトにより、以下の成果物が自動生成されます：
1. **プロジェクト統合サマリJSON**:
   - `docs/plans/metrics/development-metrics-summary.json`
   - 12 指標および 4 大カテゴリスコアが格納された機械可読データ。
2. **総合健全性診断レポートMarkdown**:
   - `metrics/system_health_report.md`
   - 総合グレード、トークン消費内訳、ツール呼出頻度、レビュー合否実績が整理された人間可読レポート。

コンダクターはレポートの内容を読み込み、総合スコアと特記事項（ボトルネックや改善候補）を確認します。

---

### Step 3: PHASE 8 およびユーザーへの完了報告

集計完了後、コンダクターは以下の標準フォーマットでユーザーに結果サマリを報告してください。

```markdown
### 📊 定量測定・メトリクス集計サマリ (PHASE 8)

- **総合健全性グレード**: **{Grade}** ({Total_Score} / 100 点)
- **分析モード**: {Standard (Multi-Session) / Retroactive}
- **通算トークン消費**: {Total_Tokens:,} Tokens (キャッシュ読込: {Cache_Tokens:,} Tokens)
- **メインコンテキスト消費率**: {Context_Usage}%
- **ツール呼出総数 / 重複率**: {Tool_Calls} 回 / {Duplicate_Rate}%
- **レビュー初回合格率**: {Review_Pass_Rate}% (指摘密度: {Defect_Density} 件/100LOC)
- **Wiki パターン蓄積**: Tier 1: {Local_Wiki} 件 / Tier 2: {Univ_Wiki} 件

詳細な診断レポートは `metrics/system_health_report.md` をご確認ください。
```
