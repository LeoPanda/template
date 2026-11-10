---
name: dev-phase2-requirements
description: "PHASE 2 要件定義書を作成・精査・清書するためのスキル。2.5層プロファイル体系 (Core Profile A〜E ＋ Capability Traits) の選定ディシジョンツリー・適合性診断・2択提案、定常コア規範の非機能要件自動バインド、サブ要件ID細分化を実施する。"
---

# PHASE 2: 要件定義書の作成および清書

- **主担当エージェント**: 📐 設計・立案スペシャリスト (`architect`) (Model: `pro`)
- **委譲元 / 統括**: 👑 プロジェクトコンダクター (`conductor`)
- **承認ゲート**: 👤 ユーザーによる明示的承認必須

本スキルは、`docs/設計書/Current/要件定義書.md` の精査・詳細化および清書を支援・実行します。

---

## 作業手順

1. **ドキュメントの読み込み**:
   - `docs/設計書/Current/要件定義書.md` および関連ドキュメントを読み込んでください。
2. **2.5層プロファイル体系の適用と選定**:
   - **第1層 (定常的コア設計規範)**: `rules/AGENTS.md` に定める定常コア規範（2段階行数制限、型同期、Pydantic Settings、Aware UTC、CI、Contract-First MSW、O(1)描画キャッシュ等）を非機能要件欄に自動バインドします。
   - **第2層 (Core Profile A〜E ＋ Capability Traits 選定)**:
     - ディシジョンツリーに基づき Core Profile（A〜E）を選定し、複合アプリケーション固有の検証要件に応じて **Capability Traits**（`+trait:local-api`, `+trait:media-export`, `+trait:frame-render`, `+trait:external-cli`, `+trait:dual-mode-workspace`）を追加バインドします。
     - 主案と代替案の2択を提示してユーザー合意を形成します。
3. **要件定義書の清書・構造化 & サブ要件ID採番**:
   - 目的、システムの概要、2層プロファイル体系、機能要件、非機能要件、外部インターフェース要件、制約事項について具体的に清書してください。
   - 機能要件は大きな単位（`[REQ-F01]`）にとどまらず、テスト可能な粒度までサブ要件ID（`[REQ-F01-01]`, `[REQ-F01-02]` 等）を細分化して付与してください。
4. **レビューと未決事項（Open Questions）の抽出**:
   - 曖昧な仕様やユーザー確認が必要な事項がある場合は、標準完了サマリの「残課題 / Open Questions」に明記してください。
5. **標準完了サマリの返却 (Single Writer原則)**:
   - 作業完了後、コンダクターに対して完了サマリを返送してください。コンダクターが `python3 scripts/state_manager.py complete-task --id P2-T01` を実行してタスクを完了し、ユーザー承認ゲートを提示します。承認後は `python3 scripts/state_manager.py record-approval --phase PHASE_2` および `python3 scripts/state_manager.py set-phase PHASE_3_DESIGN` を実行します。

---

## 標準完了サマリ返却フォーマット

```markdown
## 作業完了サマリ
- **担当エージェント**: architect
- **実施フェーズ / タスク**: PHASE 2 要件定義
- **ステータス**: SUCCESS / PENDING_USER_INPUT / FAILED
- **選定システム展開プロファイル**: Profile A (サーバーレス極小コストWeb型) / 等
- **生成・更新ファイル一覧**:
  - docs/設計書/Current/要件定義書.md
- **設計の要点・特記事項**:
  - [定常コア9項目のバインド状況、プロファイル適合性診断根拠、サブ要件ID細分化状況]
- **💡 獲得した知見・落とし穴 (Lessons Learned)**:
  - **事象**: [発生した課題・落とし穴（あれば、なければ「特になし」）]
  - **対策**: [回避策・推奨ルール]
  - **仕分け推奨**: Tier 1 (プロジェクト固有) / Tier 2 (全プロジェクト共通)
- **残課題 / Open Questions**:
  - [ユーザー確認が必要な事項（あれば）]
```
