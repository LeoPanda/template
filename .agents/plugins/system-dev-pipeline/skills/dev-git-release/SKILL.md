---
name: dev-git-release
description: "GitHub本番リリースおよび開発ブランチ刷新スキル。featureブランチの変更をmainへmerge squashし、バージョンタグを付与してcommit & pushを行い、featureブランチを削除・再作成する（コンダクター専任）。"
---

# dev-git-release: GitHub本番リリースおよび開発ブランチ刷新スキル

- **主担当エージェント**: 👑 プロジェクトコンダクター (`conductor`) (専任実行)

PHASE 8（本番リリースおよびドキュメント改訂管理ルール適用時）、および以後のシステム改訂完了時に発動し、変更を1コミットに集約してGitHubの `main` ブランチへ公開し、次期改訂用の `feature` ブランチを自動再作成してください。

---

## 実行前提条件
- プロジェクトディレクトリ直下で実行すること。
- サブエージェントからの実行は厳格に禁止（コンダクター専任）。
- GitHub接続用のSSH Keyが端末に設定済みであること。

---

## 作業手順

### 1. 開発ブランチおよび未コミット変更の確認
1. 現在のブランチが `feature` であることを確認してください。
   ```bash
   git branch --show-current
   ```
2. 作業ツリー内の未コミット変更（新規・修正・削除ファイル）を確認してください。
   ```bash
   git status --porcelain
   ```
3. 未コミットの変更が存在する場合、それらをすべてステージングして自動コミットを実行してください。
   ```bash
   git add -A
   git commit -m "chore: save work before release"
   ```

### 2. バージョン番号の取得とサニタイズ (二重プレフィックス防止ガード)
1. `.env`（または `.env.production`）ファイルからバージョン番号を抽出し、先頭の `v` または `V` を除去してサニタイズしてください。
   ```bash
   RAW_VERSION=$(grep -E '^(APP_)?VERSION=' .env | cut -d '=' -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
   CLEAN_VERSION=$(echo "$RAW_VERSION" | sed -E 's/^[vV]+//')
   VERSION="${CLEAN_VERSION:-1.0.0}"
   ```
2. バージョン番号が取得できない場合は、デフォルトとして `1.0.0` を設定するか、ユーザーにバージョン番号の確認を求めてください。

### 3. リリース前ローカル CI 検証ゲート (Pre-Push CI Gate / Shift-Left Hard Gate)
`main` への統合およびプッシュを行う前に、リモート GitHub Actions CI と同等の全チェックをローカルで事前実行し、すべて PASS することを機械的に検証してください。1つでもエラーがある場合はリリースを中断し、原因を解消してください。

1. **バックエンド検証 (Ruff Lint, Mypy 型チェック, Pytest)**:
   ```bash
   if [ -d "backend" ]; then
     (cd backend && (ruff check . || ../.venv/bin/ruff check .) && (mypy app || ../.venv/bin/mypy app) && (pytest || ../.venv/bin/pytest))
   fi
   ```
2. **フロントエンド検証 (TypeScript 型チェック, プロダクションビルド)**:
   ```bash
   if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
     (cd frontend && npm run type-check && npm run build)
   fi
   ```
3. **Hard Gate ガードレール検証**:
   ```bash
   if [ -f "scripts/harness_guard.py" ]; then
     python3 scripts/harness_guard.py --all
   fi
   ```
※ 上記のいずれかが終了コード 1（失敗）となった場合は、**`main` へのチェックアウトおよびマージを即座に中断**し、エラー原因を解消してから本スキルを再実行してください。

### 4. 本番ブランチへの統合（Squash Merge）とコミット・タグ付与
1. 本番ブランチ `main` に切り替えてください。
   ```bash
   git checkout main
   ```
2. `feature` ブランチの全変更を1つに集約してステージングしてください（Squash Merge）。
   ```bash
   git merge --squash feature
   ```
3. バージョン番号を明記して本番リリース確定コミットを実行してください。
   ```bash
   git commit -m "Release v${VERSION}"
   ```
4. リリースタグを付与してください。
   ```bash
   git tag -a "v${VERSION}" -m "Release v${VERSION}"
   ```

### 5. GitHubへのプッシュ（SSH接続）
1. GitHubのリモートリポジトリ（`origin`）へ `main` ブランチおよびタグをプッシュしてください。
   ```bash
   git push -u origin main
   git push origin "v${VERSION}"
   ```

### 6. 開発ブランチの刷新（削除と再作成）
1. 旧 `feature` ブランチを削除してください。
   ```bash
   git branch -D feature
   ```
2. 最新の `main` ブランチを基点として、新しい `feature` ブランチを作成・チェックアウトしてください。
   ```bash
   git checkout -b feature
   ```

### 7. 状態管理（Single Writer 原則）との同期
1. `python3 scripts/state_manager.py complete-task --id P8-T02` を実行し、本番リリースの完了を状態台帳へ記録してください。
