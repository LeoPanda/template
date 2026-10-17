#!/usr/bin/env bash
# ==============================================================================
# template-pipeline-sync: Global <-> Workspace パイプライン同期・診断スクリプト
# 対象スコープ: template プロジェクト専用 (.agents/skills/template-pipeline-sync/)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

WS_PLUGIN="${WORKSPACE_ROOT}/.agents/plugins/system-dev-pipeline"
WS_ROOT_RULES="${WORKSPACE_ROOT}/rules/AGENTS.md"
GLOBAL_PLUGINS_DIR="${HOME}/.gemini/config/plugins"
GLOBAL_PLUGIN="${GLOBAL_PLUGINS_DIR}/system-dev-pipeline"
BACKUP_BASE_DIR="${HOME}/.gemini/backups/system-dev-pipeline"
KNOWLEDGE_HUB_DIR="${HOME}/.gemini/knowledge-hub"
SYNC_STAMP_FILE="${WORKSPACE_ROOT}/.git/pipeline_sync_stamp"

SEC11_HEADER="## 11. パイプライン改訂作業におけるグローバル・ワークスペース同期規約"

# ------------------------------------------------------------------------------
# ヘルパー関数: ルート rules/AGENTS.md から共通部(第1〜10節)と固有部(第11節)を分離
# ------------------------------------------------------------------------------
extract_root_rules_common() {
  local target_file="$1"
  if [[ ! -f "$target_file" ]]; then
    return 0
  fi
  python3 - "$target_file" "$SEC11_HEADER" << 'PYEOF'
import sys, pathlib, re

path = pathlib.Path(sys.argv[1])
header = sys.argv[2]
text = path.read_text(encoding="utf-8")

if header in text:
    idx = text.index(header)
    prefix = text[:idx]
    # 直前の "---" セパレータを除去して末尾改行を1つに揃える
    prefix = re.sub(r'\n+---\n*$', '\n', prefix)
    sys.stdout.write(prefix)
else:
    sys.stdout.write(text)
PYEOF
}

extract_root_rules_sec11() {
  local target_file="$1"
  if [[ ! -f "$target_file" ]]; then
    return 0
  fi
  python3 - "$target_file" "$SEC11_HEADER" << 'PYEOF'
import sys, pathlib

path = pathlib.Path(sys.argv[1])
header = sys.argv[2]
text = path.read_text(encoding="utf-8")

if header in text:
    idx = text.index(header)
    sys.stdout.write(text[idx:])
PYEOF
}

# ------------------------------------------------------------------------------
# ヘルパー関数: プラグイン正本 rules/AGENTS.md をルート rules/AGENTS.md の共通部へ反映
# ------------------------------------------------------------------------------
sync_root_rules_from_plugin() {
  python3 - "$WS_PLUGIN/rules/AGENTS.md" "$WS_ROOT_RULES" "$SEC11_HEADER" << 'PYEOF'
import sys, pathlib

plugin_rules_path = pathlib.Path(sys.argv[1])
root_rules_path = pathlib.Path(sys.argv[2])
header = sys.argv[3]

plugin_text = plugin_rules_path.read_text(encoding="utf-8").rstrip() + "\n"
root_text = root_rules_path.read_text(encoding="utf-8") if root_rules_path.exists() else ""

if header in root_text:
    idx = root_text.index(header)
    sec11_text = root_text[idx:].rstrip() + "\n"
    combined = plugin_text + "\n---\n\n" + sec11_text
else:
    combined = plugin_text

root_rules_path.write_text(combined, encoding="utf-8")
PYEOF
}

# ------------------------------------------------------------------------------
# ヘルパー関数: グローバルプラグインのツリーハッシュ計算 & 同期証跡スタンプ更新 (提案1)
# ------------------------------------------------------------------------------
compute_tree_hash() {
  local dir="$1"
  if [[ ! -d "$dir" ]]; then
    echo "NONE"
    return 0
  fi
  (cd "$dir" && find . -type f ! -name ".DS_Store" ! -name "*.orig" ! -name "*.rej" | sort | xargs shasum -a 256 2>/dev/null | shasum -a 256 | awk '{print $1}')
}

update_sync_stamp() {
  local mode="$1"
  local g_hash
  local w_hash
  g_hash="$(compute_tree_hash "$GLOBAL_PLUGIN")"
  w_hash="$(compute_tree_hash "$WS_PLUGIN")"
  local now_iso
  now_iso="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  cat > "$SYNC_STAMP_FILE" << EOF
{
  "synced_at": "${now_iso}",
  "last_action": "${mode}",
  "global_tree_hash": "${g_hash}",
  "workspace_tree_hash": "${w_hash}"
}
EOF
}

# ------------------------------------------------------------------------------
# 診断・ステータス表示 (--status)
# ------------------------------------------------------------------------------
run_status() {
  python3 - "$WORKSPACE_ROOT" "$WS_PLUGIN" "$WS_ROOT_RULES" "$GLOBAL_PLUGINS_DIR" "$GLOBAL_PLUGIN" "$KNOWLEDGE_HUB_DIR" "$SEC11_HEADER" "$SYNC_STAMP_FILE" << 'PYEOF'
import sys, os, pathlib, subprocess, hashlib, json, datetime, re

ws_root = pathlib.Path(sys.argv[1])
ws_plugin = pathlib.Path(sys.argv[2])
ws_root_rules = pathlib.Path(sys.argv[3])
global_plugins_dir = pathlib.Path(sys.argv[4])
global_plugin = pathlib.Path(sys.argv[5])
hub_dir = pathlib.Path(sys.argv[6])
sec11_header = sys.argv[7]
stamp_file = pathlib.Path(sys.argv[8])

print("=" * 76)
print("🔍 [template-pipeline-sync] グローバル ⇔ ワークスペース 同期診断レポート")
print("=" * 76)

issues_count = 0
cause_a_files = []  # Global先行
cause_b_files = []  # Workspace先行
cause_c_files = []  # 双方向変更
cause_d_items = []  # 環境汚染・残骸
hub_pending_claims = []

# 1. 原因D: 環境汚染・残骸ファイルの検査
if global_plugins_dir.exists():
    for item in sorted(global_plugins_dir.iterdir()):
        if item.name.startswith("system-dev-pipeline") and item.name != "system-dev-pipeline":
            cause_d_items.append(f"プラグイン直下の重複バックアップフォルダ: {item} (ローダー二重スキャンリスク)")

for base_label, base_path in [("Global", global_plugin), ("Workspace", ws_plugin)]:
    if base_path.exists():
        for p in sorted(base_path.rglob("*")):
            if p.is_file() and (p.name.endswith(".orig") or p.name.endswith(".rej")):
                rel = p.relative_to(base_path)
                cause_d_items.append(f"{base_label}内のパッチ残骸ファイル: {rel} ({p})")

# 2. Global ⇔ Workspace ファイル比較と原因 A / B / C 分類
def list_rel_files(root: pathlib.Path):
    res = set()
    if not root.exists():
        return res
    for p in root.rglob("*"):
        if p.is_file() and p.name != ".DS_Store" and not p.name.endswith(".orig") and not p.name.endswith(".rej"):
            res.add(str(p.relative_to(root)))
    return res

g_files = list_rel_files(global_plugin)
w_files = list_rel_files(ws_plugin)
all_rel = sorted(g_files | w_files)

def is_ws_git_dirty(rel_path: str) -> bool:
    target = f".agents/plugins/system-dev-pipeline/{rel_path}"
    r = subprocess.run(["git", "status", "--porcelain", "--", target], cwd=ws_root, capture_output=True, text=True)
    return bool(r.stdout.strip())

for rel in all_rel:
    gp = global_plugin / rel
    wp = ws_plugin / rel
    if gp.exists() and not wp.exists():
        cause_a_files.append((rel, "Globalのみに存在 (新規追加ファイル / PURPOSE.md 等)"))
    elif wp.exists() and not gp.exists():
        cause_b_files.append((rel, "Workspaceのみに存在 (ローカル新規作成ファイル)"))
    else:
        g_bytes = gp.read_bytes()
        w_bytes = wp.read_bytes()
        if g_bytes != w_bytes:
            g_text = g_bytes.decode("utf-8", errors="replace")
            w_text = w_bytes.decode("utf-8", errors="replace")
            g_lines = set(g_text.splitlines())
            w_lines = set(w_text.splitlines())
            g_only = g_lines - w_lines
            w_only = w_lines - g_lines
            ws_dirty = is_ws_git_dirty(rel)
            g_mtime = gp.stat().st_mtime
            w_mtime = wp.stat().st_mtime

            if g_only and not w_only:
                cause_a_files.append((rel, "Globalに追記行あり (知見昇格パッチ等の先行反映)"))
            elif w_only and not g_only:
                cause_b_files.append((rel, "Workspaceに追記行あり (ローカル改訂作業中)"))
            elif not ws_dirty and g_mtime > w_mtime:
                cause_a_files.append((rel, "Global側の更新日時が新しくWorkspace側はGit未変更 (Global先行)"))
            elif ws_dirty and w_mtime > g_mtime and not any("PAT-" in ln for ln in g_only):
                cause_b_files.append((rel, "Workspace側に未コミット変更あり (ローカル改訂作業中)"))
            else:
                cause_c_files.append((rel, "GlobalとWorkspaceの双方に固有の変更行あり (要マージ確認)"))

# 3. ワークスペース内 rules/AGENTS.md (共通部 + 第11節) の整合性検査 (提案 2-B)
root_rules_issues = []
plugin_rules_file = ws_plugin / "rules/AGENTS.md"
if plugin_rules_file.exists() and ws_root_rules.exists():
    p_text = plugin_rules_file.read_text(encoding="utf-8")
    r_text = ws_root_rules.read_text(encoding="utf-8")
    if sec11_header in p_text:
        root_rules_issues.append("配布用プラグイン側 (.agents/plugins/.../rules/AGENTS.md) にワークスペース固有の第11節が混入しています")
    if sec11_header not in r_text:
        root_rules_issues.append("ワークスペースルート側 (rules/AGENTS.md) に第11節（同期規約）が未記載です")
        r_common = r_text
    else:
        idx = r_text.index(sec11_header)
        r_common = re.sub(r'\n+---\n*$', '\n', r_text[:idx])
    if p_text.rstrip() != r_common.rstrip():
        root_rules_issues.append("ワークスペースルート rules/AGENTS.md の共通部(第1〜10節)とプラグイン正本に差分があります")

# 4. Central Knowledge Hub (~/.gemini/knowledge-hub/) 未吸収原票チェック (提案 5)
absorbed_claims = set()
manifest_file = ws_plugin / "PIPELINE_MANIFEST.json"
if manifest_file.exists():
    try:
        mdata = json.loads(manifest_file.read_text(encoding="utf-8"))
        for entry in mdata.get("absorbed_patterns", []):
            for cid in entry.get("claim_ids", []):
                absorbed_claims.add(cid)
    except Exception:
        pass

for sub in ["inbox", "active_claims"]:
    subdir = hub_dir / sub
    if subdir.exists():
        for cp in sorted(subdir.glob("CLAIM-*.md")):
            cid = cp.stem
            if cid not in absorbed_claims:
                hub_pending_claims.append(f"{sub}/{cp.name}")

# レポート出力
print("\n[1] Global ⇔ Workspace パイプライン資産比較:")
if not cause_a_files and not cause_b_files and not cause_c_files:
    print("  ✅ Global と Workspace 正本の全ファイルが完全一致しています。")
else:
    if cause_a_files:
        issues_count += len(cause_a_files)
        print(f"  📥 【原因A: グローバル先行 (未還流の知見昇格)】({len(cause_a_files)} 件)")
        for f, desc in cause_a_files:
            print(f"     - {f}: {desc}")
    if cause_b_files:
        issues_count += len(cause_b_files)
        print(f"  📝 【原因B: ワークスペース先行 (ローカル改訂中)】({len(cause_b_files)} 件)")
        for f, desc in cause_b_files:
            print(f"     - {f}: {desc}")
    if cause_c_files:
        issues_count += len(cause_c_files)
        print(f"  ⚠️ 【原因C: 双方向変更 (コンフリクト要確認)】({len(cause_c_files)} 件)")
        for f, desc in cause_c_files:
            print(f"     - {f}: {desc}")

print("\n[2] 環境汚染・残骸ファイル検査 (原因D):")
if not cause_d_items:
    print("  ✅ .orig/.rej 残骸および plugins/ 直下の重複バックアップはありません。")
else:
    issues_count += len(cause_d_items)
    print(f"  🧹 【原因D: 環境汚染・残骸検出】({len(cause_d_items)} 件)")
    for item in cause_d_items:
        print(f"     - {item}")

print("\n[3] ワークスペース内 rules/AGENTS.md 役割分離・共通部整合性 (提案 2-B):")
if not root_rules_issues:
    print("  ✅ 共通部(第1〜10節)は完全一致しており、第11節はルート規約のみに分離配置されています。")
else:
    issues_count += len(root_rules_issues)
    for item in root_rules_issues:
        print(f"  ⚠️ {item}")

print("\n[4] V2.3 Central Knowledge Hub (~/.gemini/knowledge-hub/) 未吸収原票監査 (提案 5):")
if not hub_dir.exists():
    print("  ℹ️ ~/.gemini/knowledge-hub/ は未作成です（V2.3 移行時に自動構成）。")
elif not hub_pending_claims:
    print("  ✅ 未吸収の知見原票 (CLAIM-*.md) はありません。")
else:
    issues_count += len(hub_pending_claims)
    print(f"  📥 未本流化の知見原票が {len(hub_pending_claims)} 件存在します:")
    for c in hub_pending_claims:
        print(f"     - {c}")

print("\n" + "-" * 76)
if issues_count == 0:
    print("🎉 判定結果: [SYNCED] ドリフト・残骸は 0 件です。安全に改訂・改変作業を進行できます。")
    sys.exit(0)
else:
    print(f"🚨 判定結果: [DRIFT_DETECTED] 計 {issues_count} 件の差分または要処置項目が検出されました。")
    print("💡 推奨アクション:")
    if cause_d_items:
        print("   ・残骸・重複バックアップの清掃: sync_pipeline.sh --cleanup")
    if cause_a_files:
        print("   ・Global先行差分の逆同期 (Backport): sync_pipeline.sh --backport (※要ユーザー承認)")
    if cause_b_files and not cause_a_files and not cause_c_files:
        print("   ・改訂完了後のGlobal反映 (Deploy): sync_pipeline.sh --deploy (※要ユーザー承認)")
    if root_rules_issues:
        print("   ・ルート rules/AGENTS.md 共通部の同期: sync_pipeline.sh --sync-root-rules")
    sys.exit(2)
PYEOF
}

# ------------------------------------------------------------------------------
# 環境清掃 (--cleanup)
# ------------------------------------------------------------------------------
run_cleanup() {
  echo "🧹 [Cleanup] 環境内の .orig / .rej 残骸および重複バックアップを清掃しています..."
  find "$GLOBAL_PLUGIN" "$WS_PLUGIN" -type f \( -name "*.orig" -o -name "*.rej" \) -print -delete 2>/dev/null || true

  if [[ -d "$GLOBAL_PLUGINS_DIR" ]]; then
    for item in "${GLOBAL_PLUGINS_DIR}"/system-dev-pipeline*; do
      [[ -e "$item" ]] || continue
      if [[ "$(basename "$item")" != "system-dev-pipeline" ]]; then
        mkdir -p "$BACKUP_BASE_DIR"
        local dest="${BACKUP_BASE_DIR}/$(basename "$item")"
        echo "  📦 プラグイン直下のバックアップを退避: $item -> $dest"
        mv "$item" "$dest"
      fi
    done
  fi
  echo "✅ [Cleanup] 完了しました。"
}

# ------------------------------------------------------------------------------
# Global -> Workspace 逆同期 (--backport)
# ------------------------------------------------------------------------------
run_backport() {
  run_cleanup
  echo "📥 [Backport] Global (~/.gemini/config/plugins/system-dev-pipeline) -> Workspace 正本へ逆同期しています..."
  rsync -av --exclude=".DS_Store" --exclude="*.orig" --exclude="*.rej" "${GLOBAL_PLUGIN}/" "${WS_PLUGIN}/"
  echo "🔄 [Root Rules Sync] ワークスペースルートの rules/AGENTS.md 共通部(第1〜10節)を連動更新しています..."
  sync_root_rules_from_plugin
  update_sync_stamp "backport"
  echo "✅ [Backport] 逆同期および証跡スタンプの更新が完了しました。"
}

# ------------------------------------------------------------------------------
# Workspace -> Global 順同期・リリース反映 (--deploy)
# ------------------------------------------------------------------------------
run_deploy() {
  run_cleanup
  mkdir -p "$BACKUP_BASE_DIR"
  local ts
  ts="$(date +%Y%m%d_%H%M%S)"
  local backup_dest="${BACKUP_BASE_DIR}/backup_${ts}"
  if [[ -d "$GLOBAL_PLUGIN" ]]; then
    echo "📦 [Backup] 更新前の Global プラグインを退避しています: ${backup_dest}"
    cp -R "$GLOBAL_PLUGIN" "$backup_dest"
  fi
  echo "🚀 [Deploy] Workspace 正本 -> Global (~/.gemini/config/plugins/system-dev-pipeline) へ反映しています..."
  mkdir -p "$GLOBAL_PLUGIN"
  rsync -av --delete --exclude=".DS_Store" --exclude="*.orig" --exclude="*.rej" "${WS_PLUGIN}/" "${GLOBAL_PLUGIN}/"
  echo "🔄 [Root Rules Sync] ワークスペースルートの rules/AGENTS.md 共通部(第1〜10節)を連動更新しています..."
  sync_root_rules_from_plugin
  if [[ -f "${GLOBAL_PLUGIN}/scripts/pipeline-reconciler.sh" ]]; then
    echo "🔄 [Upgrade Reconciler] Global Knowledge Hub との照合・マイグレーションを実行しています..."
    bash "${GLOBAL_PLUGIN}/scripts/pipeline-reconciler.sh" --upgrade
  fi
  update_sync_stamp "deploy"
  echo "✅ [Deploy] グローバル反映および証跡スタンプの更新が完了しました。"
}

# ------------------------------------------------------------------------------
# Git pre-commit フック用チェック (--pre-commit-check) (提案1)
# ------------------------------------------------------------------------------
run_pre_commit_check() {
  python3 - "$WORKSPACE_ROOT" "$WS_PLUGIN" "$WS_ROOT_RULES" "$GLOBAL_PLUGIN" "$SEC11_HEADER" << 'PYEOF'
import sys, pathlib, subprocess, re

ws_root = pathlib.Path(sys.argv[1])
ws_plugin = pathlib.Path(sys.argv[2])
ws_root_rules = pathlib.Path(sys.argv[3])
global_plugin = pathlib.Path(sys.argv[4])
sec11_header = sys.argv[5]

# ステージングされたファイルを取得
r = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ws_root, capture_output=True, text=True)
staged = [line.strip() for line in r.stdout.splitlines() if line.strip()]

touches_pipeline = any(f.startswith(".agents/plugins/system-dev-pipeline/") or f == "rules/AGENTS.md" for f in staged)
if not touches_pipeline:
    sys.exit(0)

errors = []

# 1. Global側にのみ存在するファイルや、Global側が新しい未取り込み変更(原因A)がないか検査
if global_plugin.exists():
    for gp in global_plugin.rglob("*"):
        if gp.is_file() and gp.name != ".DS_Store" and not gp.name.endswith(".orig") and not gp.name.endswith(".rej"):
            rel = gp.relative_to(global_plugin)
            wp = ws_plugin / rel
            if not wp.exists():
                errors.append(f"Global側にのみ存在する未同期ファイルがあります: {rel}")
            else:
                g_text = gp.read_text(encoding="utf-8", errors="replace")
                w_text = wp.read_text(encoding="utf-8", errors="replace")
                if g_text != w_text:
                    g_only = set(g_text.splitlines()) - set(w_text.splitlines())
                    # Global側に固有のPAT記述がありWorkspaceにない場合は未Backportと判定
                    if any("PAT-" in ln for ln in g_only):
                        errors.append(f"Global側の昇格知見がWorkspaceへ未反映です: {rel}")

# 2. 提案2-B: 配布用プラグイン側に第11節が混入していないか & 共通部が一致しているか
p_rules = ws_plugin / "rules/AGENTS.md"
if p_rules.exists() and ws_root_rules.exists():
    p_text = p_rules.read_text(encoding="utf-8")
    r_text = ws_root_rules.read_text(encoding="utf-8")
    if sec11_header in p_text:
        errors.append(".agents/plugins/system-dev-pipeline/rules/AGENTS.md にワークスペース固有の第11節が混入しています。")
    if sec11_header in r_text:
        r_common = re.sub(r'\n+---\n*$', '\n', r_text[:r_text.index(sec11_header)])
    else:
        r_common = r_text
    if p_text.rstrip() != r_common.rstrip():
        errors.append("rules/AGENTS.md の共通部(第1〜10節)と .agents/plugins/.../rules/AGENTS.md が不一致です。`sync_pipeline.sh --sync-root-rules` を実行してください。")

if errors:
    print("🚨 [Git Pre-commit Guard: パイプライン同期エラー]")
    for e in errors:
        print(f"  - {e}")
    print("👉 コミット前に `template-pipeline-sync` スキル (`sync_pipeline.sh --status`) を実行して同期を行ってください。")
    sys.exit(1)

sys.exit(0)
PYEOF
}

# ------------------------------------------------------------------------------
# メインディスパッチ
# ------------------------------------------------------------------------------
MODE="${1:---status}"

case "$MODE" in
  --status)
    set +e
    run_status
    rc=$?
    set -e
    if [[ $rc -eq 0 ]]; then
      update_sync_stamp "status_clean"
    fi
    exit $rc
    ;;
  --cleanup)
    run_cleanup
    ;;
  --backport)
    run_backport
    run_status
    ;;
  --deploy)
    run_deploy
    run_status
    ;;
  --sync-root-rules)
    sync_root_rules_from_plugin
    echo "✅ ワークスペースルートの rules/AGENTS.md 共通部をプラグイン正本と同期しました。"
    ;;
  --pre-commit-check)
    run_pre_commit_check
    ;;
  *)
    echo "Usage: $0 [--status | --cleanup | --backport | --deploy | --sync-root-rules | --pre-commit-check]"
    exit 1
    ;;
esac
