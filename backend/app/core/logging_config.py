import logging
import sys
from pythonjsonlogger import jsonlogger
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def setup_logging():
    """
    Set up application-wide structured logging for stdout and file.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(ip)s %(user_email)s %(request_id)s"
    )

    # Console
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # File
    file_handler = RotatingFileHandler(LOG_DIR / "app.log", maxBytes=10*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Audit
    audit_handler = RotatingFileHandler(LOG_DIR / "audit.log", maxBytes=5*1024*1024, backupCount=3)
    audit_handler.setFormatter(formatter)
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    audit_logger.addHandler(audit_handler)