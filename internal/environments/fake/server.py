import socket
import json
import logging
from internal.environments.fake.vfs import VirtualFileSystem
from internal.environments.fake.shell import FakeShell

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [FakeEnvironment] %(message)s")

def start_rpc_server(host: str = "0.0.0.0", port: int = 6000):
    """
    TCP Socket server that acts as the backend for `FakeEnvironment` sessions.
    Receives JSON command execution requests from Go Gateway and returns simulated outputs.
    """
    vfs = VirtualFileSystem()
    shell = FakeShell(vfs)

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen(100)
    logging.info(f"FakeEnvironment VFS Worker Listening on TCP {host}:{port}...")

    try:
        while True:
            client_sock, addr = server_sock.accept()
            try:
                data = client_sock.recv(4096).decode("utf-8").strip()
                if not data:
                    client_sock.close()
                    continue
                
                req = json.loads(data)
                cmd = req.get("command", "")
                logging.info(f"Executing simulated VFS command: '{cmd}' from {addr}")
                output = shell.execute(cmd)
                resp = json.dumps({"output": output, "cwd": vfs.cwd}) + "\n"
                client_sock.sendall(resp.encode("utf-8"))
            except Exception as e:
                logging.error(f"Error executing VFS request: {e}")
            finally:
                client_sock.close()
    except KeyboardInterrupt:
        logging.info("Shutting down FakeEnvironment worker cleanly.")
    finally:
        server_sock.close()

if __name__ == "__main__":
    start_rpc_server()
