from internal.environments.fake.base import BaseCommand
from typing import List, Dict, Any

class PwdCommand(BaseCommand):
    def execute(self, args: List[str], vfs: Any, env: Dict[str, str]) -> str:
        return f"{vfs.cwd}\n"

class LsCommand(BaseCommand):
    def execute(self, args: List[str], vfs: Any, env: Dict[str, str]) -> str:
        path = args[0] if args and not args[0].startswith("-") else ""
        return vfs.list_dir(path)

class CatCommand(BaseCommand):
    def execute(self, args: List[str], vfs: Any, env: Dict[str, str]) -> str:
        if not args:
            return ""
        return "".join(vfs.read_file(arg) for arg in args if not arg.startswith("-"))
    