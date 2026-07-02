import os
from dotenv import load_dotenv

# .env file
load_dotenv()

class Settings:
    HOST = os.getenv("HONEYPOT_HOST","0.0.0.0")
    PORT = int(os.getenv("HONEYPOT_PORT", 2222))
    LOG_FILE = os.getenv("LOG_FILE_NAME", "honeypot.log")
    BANNER = os.getenv("SSH_BANNER", "SSH-2.0-OpenSSH_8.9p1Ubuntu1.6")
    COMMANDS_FILE = os.getenv("COMMANDS_FILE", os.path.join(os.path.dirname(__file__), "commands.json"))