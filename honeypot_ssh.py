import logging
import socket
import threading
import paramiko

logging.basicConfig(filename="honeypot.log", level=logging.INFO)

host_key = paramiko.RSAKey.generate(2048)

class SSHHoneypot(paramiko.ServerInterface):
    def check_auth_password(self, username, password):
        logging.info(f"Login attempt - user :{username}, pass {password}")
        return paramiko.AUTH_FAILED

def client_handler(client_socket):
    transport = paramiko.Transport(client_socket)
    transport.add_server_key(host_key)
    transport.local_version = "SSH-2.0-OpenSSH_8.9p1ubuntu1.6"

    server = SSHHoneypot()

    try:
        transport.start_server(server=server)
        transport.accept(20)
    except Exception as e:
        print(e)

def start_server(port=2222):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', port))
    server.listen(100)

    print(f"[+] Honeypot listening on port {port}")

    while True:
        client, addr = server.accept()
        print(f"[+] Connection from {addr}")
        threading.Thread(target=client_handler, args=(client,)).start()

if __name__ == "__main__":
    start_server()
