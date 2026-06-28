import paramiko
from interfaces.server_interface import HoneypotInterface
from config import settings


class SSHHandler:
    def __init__(self, client_socket, client_ip, host_key):
        self.client_socket = client_socket
        self.client_ip = client_ip
        self.host_key = host_key
    
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
            print(f"[!] SSH Hatasi ({self.client_ip}: {e})")
        except (ConnectionResetError, EOFError):
            print(f"[-] Baglanti kapatildi ({self.client_ip})")
        except Exception as e:
            print(f"[!] El sikisma hatasi ({self.client_ip}: {e})")
        finally:
            transport.close()

    def handle_shell(self, chan):
        try:
            # Ubuntu banner messages.
            chan.send("\r\nWelcome to Ubuntu 22.04.1 LTS (GNU/Linux 5.15.0-43-generic x86_64)\r\n\r\n")
            chan.send(" * Documentation:  https://help.ubuntu.com\r\n")
            chan.send(" * Management:     https://landscape.canonical.com\r\n")
            chan.send(" * Support:        https://ubuntu.com/advantage\r\n\r\n")
            
            prompt = "ubuntu@server:~$ "
            chan.send(prompt)
            buffer = ""
            while True:
                data = chan.recv(1024)
                if not data:
                    break
                
                for char in data.decode('utf-8', errors='ignore'):
                    if char in ('\r', '\n'):
                        cmd = buffer.strip()
                        chan.send("\r\n")
                        if cmd == "exit":
                            chan.send("logout\r\n")
                            return
                        elif cmd == "ls":
                            chan.send("bin  boot  dev  etc  home  lib  media  mnt  opt  run  sbin  srv  usr  var\r\n")
                        elif cmd == "whoami":
                            chan.send("ubuntu\r\n")
                        elif cmd == "id":
                            chan.send("uid=1000(ubuntu) gid=1000(ubuntu) groups=1000(ubuntu)\r\n")
                        elif cmd == "help":
                            chan.send("You can use: help, ls, whoami, id, exit\r\n")
                        elif cmd == "":
                            pass
                        else:
                            chan.send(f"bash: {cmd}: command not found\r\n")
                        
                        buffer = ""
                        chan.send(prompt)
                    elif char in ('\x7f', '\x08'):
                        # Backspace
                        if len(buffer) > 0:
                            buffer = buffer[:-1]
                            # If you want to delete a char in terminal, back to imlec and again rewrite
                            chan.send("\b \b")
                    elif char == '\x03':
                        # Ctrl+C 
                        chan.send("^C\r\n")
                        buffer = ""
                        chan.send(prompt)
                    else:
                        buffer += char
                        chan.send(char)
        except Exception as e:
            pass
        finally:
            chan.close()