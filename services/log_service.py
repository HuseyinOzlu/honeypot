import logging
from config import settings

class LogService:
    def __init__(self):
        logging.basicConfig(
            filename=settings.LOG_FILE,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def log_attempt(self, username, password, ip, status):
        logging.info(f"Connection, -> IP: {ip} | KBY: {username} | Password: {password} | Status: {status}")