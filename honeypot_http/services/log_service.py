import logging
from config.settings import Settings

class LogService:
    def __init__(self):
        logging.basicConfig(
            filename=Settings.LOG_FILE,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def log_request(self, ip, method, path, params, headers, body):
        headers_str = ", ".join([f"{k}: {v}" for k, v in headers.items()])
        logging.info(
            f"IP: {ip} | Method: {method} | Path: {path} | Params: {dict(params)} | Headers: {{{headers_str}}} | Body: {body}"
        )
