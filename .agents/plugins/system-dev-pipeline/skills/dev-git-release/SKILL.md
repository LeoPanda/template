---
name: dev-git-release
description: "GitHub本番リリースおよび開発ブランチ刷新スキル。featureブランチの変更をmainへmerge squashし、.envのバージョンを付与してcommit & pushを行い、featureブランチを削除・再作成する。"
---

# dev-git-release: GitHub本番リリースおよび開発ブランチ刷新スキル

- **主担当エージェント**: 👑 プロジェクトコンダクター (`conductor`)（決定論的ツール/スキル）

PHASE 8（本番リリースおよびドキュメント改訂管理ルール適用時）、および以後のシステム改訂完了時に発動し、変更を1コミットに集約してGitHubの `main` ブランチへ公開し、次期改訂用の `feature` ブランチを自動再作成してください。

## 実行前提条件
- プロジェクトディレクトリ直下で実行すること。
- GitHub接続用のSSH Keyが端末に設定済みであること。

---

## 作業手順

### 1. 開発ブランチおよび未コミット変更の確認
1. 現在のブランチが `feature` であることを確認してください。
   ```bash
   git branch --show-current
   ```
   もし `feature` でない場合は、作業中のブランチ状況を確認し、必要に応じて `git checkout feature` を行ってください。
2. 作業ツリー内の未コミット変更（新規・修正・削除ファイル）を確認してください。
   ```bash
   git status --porcelain
   ```
3. 未コミットの変更が存在する場合、それらをすべてステージングして自動コミットを実行してください。
   ```bash
   git add -A
   git commit -m "chore: save work before release"
   ```

### 2. バージョン番号の取得
1. `.env`（または `.env.production`）ファイルからバージョン番号を抽出してください。
   ```bash
   grep -E '^(APP_)?VERSION=' .env | cut -d '=' -f2 | tr -d '"' | tr -d "'"
   ```
2. バージョン番号が取得できない場合は、デフォルトとして `1.0.0` を設定するか、ユーザーにバージョン番号の確認を求めてください。

### 3. 本番ブランチへの統合（Squash Merge）とコミット
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

### 4. GitHubへのプッシュ（SSH接続）
1. GitHubのリモートリポジトリ（`origin`）へ `main` ブランチをプッシュしてください。
   ```bash
   git push -u origin main
   ```
   ※既にアップストリームが設定済みの場合は `git push origin main` を実行。

### 5. 開発ブランチの刷新（削除と再作成）
1. 旧 `feature` ブランチを削除してください。
   ```bash
   git branch -D feature
   ```
2. 最新の `main` ブランチを基点として、新しい `feature` ブランチを作成・チェックアウトしてください。
   ```bash
   git checkout -b feature
   ```

### 6. 状態管理（PROJECT_STATE.md）との同期
1. `PROJECT_STATE.md` のバージョン情報、現在のブランチ（`feature`）、および最新リリースコミットハッシュを記録・同期してください。
