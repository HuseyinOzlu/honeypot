import os
import time
from typing import Dict, Any, Optional, List

class VirtualFileSystem:
    """
    Lightweight in-memory Linux filesystem simulation used by FakeEnvironment.
    Supports basic POSIX operations (open, read, write, mkdir, ls, rm).
    """
    def __init__(self, commands_path: Optional[str] = None):
        self.root: Dict[str, Any] = {
            "type": "dir",
            "permissions": "drwxr-xr-x",
            "owner": "root",
            "group": "root",
            "size": 4096,
            "modified": time.strftime("%b %d %H:%M"),
            "children": {
                "bin": {"type": "dir", "children": {}},
                "etc": {"type": "dir", "children": {
                    "passwd": {"type": "file", "content": "root:x:0:0:root:/root:/bin/bash\nubuntu:x:1000:1000:Ubuntu:/home/ubuntu:/bin/bash\n", "size": 115},
                    "shadow": {"type":"file","content":"root:$6$v19fcbc0a385e8f2576853874546bf69361:19000:0:99999:7:::\nubuntu::$6$a8f1c62a83a752ad29f8e7322d45b0c3282:19000:0:99999:7:::\n", "size": 180, "permissions":"-rw-r-----"},
                    "issue": {"type": "file", "content": "Ubuntu 22.04.3 LTS \\n \\l\n", "size": 24}
                }},
                "home": {"type": "dir", "children": {
                    "ubuntu": {"type": "dir", "children": {}}
                }},
                "root": {"type": "dir", "children": {
                    ".bashrc": {"type": "file", "content": "# ~/.bashrc: executed by bash(1) for non-login shells.\n", "size": 55},
                    ".env": {"type": "file", "content": "DB_HOST=10.0.0.5\nDB_USER=admin\nDB_PASS=Sup3rS3cr3t!\n", "size": 62, "permissions": "-rw-------"},
                    ".aws": {"type": "dir", "children": {
                        "credentials": {"type": "file", "content": "[default]\naws_access_key_id=AKIAIOSFODNN7EXAMPLE\naws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n", "size": 116, "permissions": "-rw-------"}
                    }}
                }},
                "var": {"type": "dir", "children": {
                    "log": {"type": "dir", "children": {
                        "auth.log": {"type": "file", "content": "Failed password for invalid user admin from 192.168.1.100 port 44212 ssh2\n", "size": 74}
                    }}
                }},
                "tmp": {"type": "dir", "children": {}}
            }
        }
        self.cwd = "/root"

    def _resolve_path(self, path: str) -> str:
        if not path.startswith("/"):
            path = os.path.normpath(os.path.join(self.cwd, path))
        else:
            path = os.path.normpath(path)
        return path.replace("\\", "/")

    def _get_node(self, path: str) -> Optional[Dict[str, Any]]:
        parts = [p for p in path.split("/") if p]
        curr = self.root
        for part in parts:
            if curr.get("type") != "dir" or part not in curr.get("children", {}):
                return None
            curr = curr["children"][part]
        return curr

    def list_dir(self, path: str = "") -> str:
        target = self._resolve_path(path if path else self.cwd)
        node = self._get_node(target)
        if not node:
            return f"ls: cannot access '{path}': No such file or directory\n"
        if node.get("type") == "file":
            return f"{path}\n"
        
        output: List[str] = []
        for name, item in node.get("children", {}).items():
            perm = item.get("permissions", "-rw-r--r--" if item.get("type") == "file" else "drwxr-xr-x")
            owner = item.get("owner", "root")
            group = item.get("group", "root")
            size = item.get("size", 1024 if item.get("type") == "file" else 4096)
            mod = item.get("modified", time.strftime("%b %d %H:%M"))
            output.append(f"{perm} 1 {owner} {group} {size:>8} {mod} {name}")
        return "\n".join(output) + "\n" if output else ""

    def read_file(self, path: str) -> str:
        target = self._resolve_path(path)
        node = self._get_node(target)
        if not node:
            return f"cat: {path}: No such file or directory\n"
        if node.get("type") == "dir":
            return f"cat: {path}: Is a directory\n"
        return node.get("content", "")

    def write_file(self, path: str, content: str, append: bool = False) -> str:
        target = self._resolve_path(path)
        parts = [p for p in target.split("/") if p]
        if not parts:
            return "Permission denied\n"
        
        file_name = parts[-1]
        parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
        parent_node = self._get_node(parent_path)
        if not parent_node or parent_node.get("type") != "dir":
            return f"Cannot create file '{path}': No such file or directory\n"
        
        if file_name in parent_node["children"]:
            if parent_node["children"][file_name].get("type") == "dir":
                return f"Cannot write to '{path}': Is a directory\n"
            if append:
                parent_node["children"][file_name]["content"] += content
            else:
                parent_node["children"][file_name]["content"] = content
            parent_node["children"][file_name]["size"] = len(parent_node["children"][file_name]["content"])
        else:
            parent_node["children"][file_name] = {
                "type": "file",
                "permissions": "-rw-r--r--",
                "owner": "root",
                "group": "root",
                "size": len(content),
                "modified": time.strftime("%b %d %H:%M"),
                "content": content
            }
        return ""
