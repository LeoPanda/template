#!/usr/bin/env bash
# ==============================================================================
# pipeline-reconciler.sh: V2.5 Central Knowledge Hub 管理 & Upgrade Reconciler
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RECONCILER_PY="${SCRIPT_DIR}/reconciler_core.py"
HUB_DIR="${KNOWLEDGE_HUB_DIR:-${HOME}/.gemini/knowledge-hub}"

MODE="${1:---status}"

case "$MODE" in
  --init-hub)
    exec python3 "$RECONCILER_PY" --hub-dir "$HUB_DIR" --plugin-root "$PLUGIN_ROOT" init-hub
    ;;
  --status)
    exec python3 "$RECONCILER_PY" --hub-dir "$HUB_DIR" --plugin-root "$PLUGIN_ROOT" status
    ;;
  --rebuild-overlay)
    exec python3 "$RECONCILER_PY" --hub-dir "$HUB_DIR" --plugin-root "$PLUGIN_ROOT" rebuild-overlay
    ;;
  --upgrade)
    exec python3 "$RECONCILER_PY" --hub-dir "$HUB_DIR" --plugin-root "$PLUGIN_ROOT" upgrade
    ;;
  --activate-claim)
    shift
    exec python3 "$RECONCILER_PY" --hub-dir "$HUB_DIR" --plugin-root "$PLUGIN_ROOT" activate-claim "${1:-}"
    ;;
  --reject-claim)
    shift
    exec python3 "$RECONCILER_PY" --hub-dir "$HUB_DIR" --plugin-root "$PLUGIN_ROOT" reject-claim "${1:-}" "${2:-Rejected by Semantic Auditor}"
    ;;
  --audit-budget)
    exec python3 "$RECONCILER_PY" --hub-dir "$HUB_DIR" --plugin-root "$PLUGIN_ROOT" audit-budget
    ;;
  --export-claims)
    shift
    exec python3 "$RECONCILER_PY" --hub-dir "$HUB_DIR" --plugin-root "$PLUGIN_ROOT" export-claims "${1:-./exported-claims}"
    ;;
  *)
    echo "Usage: $0 [--init-hub | --status | --rebuild-overlay | --upgrade | --activate-claim <CLAIM> | --reject-claim <CLAIM> [REASON] | --audit-budget | --export-claims [DIR]]"
    exit 1
    ;;
esac
