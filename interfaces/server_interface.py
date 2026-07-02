import paramiko
from services import AuthService

class HoneypotInterface(paramiko.ServerInterface):
    def __init__(self, client_ip):
        self.client_ip = client_ip
        self.auth_service = AuthService()

    def check_auth_password(self, username, password):
        return self.auth_service.process_login(username, password, self.client_ip)

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_shell_request(self, channel):
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True