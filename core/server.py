import socket
import threading
import paramiko
from core.ssh_handler import SSHHandler

class HoneypotServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.host_key = paramiko.RSAKey.generate(2048)
    
    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(100)

        print(f"Honeypot Listening: {self.host}:{self.port}")

        while True:
            client_socket, client_addr = server_socket.accept()
            client_ip = client_addr[0]
            print(f"[+] Connection captured: {client_ip}")

            handler = SSHHandler(client_socket, client_ip, self.host_key)
            threading.Thread(target=handler.handle, daemon=True).start()