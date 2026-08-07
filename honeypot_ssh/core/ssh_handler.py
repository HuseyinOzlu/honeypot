import paramiko
import json
from interfaces.server_interface import HoneypotInterface
from config import settings
from services import LogService
from core.vfs import VirtualFileSystem
from core.shell import Shell

class SSHHandler:
    def __init__(self, client_socket, client_ip, host_key):
        self.client_socket = client_socket
        self.client_ip = client_ip
        self.host_key = host_key
        self.logger = LogService()
        self.commands_config = self._load_commands()
    
    def _load_commands(self):
        try:
            with open(settings.COMMANDS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Error Command File is not imported: {e}")
            return {"commands": {}, "default_error": "bash: {cmd}: command not found\n"}

    def handle(self):
        try:
            transport = paramiko.Transport(self.client_socket)
            transport.add_server_key(self.host_key)
            transport.local_version = settings.BANNER

            interface = HoneypotInterface(self.client_ip)
            transport.start_server(server=interface)

            chan = transport.accept(20)
            if chan:
                self.handle_shell(chan)
        except paramiko.SSHException as e:
            print(f"[-] SSH Error ({self.client_ip}: {e})")
        except (ConnectionResetError, EOFError):
            print(f"[-] Connection Closed ({self.client_ip})")
        except Exception as e:
            print(f"[-] Handshake Error ({self.client_ip}: {e})")
        finally:
            transport.close()

    def handle_shell(self, chan):
        try:
            vfs = VirtualFileSystem(self.commands_config)
            shell = Shell(vfs, chan, self.commands_config, self.client_ip)
            
            chan.send("\r\nWelcome to Ubuntu 22.04.1 LTS (GNU/Linux 5.15.0-43-generic x86_64)\r\n\r\n")
            chan.send(" * Documentation:  https://help.ubuntu.com\r\n")
            chan.send(" * Management:     https://landscape.canonical.com\r\n")
            chan.send(" * Support:        https://ubuntu.com/advantage\r\n\r\n")
            
            shell.run()
        except Exception as e:
            pass
        finally:
            chan.close()