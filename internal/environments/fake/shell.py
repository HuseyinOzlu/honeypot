import shlex
from typing import Tuple
from internal.environments.fake.vfs import VirtualFileSystem

class FakeShell:
    """
    Lightweight Bash emulator for Low-Interaction fallback sessions.
    Interprets commands against the VirtualFileSystem and returns simulated outputs.
    """
    def __init__(self, vfs: VirtualFileSystem):
        self.vfs = vfs
        self.env = {
            "USER": "root",
            "HOME": "/root",
            "SHELL": "/bin/bash",
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "TERM": "xterm-256color"
        }

    def execute(self, cmd_line: str) -> str:
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return ""
        
        # Handle simple redirections like `echo hello > /tmp/a.txt`
        if ">" in cmd_line:
            parts = cmd_line.split(">", 1)
            left = parts[0].strip()
            right = parts[1].strip()
            append = False
            if right.startswith(">"):
                append = True
                right = right[1:].strip()
            output = self._run_single_cmd(left)
            return self.vfs.write_file(right, output, append=append)

        return self._run_single_cmd(cmd_line)

    def _run_single_cmd(self, cmd_line: str) -> str:
        try:
            tokens = shlex.split(cmd_line)
        except ValueError:
            tokens = cmd_line.split()

        if not tokens:
            return ""

        cmd = tokens[0]
        args = tokens[1:]

        if cmd in ("exit", "logout"):
            return "logout\nConnection to host closed.\n"
        elif cmd == "pwd":
            return f"{self.vfs.cwd}\n"
        elif cmd == "cd":
            target = args[0] if args else self.env["HOME"]
            resolved = self.vfs._resolve_path(target)
            node = self.vfs._get_node(resolved)
            if node and node.get("type") == "dir":
                self.vfs.cwd = resolved
                return ""
            return f"bash: cd: {target}: No such file or directory\n"
        elif cmd == "ls":
            path = args[0] if args and not args[0].startswith("-") else ""
            return self.vfs.list_dir(path)
        elif cmd == "cat":
            if not args:
                return ""
            return "".join(self.vfs.read_file(arg) for arg in args if not arg.startswith("-"))
        elif cmd == "echo":
            return " ".join(args) + "\n"
        elif cmd == "whoami":
            return f"{self.env['USER']}\n"
        elif cmd == "id":
            return "uid=0(root) gid=0(root) groups=0(root)\n"
        elif cmd == "uname":
            if "-a" in args:
                return "Linux ip-172-16-0-101 5.15.0-89-generic #99-Ubuntu SMP Mon Oct 2 15:18:56 UTC 2023 x86_64 x86_64 x86_64 GNU/Linux\n"
            return "Linux\n"
        elif cmd == "ps":
            return "  PID TTY          TIME CMD\n    1 ?        00:00:01 init\n  142 pts/0    00:00:00 bash\n  198 pts/0    00:00:00 ps\n"
        elif cmd in ("top", "htop"):
            return "top - 15:42:10 up 14 days,  3:12,  1 user,  load average: 0.02, 0.04, 0.01\nTasks:  98 total,   1 running,  97 sleeping,   0 stopped,   0 zombie\n%Cpu(s):  0.3 us,  0.1 sy,  0.0 ni, 99.6 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st\nMiB Mem :   3936.2 total,   2140.8 free,    812.4 used,    983.0 buff/cache\n"
        elif cmd in ("wget", "curl"):
            return f"{cmd}: simulated payload download captured and forwarded to Telemetry Vault.\n"
        else:
            return f"bash: {cmd}: command not found\n"
