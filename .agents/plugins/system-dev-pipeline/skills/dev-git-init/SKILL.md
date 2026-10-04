---
name: dev-git-init
description: "Git初期化および開発ブランチ作成スキル。Git運用基準書のdocs配下への配置、Gitの初期化、GitHub SSHリモートの設定、mainブランチでの基点コミット作成、およびfeatureブランチへの切り替えを行う。"
---

# dev-git-init: Git初期化および開発ブランチ作成スキル

- **主担当エージェント**: 👑 プロジェクトコンダクター (`conductor`)（決定論的ツール/スキル）

PHASE 4の環境構築およびシステム初期実装完了時に発動し、Git運用基準書の配置、Gitリポジトリの初期化と開発ブランチ（`feature`）の切り出しを安全に実行してください。

## 実行前提条件
- プロジェクトディレクトリ直下で実行すること。
- GitHub接続用のSSH Keyが端末に設定済みであること。

---

## 作業手順

### 1. Git運用基準書の配置
1. プロジェクトの `docs/Git運用基準書.md` が存在するか確認してください。
2. 未配置の場合、プラグインの `templates/Git運用基準書.md` をプロジェクトの `docs/Git運用基準書.md` へコピー・配置してください。

### 2. Gitリポジトリの初期化
1. カレントディレクトリが既にGitリポジトリであるかを確認してください。
   ```bash
   git rev-parse --is-inside-work-tree
   ```
2. 未初期化の場合、デフォルトブランチを `main` として初期化してください。
   ```bash
   git init -b main
   ```

### 3. GitHubリモート（SSH接続）の設定
1. リモート `origin` が既に設定されているか確認してください。
   ```bash
   git remote get-url origin
   ```
2. 未設定の場合：
   - システムのルートディレクトリ名（プロジェクト名）を取得してください（例: `basename "$PWD"`）。
   - GitHubのユーザー名/アカウント名を確認してください（`git config user.name` または SSH接続テスト `ssh -T git@github.com`、不明な場合はユーザーに確認）。
   - 以下の形式でSSH接続リモートを追加してください。
     ```bash
     git remote add origin git@github.com:<GitHub-Username>/<Project-Name>.git
     ```

### 4. 初期設定ファイルのステージングと基点コミット
1. `.gitignore` が適切に配置されているか確認してください（`.env`, `node_modules/`, `__pycache__/`, `.DS_Store` 等が除外対象になっていること）。
2. `docs/Git運用基準書.md` を含む初期のファイル群をステージングしてください。
   ```bash
   git add .
   ```
3. `main` ブランチ上で初期基点コミットを作成してください。
   ```bash
   git commit -m "feat: initial project setup"
   ```

### 5. 開発ブランチ `feature` の作成と移動
1. `main` ブランチから開発用ブランチ `feature` を作成・チェックアウトしてください。
   ```bash
   git checkout -b feature
   ```

### 6. 状態管理（PROJECT_STATE.md）との同期
1. `PROJECT_STATE.md` の「4. システム・インフラ・Git状態」に現在のブランチ（`feature`）、最新コミットハッシュ、リモートURLを記録してください。
