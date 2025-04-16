import logging
import os

# Ensure logs directory exists
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Basic config for logging to terminal and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "backend.log")),  # Logs to file
        logging.StreamHandler()  # Logs to terminal
    ]
)

logger = logging.getLogger(__name__)
