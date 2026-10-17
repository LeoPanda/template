#!/usr/bin/env bash
# ==============================================================================
# pipeline-reconciler.sh: V2.3 Central Knowledge Hub 管理 & Upgrade Reconciler
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MANIFEST_FILE="${PLUGIN_ROOT}/PIPELINE_MANIFEST.json"
INVARIANTS_FILE="${PLUGIN_ROOT}/rules/CORE_INVARIANTS.md"

HUB_DIR="${KNOWLEDGE_HUB_DIR:-${HOME}/.gemini/knowledge-hub}"
STATE_FILE="${HUB_DIR}/LOCAL_HUB_STATE.json"
OVERLAY_RULES_FILE="${HUB_DIR}/overlay/LOCAL_FEEDBACK_RULES.md"

# ------------------------------------------------------------------------------
# 1. Knowledge Hub 初期化 (--init-hub)
# ------------------------------------------------------------------------------
init_hub() {
  mkdir -p \
    "${HUB_DIR}/inbox" \
    "${HUB_DIR}/pending_approval" \
    "${HUB_DIR}/overlay/skills" \
    "${HUB_DIR}/active_claims" \
    "${HUB_DIR}/archive/upstreamed" \
    "${HUB_DIR}/suspended" \
    "${HUB_DIR}/rejected"

  python3 - "$MANIFEST_FILE" "$STATE_FILE" "$OVERLAY_RULES_FILE" << 'PYEOF'
import sys, json, pathlib, datetime

manifest_path = pathlib.Path(sys.argv[1])
state_path = pathlib.Path(sys.argv[2])
overlay_path = pathlib.Path(sys.argv[3])

core_ver = "2.3.0"
if manifest_path.exists():
    try:
        core_ver = json.loads(manifest_path.read_text(encoding="utf-8")).get("version", "2.3.0")
    except Exception:
        pass

now_iso = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds")

if not state_path.exists():
    initial_state = {
        "base_core_version": core_ver,
        "last_reconciled_at": now_iso,
        "active_overlay_claims": [],
        "upstreamed_history": []
    }
    state_path.write_text(json.dumps(initial_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if not overlay_path.exists():
    header = (
        "# 環境共通 ローカルオーバーレイ規約 (LOCAL_FEEDBACK_RULES)\n\n"
        "> 本ファイルは Central Knowledge Hub の有効原票からクリーン再生成される拡張規約層（上限80行）です。\n\n"
        "現在、ローカルオーバーレイに適用中の追加規約はありません（すべて公式 Immutable Core に統合済みです）。\n"
    )
    overlay_path.write_text(header, encoding="utf-8")
PYEOF
}

# ------------------------------------------------------------------------------
# 2. Local Overlay クリーン再生成 (--rebuild-overlay)
# ------------------------------------------------------------------------------
rebuild_overlay() {
  init_hub
  python3 - "$HUB_DIR" "$MANIFEST_FILE" "$STATE_FILE" "$OVERLAY_RULES_FILE" << 'PYEOF'
import sys, json, pathlib, datetime, re

hub_dir = pathlib.Path(sys.argv[1])
manifest_path = pathlib.Path(sys.argv[2])
state_path = pathlib.Path(sys.argv[3])
overlay_path = pathlib.Path(sys.argv[4])
active_dir = hub_dir / "active_claims"

core_ver = "2.3.0"
if manifest_path.exists():
    try:
        core_ver = json.loads(manifest_path.read_text(encoding="utf-8")).get("version", "2.3.0")
    except Exception:
        pass

state = {"base_core_version": core_ver, "active_overlay_claims": [], "upstreamed_history": []}
if state_path.exists():
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        pass

def parse_claim(md_path: pathlib.Path):
    text = md_path.read_text(encoding="utf-8")
    meta = {
        "claim_id": md_path.stem,
        "pattern_id": "",
        "title": md_path.stem,
        "applicable_profiles": ["ALL"],
        "category": "GENERAL",
        "target_candidates": [],
        "distilled_rules": []
    }
    # Frontmatter 簡易抽出
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    body = text
    if fm_match:
        fm_text, body = fm_match.group(1), fm_match.group(2)
        for line in fm_text.splitlines():
            m = re.match(r'^([a-zA-Z0-9_]+):\s*(.+)$', line.strip())
            if m:
                k, v = m.group(1), m.group(2).strip().strip('"').strip("'")
                if k in ("claim_id", "pattern_id", "title", "category"):
                    meta[k] = v
                elif k == "applicable_profiles":
                    profs = re.findall(r'[A-Za-z0-9_ -]+', v)
                    meta[k] = [p.strip() for p in profs if p.strip()]

    # セクション3 (抽象化された処方箋・推奨ルール) から箇条書き抽出
    sec3 = re.search(r"##\s*3\..*?\n(.*?)(?=\n##\s*[45]\.|\Z)", body, re.DOTALL)
    target_block = sec3.group(1) if sec3 else body
    rules = []
    for ln in target_block.splitlines():
        s = ln.strip()
        if s.startswith("- ") or s.startswith("* "):
            # 純度保護: 万が一 [PAT-xxx] や [CLAIM-xxx] が含まれていたら除去
            clean_ln = re.sub(r'\[?(PAT-[A-Z0-9-]+|CLAIM-[A-Za-z0-9-]+)\]?\s*:?\s*', '', s[2:]).strip()
            if clean_ln:
                rules.append(clean_ln)
    meta["distilled_rules"] = rules
    return meta

claims_meta = []
for cp in sorted(active_dir.glob("CLAIM-*.md")):
    claims_meta.append(parse_claim(cp))

lines = [
    "# 環境共通 ローカルオーバーレイ規約 (LOCAL_FEEDBACK_RULES)",
    "",
    "> 本ファイルは Central Knowledge Hub の有効原票から自動生成される拡張規約層（絶対上限 80行）です。",
    ""
]

now_iso = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds")
new_active_list = []

if not claims_meta:
    lines.append("現在、ローカルオーバーレイに適用中の追加規約はありません（すべて公式 Immutable Core に統合済みです）。")
else:
    by_cat = {}
    for cm in claims_meta:
        cat = cm["category"] or "GENERAL"
        by_cat.setdefault(cat, []).append(cm)
        new_active_list.append({
            "claim_id": cm["claim_id"],
            "pattern_id": cm["pattern_id"],
            "applied_at": now_iso,
            "overlay_target": "overlay/LOCAL_FEEDBACK_RULES.md",
            "distilled_rule_text": " / ".join(cm["distilled_rules"])
        })

    for cat, items in sorted(by_cat.items()):
        lines.append(f"## [{cat}] 拡張ガードレール")
        for item in items:
            profs = ", ".join(item["applicable_profiles"]) if item["applicable_profiles"] else "ALL"
            prefix = f"[対象: {profs}] " if profs != "ALL" else ""
            for r in item["distilled_rules"]:
                lines.append(f"- {prefix}{r}")
        lines.append("")

if len(lines) > 80:
    print(f"⚠️ [Warning] LOCAL_FEEDBACK_RULES.md が 80行バジェットを超過しています ({len(lines)}行)。wiki-compactor による圧縮または Core 昇格を実施してください。", file=sys.stderr)
    lines = lines[:79] + ["- (※行数上限80行到達のため以降省略。要Core昇格コンパイル)"]

overlay_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

state["base_core_version"] = core_ver
state["last_reconciled_at"] = now_iso
state["active_overlay_claims"] = new_active_list
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"✅ [Rebuild Overlay] active_claims ({len(claims_meta)}件) から LOCAL_FEEDBACK_RULES.md ({len(lines)}行) をクリーン再生成しました。")
PYEOF
}

# ------------------------------------------------------------------------------
# 3. ステータス確認 (--status)
# ------------------------------------------------------------------------------
run_status() {
  init_hub
  python3 - "$HUB_DIR" "$MANIFEST_FILE" "$STATE_FILE" "$OVERLAY_RULES_FILE" << 'PYEOF'
import sys, json, pathlib

hub_dir = pathlib.Path(sys.argv[1])
manifest_path = pathlib.Path(sys.argv[2])
state_path = pathlib.Path(sys.argv[3])
overlay_path = pathlib.Path(sys.argv[4])

manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}

inbox_files = sorted((hub_dir / "inbox").glob("CLAIM-*.md"))
pending_files = sorted((hub_dir / "pending_approval").glob("*.md"))
active_files = sorted((hub_dir / "active_claims").glob("CLAIM-*.md"))
archived_files = sorted((hub_dir / "archive/upstreamed").glob("CLAIM-*.md"))
suspended_files = sorted((hub_dir / "suspended").glob("CLAIM-*.md"))
rejected_files = sorted((hub_dir / "rejected").glob("*.md"))
overlay_lines = len(overlay_path.read_text(encoding="utf-8").splitlines()) if overlay_path.exists() else 0

print("=" * 76)
print("📊 [Central Knowledge Hub & Reconciler] 状態診断レポート")
print("=" * 76)
print(f"  ・Immutable Core Version : {manifest.get('version', 'unknown')} (吸収済パターン: {len(manifest.get('absorbed_patterns', []))}件)")
print(f"  ・Hub Base Core Version  : {state.get('base_core_version', 'unknown')}")
print(f"  ・Local Overlay 行数     : {overlay_lines} / 80 行 ({overlay_path})")
print("-" * 76)
print(f"  📥 inbox/ (未監査原票)            : {len(inbox_files)} 件")
for f in inbox_files:
    print(f"     - {f.name}")
print(f"  🗂️ pending_approval/ (承認・裁定待): {len(pending_files)} 件")
for f in pending_files:
    print(f"     - {f.name}")
print(f"  🧩 active_claims/ (Overlay適用中) : {len(active_files)} 件")
for f in active_files:
    print(f"     - {f.name}")
print(f"  📦 archive/upstreamed/ (Core吸収済): {len(archived_files)} 件")
print(f"  ⏸️ suspended/ (仕様衝突保留)       : {len(suspended_files)} 件")
print(f"  🚫 rejected/ (監査棄却履歴)        : {len(rejected_files)} 件")
print("=" * 76)
PYEOF
}

# ------------------------------------------------------------------------------
# 4. 新バージョン適用時 Upgrade Reconciler (--upgrade)
# ------------------------------------------------------------------------------
run_upgrade() {
  init_hub
  echo "🔄 [Upgrade Reconciler] 新 Immutable Core の PIPELINE_MANIFEST.json と Local Hub を照合しています..."
  python3 - "$HUB_DIR" "$MANIFEST_FILE" "$STATE_FILE" << 'PYEOF'
import sys, json, pathlib, shutil, datetime, re

hub_dir = pathlib.Path(sys.argv[1])
manifest_path = pathlib.Path(sys.argv[2])
state_path = pathlib.Path(sys.argv[3])

if not manifest_path.exists():
    print("❌ PIPELINE_MANIFEST.json が見つかりません。", file=sys.stderr)
    sys.exit(1)

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"upstreamed_history": []}

core_ver = manifest.get("version", "2.3.0")
absorbed_pat_ids = set()
absorbed_claim_ids = set()
for entry in manifest.get("absorbed_patterns", []):
    if entry.get("pattern_id"):
        absorbed_pat_ids.add(entry["pattern_id"])
    for cid in entry.get("claim_ids", []):
        absorbed_claim_ids.add(cid)

active_dir = hub_dir / "active_claims"
inbox_dir = hub_dir / "inbox"
archive_dir = hub_dir / "archive/upstreamed"
now_iso = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds")

retired_count = 0
retained_count = 0

for target_dir in (active_dir, inbox_dir):
    for cp in sorted(target_dir.glob("CLAIM-*.md")):
        text = cp.read_text(encoding="utf-8")
        cid = cp.stem
        m_pat = re.search(r'^pattern_id:\s*["\']?([A-Za-z0-9-]+)["\']?', text, re.MULTILINE)
        pid = m_pat.group(1) if m_pat else ""

        if cid in absorbed_claim_ids or (pid and pid in absorbed_pat_ids):
            dest = archive_dir / cp.name
            shutil.move(str(cp), str(dest))
            retired_count += 1
            state.setdefault("upstreamed_history", []).append({
                "claim_id": cid,
                "pattern_id": pid,
                "retired_at_version": core_ver,
                "retired_at": now_iso,
                "resolution": "FAST_PATH_ID_MATCH",
                "archived_path": f"archive/upstreamed/{cp.name}"
            })
            print(f"  📦 [Pattern A: ID一致自動退役] {cp.name} ({pid}) -> archive/upstreamed/")
        else:
            if target_dir == active_dir:
                retained_count += 1
                print(f"  🧩 [Pattern C: 独自知見継続保持] {cp.name} ({pid})")

state["base_core_version"] = core_ver
state["last_reconciled_at"] = now_iso
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"✅ 照合完了: 自動退役 {retired_count} 件 / 継続保持 {retained_count} 件")
PYEOF
  rebuild_overlay
}

# ------------------------------------------------------------------------------
# 5. 原票の承認適用 (--activate-claim <CLAIM_FILE_OR_ID>) / 棄却 (--reject-claim <CLAIM_FILE_OR_ID> [REASON])
# ------------------------------------------------------------------------------
activate_claim() {
  local target="${1:-}"
  if [[ -z "$target" ]]; then
    echo "Usage: $0 --activate-claim <CLAIM_FILE_OR_ID>" >&2
    exit 1
  fi
  init_hub
  local src=""
  if [[ -f "$target" ]]; then
    src="$target"
  elif [[ -f "${HUB_DIR}/inbox/${target}" ]]; then
    src="${HUB_DIR}/inbox/${target}"
  elif [[ -f "${HUB_DIR}/inbox/${target}.md" ]]; then
    src="${HUB_DIR}/inbox/${target}.md"
  else
    echo "❌ 指定された原票が見つかりません: $target" >&2
    exit 1
  fi
  local fname
  fname="$(basename "$src")"
  python3 - "$src" "${HUB_DIR}/active_claims/${fname}" << 'PYEOF'
import sys, pathlib, re
src = pathlib.Path(sys.argv[1])
dst = pathlib.Path(sys.argv[2])
text = src.read_text(encoding="utf-8")
text = re.sub(r'^status:\s*".*"$', 'status: "OVERLAY_ACTIVE"', text, flags=re.MULTILINE)
dst.write_text(text, encoding="utf-8")
if src.resolve() != dst.resolve() and src.parent.name in ("inbox", "pending_approval"):
    src.unlink()
PYEOF
  echo "✅ 原票を active_claims/ へ昇格しました: ${fname}"
  rebuild_overlay
}

reject_claim() {
  local target="${1:-}"
  local reason="${2:-Rejected by Semantic Auditor}"
  if [[ -z "$target" ]]; then
    echo "Usage: $0 --reject-claim <CLAIM_FILE_OR_ID> [REASON]" >&2
    exit 1
  fi
  init_hub
  local src=""
  if [[ -f "$target" ]]; then
    src="$target"
  elif [[ -f "${HUB_DIR}/inbox/${target}" ]]; then
    src="${HUB_DIR}/inbox/${target}"
  elif [[ -f "${HUB_DIR}/inbox/${target}.md" ]]; then
    src="${HUB_DIR}/inbox/${target}.md"
  else
    echo "❌ 指定された原票が見つかりません: $target" >&2
    exit 1
  fi
  local fname
  fname="$(basename "$src")"
  python3 - "$src" "${HUB_DIR}/rejected/${fname}" "$reason" << 'PYEOF'
import sys, pathlib, re, datetime
src = pathlib.Path(sys.argv[1])
dst = pathlib.Path(sys.argv[2])
reason = sys.argv[3]
now_iso = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds")
text = src.read_text(encoding="utf-8")
text = re.sub(r'^status:\s*".*"$', 'status: "REJECTED"', text, flags=re.MULTILINE)
text += f"\n\n---\n## 監査棄却記録 (Rejection Record)\n- **棄却日時**: {now_iso}\n- **棄却理由**: {reason}\n"
dst.write_text(text, encoding="utf-8")
if src.resolve() != dst.resolve() and src.parent.name in ("inbox", "pending_approval", "active_claims"):
    src.unlink()
PYEOF
  echo "🚫 原票を rejected/ へ移動・永続記録しました: ${fname}"
  rebuild_overlay
}

# ------------------------------------------------------------------------------
# 6. パイプライン純度・絶対行数バジェット検証 (--audit-budget)
# ------------------------------------------------------------------------------
audit_budget() {
  init_hub
  python3 - "$PLUGIN_ROOT" "$OVERLAY_RULES_FILE" << 'PYEOF'
import sys, pathlib, re

plugin_root = pathlib.Path(sys.argv[1])
overlay_file = pathlib.Path(sys.argv[2])

errors = []
checked = 0

def check_file(p: pathlib.Path, limit: int, check_pat_id: bool = True):
    global checked
    if not p.exists():
        return
    checked += 1
    lines = p.read_text(encoding="utf-8").splitlines()
    if len(lines) > limit:
        errors.append(f"[Budget Exceeded] {p.relative_to(plugin_root) if p.is_relative_to(plugin_root) else p}: {len(lines)} 行 (上限 {limit} 行)")
    if check_pat_id:
        for idx, ln in enumerate(lines, 1):
            # 特定の過去履歴ID (例: PAT-SYS-001, CLAIM-2026...) の混入を検査 (フォーマット説明用の PAT-LOC-xxx や PAT-{CAT}-xxx は除外)
            if re.search(r'\bPAT-[A-Z]+-\d{3}\b', ln) or re.search(r'\bCLAIM-\d{8}-[A-Za-z0-9_-]+\b', ln):
                errors.append(f"[Lineage Impurity] {p.relative_to(plugin_root) if p.is_relative_to(plugin_root) else p}:{idx} に特定の履歴IDが混入しています: {ln.strip()}")

check_file(plugin_root / "rules/AGENTS.md", 220, True)
for ap in sorted((plugin_root / "agents").glob("*.md")):
    check_file(ap, 120, True)
for sp in sorted((plugin_root / "skills").glob("*/SKILL.md")):
    check_file(sp, 120, True)
if overlay_file.exists():
    check_file(overlay_file, 80, True)

# PURPOSE.md 残存チェック
for pp in sorted((plugin_root / "skills").glob("*/PURPOSE.md")):
    errors.append(f"[Deprecated File] 廃止された個別 PURPOSE.md が残存しています: {pp.relative_to(plugin_root)}")

if errors:
    print("🚨 [New Gate 4: 純度・絶対行数バジェット監査 FAIL]")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print(f"✅ [New Gate 4: 純度・絶対行数バジェット監査 PASS] 全 {checked} ファイルが上限行数以内かつ履歴ID混入ゼロです。")
    sys.exit(0)
PYEOF
}

# ------------------------------------------------------------------------------
# 7. 未吸収原票のエクスポート (--export-claims [DEST_DIR])
# ------------------------------------------------------------------------------
export_claims() {
  local dest_dir="${1:-./exported-claims}"
  init_hub
  mkdir -p "$dest_dir"
  local count=0
  for sub in "active_claims" "inbox"; do
    for cp in "${HUB_DIR}/${sub}"/CLAIM-*.md; do
      [[ -e "$cp" ]] || continue
      cp "$cp" "${dest_dir}/"
      count=$((count + 1))
    done
  done
  echo "📤 [Export Claims] 計 ${count} 件の未吸収知見原票を ${dest_dir} へエクスポートしました。"
}

# ------------------------------------------------------------------------------
# メインディスパッチ
# ------------------------------------------------------------------------------
MODE="${1:---status}"

case "$MODE" in
  --init-hub)
    init_hub
    echo "✅ Knowledge Hub (${HUB_DIR}) を初期化しました。"
    ;;
  --status)
    run_status
    ;;
  --rebuild-overlay)
    rebuild_overlay
    ;;
  --upgrade)
    run_upgrade
    ;;
  --activate-claim)
    shift
    activate_claim "${1:-}"
    ;;
  --reject-claim)
    shift
    reject_claim "${1:-}" "${2:-}"
    ;;
  --audit-budget)
    audit_budget
    ;;
  --export-claims)
    shift
    export_claims "${1:-./exported-claims}"
    ;;
  *)
    echo "Usage: $0 [--init-hub | --status | --rebuild-overlay | --upgrade | --activate-claim <CLAIM> | --reject-claim <CLAIM> [REASON] | --audit-budget | --export-claims [DIR]]"
    exit 1
    ;;
esac
