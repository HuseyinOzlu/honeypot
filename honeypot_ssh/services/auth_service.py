import paramiko
from services.log_service import LogService

class AuthService:
    def __init__(self):
        self.logger = LogService()

    def process_login(self, username, password, client_ip):
        self.logger.log_attempt(username, password, client_ip, "ACCEPTED")
        return paramiko.AUTH_SUCCESSFUL