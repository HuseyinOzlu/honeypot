import unittest
import json
import time
import sys
import io
from core.vfs import VirtualFileSystem
from core.shell import Shell, parse_command_line, parse_segment

class DummyChannel:
    def __init__(self):
        self.sent_data = []
        self.recv_data = []
        
    def send(self, data):
        if isinstance(data, str):
            self.sent_data.append(data)
        else:
            self.sent_data.append(data.decode('utf-8'))
            
    def recv(self, size):
        if not self.recv_data:
            return b""
        val = self.recv_data.pop(0)
        if isinstance(val, str):
            return val.encode('utf-8')
        return val

    def recv_ready(self):
        return len(self.recv_data) > 0

class TestVFSShell(unittest.TestCase):
    def setUp(self):
        # Setup basic mock config
        self.commands_config = {
            "fs": {
                "/": {
                    "type": "dir",
                    "files": {
                        "bin": {"type": "dir"},
                        "etc": {"type": "dir"},
                        "home": {"type": "dir"}
                    }
                },
                "/home": {
                    "type": "dir",
                    "files": {
                        "ubuntu": {"type": "dir"}
                    }
                },
                "/home/ubuntu": {
                    "type": "dir",
                    "files": {
                        "test.txt": {"type": "file", "content": "Hello World\nLine 2\n"}
                    }
                },
                "/etc": {
                    "type": "dir",
                    "files": {
                        "passwd": {"type": "file", "content": "root:x:0:0...\nubuntu:x:1000...\n"}
                    }
                }
            },
            "commands": {
                "whoami": {"output": "ubuntu\n"}
            }
        }
        self.vfs = VirtualFileSystem(self.commands_config)
        self.chan = DummyChannel()
        self.shell = Shell(self.vfs, self.chan, self.commands_config, "127.0.0.1")

    def test_vfs_path_resolution(self):
        self.assertEqual(self.vfs.resolve_path("/home/ubuntu", "test.txt"), "/home/ubuntu/test.txt")
        self.assertEqual(self.vfs.resolve_path("/home/ubuntu", "../ubuntu/test.txt"), "/home/ubuntu/test.txt")
        self.assertEqual(self.vfs.resolve_path("/home/ubuntu", "../../etc/passwd"), "/etc/passwd")

    def test_vfs_metadata_defaults(self):
        stat_root = self.vfs.stat("/")
        self.assertEqual(stat_root["owner"], "root")
        self.assertEqual(stat_root["group"], "root")
        self.assertEqual(stat_root["mode"], 0o755)

        stat_user = self.vfs.stat("/home/ubuntu/test.txt")
        self.assertEqual(stat_user["owner"], "ubuntu")
        self.assertEqual(stat_user["mode"], 0o644)

    def test_vfs_chmod_chown(self):
        # Chmod numeric
        self.assertTrue(self.vfs.chmod("/home/ubuntu/test.txt", "755"))
        self.assertEqual(self.vfs.stat("/home/ubuntu/test.txt")["mode"], 0o755)
        
        # Chmod symbolic
        self.assertTrue(self.vfs.chmod("/home/ubuntu/test.txt", "+x"))
        self.assertEqual(self.vfs.stat("/home/ubuntu/test.txt")["mode"], 0o755) # was already exec
        
        self.assertTrue(self.vfs.chmod("/home/ubuntu/test.txt", "-x"))
        self.assertEqual(self.vfs.stat("/home/ubuntu/test.txt")["mode"], 0o644)

        # Chown
        self.assertTrue(self.vfs.chown("/home/ubuntu/test.txt", "root", "root"))
        stat_info = self.vfs.stat("/home/ubuntu/test.txt")
        self.assertEqual(stat_info["owner"], "root")
        self.assertEqual(stat_info["group"], "root")

    def test_command_line_parsing(self):
        segs = parse_command_line("echo 'hello && world'; ls -l || whoami")
        self.assertEqual(len(segs), 3)
        self.assertEqual(segs[0], ("echo 'hello && world'", ";"))
        self.assertEqual(segs[1], ("ls -l", "||"))
        self.assertEqual(segs[2], ("whoami", None))

    def test_segment_parsing(self):
        pipe_cmds, redir_file, append = parse_segment("cat test.txt | grep Line >> out.txt")
        self.assertEqual(pipe_cmds, ["cat test.txt", "grep Line"])
        self.assertEqual(redir_file, "out.txt")
        self.assertTrue(append)

    def test_redirection_and_piping(self):
        # Run echo redirected to file
        self.shell.execute("echo 'piped content' | grep piped > /home/ubuntu/out.txt")
        self.assertTrue(self.vfs.exists("/home/ubuntu/out.txt"))
        self.assertEqual(self.vfs.read_file("/home/ubuntu/out.txt"), "piped content\n")

    def test_builtins(self):
        # cd & pwd
        success, out = self.shell._run_single_command("cd /etc")
        self.assertTrue(success)
        self.assertEqual(self.shell.current_dir, "/etc")
        
        success, out = self.shell._run_single_command("pwd")
        self.assertTrue(success)
        self.assertEqual(out, "/etc\n")
        
        # whoami
        success, out = self.shell._run_single_command("whoami")
        self.assertTrue(success)
        self.assertEqual(out, "ubuntu\n")

    def test_grep_wc(self):
        # grep
        success, out = self.shell._run_single_command("grep Line /home/ubuntu/test.txt")
        self.assertTrue(success)
        self.assertEqual(out, "Line 2\n")

        # wc -l
        success, out = self.shell._run_single_command("wc -l /home/ubuntu/test.txt")
        self.assertTrue(success)
        self.assertEqual(out, "2 /home/ubuntu/test.txt\n")

    def test_autocomplete(self):
        # Autocomplete command
        self.shell.buffer = "whoa"
        self.shell.cursor_idx = 4
        self.shell.handle_autocomplete()
        self.assertEqual(self.shell.buffer, "whoami ")

        # Autocomplete path
        self.shell.buffer = "cat /home/ubuntu/tes"
        self.shell.cursor_idx = 20
        self.shell.handle_autocomplete()
        self.assertEqual(self.shell.buffer, "cat /home/ubuntu/test.txt ")

if __name__ == "__main__":
    unittest.main()
