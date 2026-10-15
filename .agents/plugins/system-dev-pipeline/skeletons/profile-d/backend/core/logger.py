import logging
import json
import uuid
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(JST).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "log_id": getattr(record, "log_id", str(uuid.uuid4())),
        }
        return json.dumps(log_data, ensure_ascii=False)

def setup_logger():
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.handlers = [handler]
    return logger

logger = setup_logger()
