import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    HOST = os.getenv("HONEYPOT_HTTP_HOST", "0.0.0.0")
    PORT = int(os.getenv("HONEYPOT_HTTP_PORT", 80))
    LOG_FILE = os.getenv("LOG_FILE_NAME", "web.log")
    SERVER_BANNER = os.getenv("SERVER_BANNER", "Apache/2.4.41 (Ubuntu)")
