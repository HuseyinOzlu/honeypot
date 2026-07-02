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

    def log_command(self, ip, command):
        logging.info(f"Command executed -> IP: {ip} | Command: {command}")

    def log_download(self, ip, url, file_path):
        logging.info(f"Download attempted -> IP: {ip} | URL: {url} | SavedTo: {file_path}")