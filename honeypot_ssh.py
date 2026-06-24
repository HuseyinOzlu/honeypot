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
    try:
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(host_key)
        transport.local_version = "SSH-2.0-OpenSSH_8.9p1ubuntu1.6"

        server = SSHHoneypot()

        # SSH el sıkışmasını başlatır ve banner gönderir
        transport.start_server(server=server)

        # Gelen channel isteklerini bekler(maksimum 20 sn)
        chan = transport.accept(20)
        if chan is None:
            print("[-] İstemci kanali basariyla acilamadi veya süre asimina ugradi.")
            return
        print("[+] İstemci kanali basariyla acildi!")

        # İstemci baglandiktan sonra baglantiyi acik tutmak veya 
        # sahte bir terminal simüle etmek icin buraya kod ekleyebiliriz
        # Örn: chan.send("Welcome to Ubuntu...\r\n")
        
        # Test icin biraz acik birakabilirz
        chan.send("Ubuntu 22.04.1 LTS\r\n")
        chan.send("Honeypot simulation\r\n\r\n")
        chan.send("attacker@hostname:~# ")
        chan.close()
        
    except Exception as e:
        print(f"[-] Hata olustu: {e}")
    finally:
        try:
            transport.close()
        except:
            pass

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
