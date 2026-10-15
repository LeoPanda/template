import os
import subprocess
import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from core.config import settings

router = APIRouter()

@router.get("/litestream/status")
def litestream_status():
    if not settings.LITESTREAM_BUCKET:
        return {
            "status": "disabled",
            "message": "LITESTREAM_BUCKET is not set.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    try:
        # litestream replication status実行
        res = subprocess.run(
            ["litestream", "replications", "-config", "/etc/litestream.yml"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return {
            "status": "active" if res.returncode == 0 else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "output": res.stdout.strip(),
        }
    except Exception as e:
        return {
            "status": "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }
