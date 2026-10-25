#!/usr/bin/env python3
"""
Central Knowledge Hub 管理 & Upgrade Reconciler コアモジュール (reconciler_core.py)
Profile E: Zero-Dependency Python 3
Knowledge Hub 初期化、オーバーレイ再生成、ステータス診断、Coreアップグレード照合、
原票昇格・棄却、行数・純度バジェット監査
"""

import argparse
import datetime
import json
import os
import pathlib
import re
import shutil
import sys
from typing import Any, Dict, List, Optional, Set

JST = datetime.timezone(datetime.timedelta(hours=9))


class KnowledgeHubReconciler:
    def __init__(
        self,
        hub_dir: pathlib.Path,
        manifest_path: pathlib.Path,
        invariants_path: pathlib.Path,
        plugin_root: pathlib.Path,
    ):
        self.hub_dir = hub_dir
        self.manifest_path = manifest_path
        self.invariants_path = invariants_path
        self.plugin_root = plugin_root
        self.state_path = self.hub_dir / "LOCAL_HUB_STATE.json"
        self.overlay_rules_path = self.hub_dir / "overlay" / "LOCAL_FEEDBACK_RULES.md"

    def _now_iso(self) -> str:
        return datetime.datetime.now(JST).isoformat(timespec="seconds")

    def _get_core_version(self) -> str:
        if self.manifest_path.exists():
            try:
                return json.loads(self.manifest_path.read_text(encoding="utf-8")).get("version", "2.5.0")
            except (json.JSONDecodeError, OSError):
                pass
        return "2.5.0"

    def _resolve_claim_file(self, claim_path_str: str) -> Optional[pathlib.Path]:
        src = pathlib.Path(claim_path_str)
        if src.is_file():
            return src
        for sub in ("inbox", "pending_approval", "active_claims"):
            for cand in [self.hub_dir / sub / claim_path_str, self.hub_dir / sub / f"{claim_path_str}.md"]:
                if cand.is_file():
                    return cand
        return None

    def init_hub(self) -> None:
        """Knowledge Hub ディレクトリおよび初期状態ファイルのプロビジョニング"""
        for sub in ["inbox", "pending_approval", "overlay/skills", "active_claims", "archive/upstreamed", "suspended", "rejected"]:
            (self.hub_dir / sub).mkdir(parents=True, exist_ok=True)

        core_ver = self._get_core_version()
        if not self.state_path.exists():
            init_st = {"base_core_version": core_ver, "last_reconciled_at": self._now_iso(), "active_overlay_claims": [], "upstreamed_history": []}
            self.state_path.write_text(json.dumps(init_st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        if not self.overlay_rules_path.exists():
            header = (
                "# 環境共通 ローカルオーバーレイ規約 (LOCAL_FEEDBACK_RULES)\n\n"
                "> 本ファイルは Central Knowledge Hub の有効原票からクリーン再生成される拡張規約層（上限80行）です。\n\n"
                "現在、ローカルオーバーレイに適用中の追加規約はありません（すべて公式 Immutable Core に統合済みです）。\n"
            )
            self.overlay_rules_path.write_text(header, encoding="utf-8")

    def parse_claim(self, md_path: pathlib.Path) -> Dict[str, Any]:
        """Claim Markdown からメタデータとルール箇条書きを抽出"""
        text = md_path.read_text(encoding="utf-8")
        meta: Dict[str, Any] = {
            "claim_id": md_path.stem, "pattern_id": "", "title": md_path.stem,
            "applicable_profiles": ["ALL"], "category": "GENERAL", "distilled_rules": []
        }
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
        body = text
        if fm_match:
            fm_text, body = fm_match.group(1), fm_match.group(2)
            for line in fm_text.splitlines():
                m = re.match(r"^([a-zA-Z0-9_]+):\s*(.+)$", line.strip())
                if m:
                    k, v = m.group(1), m.group(2).strip().strip('"').strip("'")
                    if k in ("claim_id", "pattern_id", "title", "category"):
                        meta[k] = v
                    elif k == "applicable_profiles":
                        meta[k] = [p.strip() for p in re.findall(r"[A-Za-z0-9_ -]+", v) if p.strip()]

        sec3 = re.search(r"##\s*3\..*?\n(.*?)(?=\n##\s*[45]\.|\Z)", body, re.DOTALL)
        target_block = sec3.group(1) if sec3 else body
        rules: List[str] = []
        for ln in target_block.splitlines():
            s = ln.strip()
            if s.startswith("- ") or s.startswith("* "):
                clean_ln = re.sub(r"\[?(PAT-[A-Z0-9-]+|CLAIM-[A-Za-z0-9-]+)\]?\s*:?\s*", "", s[2:]).strip()
                if clean_ln:
                    rules.append(clean_ln)
        meta["distilled_rules"] = rules
        return meta

    def rebuild_overlay(self) -> None:
        """active_claims/ から LOCAL_FEEDBACK_RULES.md をクリーン再生成"""
        self.init_hub()
        active_dir = self.hub_dir / "active_claims"
        core_ver = self._get_core_version()
        state = {"base_core_version": core_ver, "active_overlay_claims": [], "upstreamed_history": []}
        if self.state_path.exists():
            try:
                state = json.loads(self.state_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

        claims_meta = [self.parse_claim(cp) for cp in sorted(active_dir.glob("CLAIM-*.md"))]
        lines = [
            "# 環境共通 ローカルオーバーレイ規約 (LOCAL_FEEDBACK_RULES)", "",
            "> 本ファイルは Central Knowledge Hub の有効原票から自動生成される拡張規約層（絶対上限 80行）です。", ""
        ]
        now_iso = self._now_iso()
        new_active_list = []

        if not claims_meta:
            lines.append("現在、ローカルオーバーレイに適用中の追加規約はありません（すべて公式 Immutable Core に統合済みです）。")
        else:
            by_cat: Dict[str, List[Dict[str, Any]]] = {}
            for cm in claims_meta:
                cat = cm["category"] or "GENERAL"
                by_cat.setdefault(cat, []).append(cm)
                new_active_list.append({
                    "claim_id": cm["claim_id"], "pattern_id": cm["pattern_id"], "applied_at": now_iso,
                    "overlay_target": "overlay/LOCAL_FEEDBACK_RULES.md", "distilled_rule_text": " / ".join(cm["distilled_rules"])
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
            print(f"⚠️ [Warning] LOCAL_FEEDBACK_RULES.md が 80行バジェットを超過しています ({len(lines)}行)。", file=sys.stderr)
            lines = lines[:79] + ["- (※行数上限80行到達のため以降省略。要Core昇格コンパイル)"]

        self.overlay_rules_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        state.update({"base_core_version": core_ver, "last_reconciled_at": now_iso, "active_overlay_claims": new_active_list})
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"✅ [Rebuild Overlay] active_claims ({len(claims_meta)}件) から LOCAL_FEEDBACK_RULES.md ({len(lines)}行) をクリーン再生成しました。")

    def run_status(self) -> None:
        """状態診断レポートの出力"""
        self.init_hub()
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8")) if self.manifest_path.exists() else {}
        state = json.loads(self.state_path.read_text(encoding="utf-8")) if self.state_path.exists() else {}

        counts = {sub: len(list((self.hub_dir / sub).glob("*.md"))) for sub in [
            "inbox", "pending_approval", "active_claims", "archive/upstreamed", "suspended", "rejected"
        ]}
        overlay_lines = len(self.overlay_rules_path.read_text(encoding="utf-8").splitlines()) if self.overlay_rules_path.exists() else 0

        print("=" * 76 + "\n📊 [Central Knowledge Hub & Reconciler] 状態診断レポート\n" + "=" * 76)
        print(f"  ・Immutable Core Version : {manifest.get('version', 'unknown')} (吸収済パターン: {len(manifest.get('absorbed_patterns', []))}件)")
        print(f"  ・Hub Base Core Version  : {state.get('base_core_version', 'unknown')}")
        print(f"  ・Local Overlay 行数     : {overlay_lines} / 80 行 ({self.overlay_rules_path})\n" + "-" * 76)
        for label, sub in [
            ("📥 inbox/ (未監査原票)", "inbox"), ("🗂️ pending_approval/ (承認・裁定待)", "pending_approval"),
            ("🧩 active_claims/ (Overlay適用中)", "active_claims"), ("📦 archive/upstreamed/ (Core吸収済)", "archive/upstreamed"),
            ("⏸️ suspended/ (仕様衝突保留)", "suspended"), ("🚫 rejected/ (監査棄却履歴)", "rejected")
        ]:
            files = sorted((self.hub_dir / sub).glob("*.md"))
            print(f"  {label:<38}: {len(files)} 件")
            for f in files:
                print(f"     - {f.name}")
        print("=" * 76)

    def run_upgrade(self) -> None:
        """新 Immutable Core と照合し、吸収済原票の自動退役を実行"""
        self.init_hub()
        if not self.manifest_path.exists():
            print("❌ PIPELINE_MANIFEST.json が見つかりません。", file=sys.stderr)
            sys.exit(1)

        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        state = json.loads(self.state_path.read_text(encoding="utf-8")) if self.state_path.exists() else {"upstreamed_history": []}
        core_ver = manifest.get("version", "2.5.0")

        absorbed_pat_ids = {e["pattern_id"] for e in manifest.get("absorbed_patterns", []) if e.get("pattern_id")}
        absorbed_claim_ids = {cid for e in manifest.get("absorbed_patterns", []) for cid in e.get("claim_ids", [])}

        active_dir, inbox_dir, archive_dir = self.hub_dir / "active_claims", self.hub_dir / "inbox", self.hub_dir / "archive" / "upstreamed"
        now_iso = self._now_iso()
        retired_count, retained_count = 0, 0

        for target_dir in (active_dir, inbox_dir):
            for cp in sorted(target_dir.glob("CLAIM-*.md")):
                text = cp.read_text(encoding="utf-8")
                cid = cp.stem
                m_pat = re.search(r'^pattern_id:\s*["\']?([A-Za-z0-9-]+)["\']?', text, re.MULTILINE)
                pid = m_pat.group(1) if m_pat else ""

                if cid in absorbed_claim_ids or (pid and pid in absorbed_pat_ids):
                    dest = archive_dir / cp.name
                    dest.write_text(re.sub(r'^status:\s*".*"$', 'status: "UPSTREAMED"', text, flags=re.MULTILINE), encoding="utf-8")
                    if cp.resolve() != dest.resolve():
                        cp.unlink()
                    retired_count += 1
                    state.setdefault("upstreamed_history", []).append({
                        "claim_id": cid, "pattern_id": pid, "retired_at_version": core_ver,
                        "retired_at": now_iso, "resolution": "FAST_PATH_ID_MATCH", "archived_path": f"archive/upstreamed/{cp.name}"
                    })
                    print(f"  📦 [Pattern A: ID一致自動退役] {cp.name} ({pid}) -> archive/upstreamed/")
                elif target_dir == active_dir:
                    retained_count += 1
                    print(f"  🧩 [Pattern C: 独自知見継続保持] {cp.name} ({pid})")

        state.update({"base_core_version": core_ver, "last_reconciled_at": now_iso})
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"✅ 照合完了: 自動退役 {retired_count} 件 / 継続保持 {retained_count} 件")
        self.rebuild_overlay()

    def activate_claim(self, claim_path_str: str) -> None:
        """指定原票を active_claims/ へ昇格（一意性検証を含む）"""
        self.init_hub()
        src = self._resolve_claim_file(claim_path_str)
        if not src:
            print(f"❌ 指定された原票が見つかりません: {claim_path_str}", file=sys.stderr)
            sys.exit(1)

        fname = src.name
        dst = self.hub_dir / "active_claims" / fname
        text = src.read_text(encoding="utf-8")
        pid_m = re.search(r'^pattern_id:\s*["\']?([^"\']+)["\']?', text, re.MULTILINE)
        pid = pid_m.group(1).strip() if pid_m else ""

        # pattern_id 一意性バリデーション
        if pid:
            for check_dir in [self.hub_dir / "active_claims", self.hub_dir / "archive" / "upstreamed"]:
                if not check_dir.is_dir():
                    continue
                for other in check_dir.glob("CLAIM-*.md"):
                    if other.resolve() in (dst.resolve(), src.resolve()):
                        continue
                    m = re.search(r'^pattern_id:\s*["\']?([^"\']+)["\']?', other.read_text(encoding="utf-8"), re.MULTILINE)
                    if m and m.group(1).strip() == pid:
                        print(f"❌ [Error] pattern_id '{pid}' は既に他の原票 ({other.name}) で使用されています。\n   リナンバリングを実施してください。", file=sys.stderr)
                        sys.exit(1)

        dst.write_text(re.sub(r'^status:\s*".*"$', 'status: "OVERLAY_ACTIVE"', text, flags=re.MULTILINE), encoding="utf-8")
        if src.resolve() != dst.resolve() and src.parent.name in ("inbox", "pending_approval"):
            src.unlink()

        print(f"✅ 原票を active_claims/ へ昇格しました: {fname}")
        self.rebuild_overlay()

    def reject_claim(self, claim_path_str: str, reason: str = "Rejected by Semantic Auditor") -> None:
        """指定原票を rejected/ へ移動・記録"""
        self.init_hub()
        src = self._resolve_claim_file(claim_path_str)
        if not src:
            print(f"❌ 指定された原票が見つかりません: {claim_path_str}", file=sys.stderr)
            sys.exit(1)

        fname = src.name
        dst = self.hub_dir / "rejected" / fname
        text = re.sub(r'^status:\s*".*"$', 'status: "REJECTED"', src.read_text(encoding="utf-8"), flags=re.MULTILINE)
        text += f"\n\n---\n## 監査棄却記録 (Rejection Record)\n- **棄却日時**: {self._now_iso()}\n- **棄却理由**: {reason}\n"
        dst.write_text(text, encoding="utf-8")
        if src.resolve() != dst.resolve() and src.parent.name in ("inbox", "pending_approval", "active_claims"):
            src.unlink()

        print(f"🚫 原票を rejected/ へ移動・永続記録しました: {fname}")
        self.rebuild_overlay()

    def audit_budget(self) -> None:
        """純度・行数バジェットの機械的検証 (New Gate 4)"""
        self.init_hub()
        errors: List[str] = []
        checked = 0

        def check_file(p: pathlib.Path, limit: int, check_pat_id: bool = True) -> None:
            nonlocal checked
            if not p.exists():
                return
            checked += 1
            lines = p.read_text(encoding="utf-8").splitlines()
            rel = p.relative_to(self.plugin_root) if p.is_relative_to(self.plugin_root) else p
            if len(lines) > limit:
                errors.append(f"[Budget Exceeded] {rel}: {len(lines)} 行 (上限 {limit} 行)")
            if check_pat_id:
                for idx, ln in enumerate(lines, 1):
                    if re.search(r'\bPAT-[A-Z]+-\d{3}\b', ln) or re.search(r'\bCLAIM-\d{8}-[A-Za-z0-9_-]+\b', ln):
                        errors.append(f"[Lineage Impurity] {rel}:{idx} に特定の履歴IDが混入しています: {ln.strip()}")

        check_file(self.plugin_root / "rules" / "AGENTS.md", 220, True)
        for ap in sorted((self.plugin_root / "agents").glob("*.md")):
            check_file(ap, 120, True)
        for sp in sorted((self.plugin_root / "skills").glob("*/SKILL.md")):
            check_file(sp, 120, True)
        if self.overlay_rules_path.exists():
            check_file(self.overlay_rules_path, 80, True)

        for pp in sorted((self.plugin_root / "skills").glob("*/PURPOSE.md")):
            errors.append(f"[Deprecated File] 廃止された個別 PURPOSE.md が残存しています: {pp.relative_to(self.plugin_root)}")

        if errors:
            print("🚨 [New Gate 4: 純度・絶対行数バジェット監査 FAIL]", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            sys.exit(1)
        print(f"✅ [New Gate 4: 純度・絶対行数バジェット監査 PASS] 全 {checked} ファイルが上限行数以内かつ履歴ID混入ゼロです。")

    def export_claims(self, dest_dir: pathlib.Path) -> None:
        """未吸収原票のエクスポート"""
        self.init_hub()
        dest_dir.mkdir(parents=True, exist_ok=True)
        count = sum(
            shutil.copy(cp, dest_dir / cp.name) is not None
            for sub in ("active_claims", "inbox")
            for cp in (self.hub_dir / sub).glob("CLAIM-*.md")
        )
        print(f"📤 [Export Claims] 計 {count} 件の未吸収知見原票を {dest_dir} へエクスポートしました。")


def main() -> None:
    parser = argparse.ArgumentParser(description="Central Knowledge Hub Reconciler")
    parser.add_argument("--hub-dir", type=str, default=os.environ.get("KNOWLEDGE_HUB_DIR", str(pathlib.Path.home() / ".gemini" / "knowledge-hub")))
    parser.add_argument("--plugin-root", type=str, default=str(pathlib.Path(__file__).resolve().parent.parent))

    subparsers = parser.add_subparsers(dest="command")
    for cmd_name in ("init-hub", "rebuild-overlay", "status", "upgrade", "audit-budget"):
        subparsers.add_parser(cmd_name)

    p_act = subparsers.add_parser("activate-claim")
    p_act.add_argument("claim", type=str, help="Claim file path or ID")

    p_rej = subparsers.add_parser("reject-claim")
    p_rej.add_argument("claim", type=str, help="Claim file path or ID")
    p_rej.add_argument("reason", type=str, nargs="?", default="Rejected by Semantic Auditor")

    p_exp = subparsers.add_parser("export-claims")
    p_exp.add_argument("dest", type=str, nargs="?", default="./exported-claims")

    args = parser.parse_args()
    hub_dir, plugin_root = pathlib.Path(args.hub_dir), pathlib.Path(args.plugin_root)
    reconciler = KnowledgeHubReconciler(hub_dir, plugin_root / "PIPELINE_MANIFEST.json", plugin_root / "rules" / "CORE_INVARIANTS.md", plugin_root)

    cmd = args.command or "status"
    if cmd == "init-hub":
        reconciler.init_hub()
        print(f"✅ Knowledge Hub ({hub_dir}) を初期化しました。")
    elif cmd == "rebuild-overlay":
        reconciler.rebuild_overlay()
    elif cmd == "status":
        reconciler.run_status()
    elif cmd == "upgrade":
        print("🔄 [Upgrade Reconciler] 新 Immutable Core の PIPELINE_MANIFEST.json と Local Hub を照合しています...")
        reconciler.run_upgrade()
    elif cmd == "activate-claim":
        reconciler.activate_claim(args.claim)
    elif cmd == "reject-claim":
        reconciler.reject_claim(args.claim, args.reason)
    elif cmd == "audit-budget":
        reconciler.audit_budget()
    elif cmd == "export-claims":
        reconciler.export_claims(pathlib.Path(args.dest))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
