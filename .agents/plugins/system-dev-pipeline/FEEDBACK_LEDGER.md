# パイプライン知見適合・進化履歴台帳 (FEEDBACK_LEDGER.md)

本台帳は、`system-dev-pipeline` の Immutable Core に対して適合（統合・蒸留）されたすべての Tier 2 知見フィードバックの系譜（Lineage）を記録する正本である。
推論コンテキストの純度を保つため、`SKILL.md` や `AGENTS.md` 本文（State）にはパターンIDや障害経緯を一切記載せず、本台帳および `PIPELINE_MANIFEST.json` にて因果関係を一元管理する（旧 `skills/*/PURPOSE.md` を完全統合）。
なお、通常の開発フェーズ（PHASE 1〜7）を実行する推論エージェントは本ファイルを読み込まない（Context Isolation 原則の維持）。

---

## 1. 適合済みフィードバック一覧 (Adapted Knowledge Lineage)

| 適合Ver | Pattern ID | 原票 Claim ID / 発生元 | 統合種別 | 反映先ファイル & セクション | 蒸留・統合されたルール要約と背景動機 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **V2.3.0** | `PAT-SYS-001` | `CLAIM-20261017-legacy-PAT-SYS-001`<br>(`CLAIM-20261017-bicycle-log-PAT-SYS-001`) | `SUBSUMPTION`<br>(補強統合) | ・`rules/CORE_INVARIANTS.md` (`INV-06`)<br>・`rules/AGENTS.md` (§8.5)<br>・`agents/conductor.md` (§1.9)<br>・`skills/dev-phase7-release/SKILL.md` (§4) | **【改訂動機・背景】** PHASE 7 本番デプロイ検証において、`gcloud` コマンドを `--quiet` なし・`2>/dev/null` 付きで実行した結果、確認プロンプト（`(Y/n)?`）が不可視化されたままバックグラウンドタスク（`task-xxx`）で stdin 入力待ちハングを起こし、Reactive Wakeup が発火せず応答が途絶える事象が発生したため。<br>**【統合内容・効果】** ① 外部CLI実行時の非対話フラグ（`--quiet`, `--yes`, `patch -N` 等）明示指定の強制、② 診断・状態確認時の `2>/dev/null` による標準エラー破棄の禁止、③ バックグラウンド移行タスク待機時の `schedule` ワンショットタイマー（`DurationSeconds=60`, `TimerCondition="<task-id>"`）併用をコア規約およびデプロイ手順へ統合し、対話プロンプト起因のサイレント・ハング発生率を 0% に低減。 |
| **V2.3.0** | `PAT-DOC-001` | `CLAIM-20261018-system-dev-dashboard-PAT-DOC-001`<br>(`system-dev-dashboard`) | `SUBSUMPTION`<br>(包含・純化) | ・`skills/dev-phase1-setup/SKILL.md` (§5)<br>・`rules/AGENTS.md` (§10.5) | **【改訂動機・背景】** 初期セットアップ時に `templates/` 配下の旧設計文書雛形が `docs/` 直下に静的コピーされていたため、Profile 選定後の `docs/設計書/Current/` と二重存在・競合を起こし、AIエージェントの推論やドキュメント整合性チェッカー（`dev-doc-reviewer`）にノイズを発生させていたため。<br>**【統合内容・効果】** ① プロジェクト初期化（PHASE 1）における `docs/` 直下への静的設計文書雛形のコピーを廃止し、ディレクトリ構造（`docs/設計書/Current/`, `docs/検討課題/` 等）の作成のみに純化、② 設計文書はプロファイル確定後に `docs/設計書/Current/` 配下へ直接策定・配置する規約を明記し、二重管理と整合性エラーを根絶。 |
| **V2.4.0** | `PAT-002` | `CLAIM-20261018-obsidian-PAT-002`<br>(`Obsidian Vault (PKM)`) | `SUBSUMPTION`<br>(分離・純化) | ・`rules/AGENTS.md` (§6.3)<br>・`skills/wiki-maintainer/SKILL.md`<br>・`skills/wiki-proposer/SKILL.md` | **【改訂動機・背景】** 構文不正や絶対パス混入等の機械的バグを自然言語プロンプトに追記し続けることで、行数バジェット浪費と否定命令汚染が発生していたため。<br>**【統合内容・効果】** 系統A（決定論的バグ）はLinterやテストコード（Executable Specs）へ直接吸収し、系統B（セマンティック文脈判断）は30日以内N>=3回反復観測されたもののみをWikiパターンとして起票する2系統物理分離を確立。 |
| **V2.4.0** | `PAT-MOCK-001` | `CLAIM-20261020-system-dev-dashboard-PAT-MOCK-001`<br>(`system-dev-dashboard`) | `SUBSUMPTION`<br>(防御強化) | ・`rules/AGENTS.md` (§4.1 定常コア7)<br>・`skills/dev-phase5-walkthrough/SKILL.md`<br>・`skills/dev-review-system/SKILL.md` | **【改訂動機・背景】** 実結合モード（`VITE_ENABLE_MOCK=false`）において、APIやIPCのエラー時にモックデータへフォールバックしてしまい、不具合が不可視化・潜在化するリスクがあったため。<br>**【統合内容・効果】** 実結合モードにおけるサイレントモックフォールバックを厳格禁止し、エラー時は即座に例外をスローしてUI/ログに顕在化させるフェイルファスト原則を制度化。 |
| **V2.4.0** | `PAT-UI-001` | `CLAIM-20261020-system-dev-dashboard-PAT-UI-001`<br>(`system-dev-dashboard`) | `SUBSUMPTION`<br>(規格標準化) | ・`rules/AGENTS.md` (§4.1 定常コア8)<br>・`templates/画面仕様書.md` (§5.4)<br>・`agents/ui-designer.md`<br>・`skills/dev-review-code/SKILL.md` | **【改訂動機・背景】** コンポーネント内の文字色・背景色にダークモード前提の淡色・透過カラーが単独直書きされ、デイライト（ライトモード）での視認性が崩れる事象が発生したため。<br>**【統合内容・効果】** セマンティックデザイントークンまたはTailwindの明暗ペア（`dark:` 併記）の指定を必須化し、ダーク前提淡色カラーの単独直書きを禁止。 |
| **V2.4.0** | `PAT-REV-001` | `CLAIM-20261022-021248`<br>(`template`) | `SCOPED_BRANCH`<br>(スコープ明確化) | ・`templates/システム改訂ルール.md` (§2.3.3)<br>・`agents/conductor.md` (§1.5) | **【改訂動機・背景】** システム改訂ルール §2.3.3 の全ドキュメント共通改定履歴表の適用により、現在状態のインジケータである `PROJECT_STATE.md` に履歴表が追記され、肥大化・構造ノイズとなっていたため。<br>**【統合内容・効果】** `PROJECT_STATE.md` を改定履歴表の適用対象外とし、改訂ターンごとの履歴追記は `/revise-log/` および改訂レポートで一元管理する方針を明文化。 |
| **V2.4.0** | `PAT-CODE-001` | `CLAIM-20261022-system-dev-dashboard-PAT-CODE-001`<br>(`system-dev-dashboard`) | `SUBSUMPTION`<br>(構造分離) | ・`rules/AGENTS.md` (§4.1 定常コア1)<br>・`agents/backend-engineer.md`<br>・`skills/dev-review-code/SKILL.md` | **【改訂動機・背景】** バックエンドのハンドラー・Controller層にDTO構造体やパーサーが同居し、ファイル行数超過（400行制限違反）や直書きモック保持が発生していたため。<br>**【統合内容・効果】** DTOおよびパーサーを独立モジュールへ物理分離し、Controller層はオーケストレーションに専念させ、直書きモックを排除してDBアクセス層やヘルパーへ委譲する設計規約を確立。 |
| **V2.4.0** | `PAT-TEST-001` | `CLAIM-20261022-system-dev-dashboard-PAT-TEST-001`<br>(`system-dev-dashboard`) | `SCOPED_BRANCH`<br>(テスト整合性) | ・`rules/AGENTS.md` (§4.2 Profile D)<br>・`skills/dev-phase6-testing/SKILL.md`<br>・`docs/設計書/Current/ProfileD詳細設計書.md` | **【改訂動機・背景】** Profile D（Tauri/SQLite WAL）における結合テストでインメモリDBを使用した場合、WALモード並行性やファイルロック挙動を正確に検証できず、本番差異が発生するリスクがあったため。<br>**【統合内容・効果】** 一時ディレクトリ配下にUUID付き実ファイルDBを動的プロビジョニングし、マイグレーションとWAL並行性を本番同等に検証した上でアトミック破棄するテスト手順を規定。 |

---

## 2. 運用ルール

1. **State と Lineage の分離**:
   - 知見原票（`CLAIM-*.md`）を Immutable Core の `rules/AGENTS.md`、`agents/*.md`、`skills/*/SKILL.md` へ本流統合する際、対象ファイルの本文には純粋な行動規範のみを記述し、履歴ID（`PAT-*`, `CLAIM-*`）や背景エピソードは必ず本ファイル（`FEEDBACK_LEDGER.md`）および `PIPELINE_MANIFEST.json` に記録すること。
2. **Upgrade Reconciler との連動**:
   - 本台帳および `PIPELINE_MANIFEST.json` に登録された `pattern_id` / `claim_ids` は、新バージョン配布時に `scripts/pipeline-reconciler.sh --upgrade` によって参照され、各開発環境の `~/.gemini/knowledge-hub/active_claims/` から `archive/upstreamed/` への自動退役判定（パターンA: Fast-Path Upstreamed）に使用される。
