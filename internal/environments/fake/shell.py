import shlex
from typing import Dict
from internal.environments.fake.base import BaseCommand
from internal.environments.fake.vfs import VirtualFileSystem
from internal.environments.fake.constants import BashErrors

from internal.environments.fake.commands.fs import LsCommand, CatCommand, PwdCommand

class FakeShell:
    def __init__(self, vfs: VirtualFileSystem):
        self.vfs = vfs
        self.env = {
            "USER": "root",
            "ROOT": "/root",
            "SHELL":"/bin/bash",
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "TERM": "xterm-256color"
        }

        self.registery: Dict[str, BaseCommand] = {
            "ls":LsCommand(),
            "cat":CatCommand(),
            "pwd":PwdCommand()
        }
    def execute(self, cmd_line: str) -> str:
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return ""
        if ">" in cmd_line:
            return self._handle_redirection(cmd_line)

        return self._run_single_cmd(cmd_line)

    def _run_single_cmd(self, cmd_line: str) -> str:
        try:
            tokens = shlex.split(cmd_line)
        except ValueError:
            tokens = cmd_line.split()

        if not tokens:
            return ""

        cmd = tokens[0] # Örn: ls
        args = tokens[1:] # Örn ["-la"]

        if cmd in self.registery:
            return self.registery[cmd].execute(args, self.vfs, self.env)
        return BashErrors.CMD_NOT_FOUND.format(cmd=cmd)
    
    def _handle_redirection(self, cmd_line: str) -> str :
        parts = cmd_line.split(">",1)
        left = parts[0].strip()
        right = parts[1].strip()
        append = right.startswith(">")
        if append:
            right = right[1:].strip()
        output = self._run_single_cmd(left)
        return self.vfs.write_file(right, output, append=append)
    