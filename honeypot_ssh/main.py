import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

from config import settings
from core import HoneypotServer

def main():
    try:
        server = HoneypotServer(host=settings.HOST, port=settings.PORT)
        server.start()
    except KeyboardInterrupt:
        print("\n[-] Honeypot downing....")

if __name__ == "__main__":
    main()