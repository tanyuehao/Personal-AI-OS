"""
Personal AI OS - Logger
结构化日志系统
"""
import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any


class StructuredFormatter(logging.Formatter):
    """结构化日志格式"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """获取日志实例"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


def log_event(logger_name: str, level: str, message: str, data: Any = None):
    """记录事件日志"""
    logger = get_logger(logger_name)
    log_record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper()),
        "",
        0,
        message,
        (),
        None
    )
    if data:
        log_record.extra_data = data
    logger.handle(log_record)


# 预定义的日志实例
app_logger = get_logger("app")
api_logger = get_logger("api")
ai_logger = get_logger("ai")
db_logger = get_logger("db")
