# パイプライン知見適合・進化履歴台帳 (FEEDBACK_LEDGER.md)

本台帳は、`system-dev-pipeline` の Immutable Core に対して適合（統合・蒸留）されたすべての Tier 2 知見フィードバックの系譜（Lineage）を記録する正本である。
推論コンテキストの純度を保つため、`SKILL.md` や `AGENTS.md` 本文（State）にはパターンIDや障害経緯を一切記載せず、本台帳および `PIPELINE_MANIFEST.json` にて因果関係を一元管理する（旧 `skills/*/PURPOSE.md` を完全統合）。
なお、通常の開発フェーズ（PHASE 1〜7）を実行する推論エージェントは本ファイルを読み込まない（Context Isolation 原則の維持）。

---

## 1. 適合済みフィードバック一覧 (Adapted Knowledge Lineage)

| 適合Ver | Pattern ID | 原票 Claim ID / 発生元 | 統合種別 | 反映先ファイル & セクション | 蒸留・統合されたルール要約と背景動機 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **V2.3.0** | `PAT-SYS-001` | `CLAIM-20261017-legacy-PAT-SYS-001`<br>(`CLAIM-20261017-bicycle-log-PAT-SYS-001`) | `SUBSUMPTION`<br>(補強統合) | ・`rules/CORE_INVARIANTS.md` (`INV-06`)<br>・`rules/AGENTS.md` (§8.5)<br>・`agents/conductor.md` (§1.9)<br>・`skills/dev-phase7-release/SKILL.md` (§4) | **【改訂動機・背景】** PHASE 7 本番デプロイ検証において、`gcloud` コマンドを `--quiet` なし・`2>/dev/null` 付きで実行した結果、確認プロンプト（`(Y/n)?`）が不可視化されたままバックグラウンドタスク（`task-xxx`）で stdin 入力待ちハングを起こし、Reactive Wakeup が発火せず応答が途絶える事象が発生したため。<br>**【統合内容・効果】** ① 外部CLI実行時の非対話フラグ（`--quiet`, `--yes`, `patch -N` 等）明示指定の強制、② 診断・状態確認時の `2>/dev/null` による標準エラー破棄の禁止、③ バックグラウンド移行タスク待機時の `schedule` ワンショットタイマー（`DurationSeconds=60`, `TimerCondition="<task-id>"`）併用をコア規約およびデプロイ手順へ統合し、対話プロンプト起因のサイレント・ハング発生率を 0% に低減。 |

---

## 2. 運用ルール

1. **State と Lineage の分離**:
   - 知見原票（`CLAIM-*.md`）を Immutable Core の `rules/AGENTS.md`、`agents/*.md`、`skills/*/SKILL.md` へ本流統合する際、対象ファイルの本文には純粋な行動規範のみを記述し、履歴ID（`PAT-*`, `CLAIM-*`）や背景エピソードは必ず本ファイル（`FEEDBACK_LEDGER.md`）および `PIPELINE_MANIFEST.json` に記録すること。
2. **Upgrade Reconciler との連動**:
   - 本台帳および `PIPELINE_MANIFEST.json` に登録された `pattern_id` / `claim_ids` は、新バージョン配布時に `scripts/pipeline-reconciler.sh --upgrade` によって参照され、各開発環境の `~/.gemini/knowledge-hub/active_claims/` から `archive/upstreamed/` への自動退役判定（パターンA: Fast-Path Upstreamed）に使用される。
