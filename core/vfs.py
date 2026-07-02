import json

class VirtualFileSystem:
    def __init__(self, commands_config):
        self.fs = {}
        initial_fs = commands_config.get("fs", {})
        
        for path, info in initial_fs.items():
            self.fs[path] = {
                "type": info.get("type", "dir"),
                "files": dict(info.get("files", {}))
            }

    def resolve_path(self, current_dir, target):
        if not target:
            return current_dir
        
        if target.startswith("/"):
            abs_path = target
        else:
            if current_dir == "/":
                abs_path = "/" + target
            else:
                abs_path = current_dir + "/" + target
                
        parts = []
        for part in abs_path.split("/"):
            if part == "" or part == ".":
                continue
            if part == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(part)
                
        normalized = "/" + "/".join(parts)
        return normalized

    def _split_path(self, path):
        if path == "/":
            return "/", ""
        if path.endswith("/") and len(path) > 1:
            path = path[:-1]
        
        r_idx = path.rfind("/")
        if r_idx == 0:
            parent = "/"
            name = path[1:]
        else:
            parent = path[:r_idx]
            name = path[r_idx+1:]
        return parent, name

    def exists(self, path):
        if path == "/":
            return True
        if path in self.fs:
            return True
        parent, name = self._split_path(path)
        if parent in self.fs and name in self.fs[parent]["files"]:
            return True
        return False

    def is_dir(self, path):
        if path == "/":
            return True
        if path in self.fs:
            return True
        parent, name = self._split_path(path)
        if parent in self.fs and name in self.fs[parent]["files"]:
            return self.fs[parent]["files"][name].get("type") == "dir"
        return False

    def is_file(self, path):
        if path == "/":
            return False
        if path in self.fs:
            return False
        parent, name = self._split_path(path)
        if parent in self.fs and name in self.fs[parent]["files"]:
            return self.fs[parent]["files"][name].get("type") == "file"
        return False

    def read_file(self, path):
        parent, name = self._split_path(path)
        if parent in self.fs and name in self.fs[parent]["files"]:
            file_info = self.fs[parent]["files"][name]
            if file_info.get("type") == "file":
                return file_info.get("content", "")
        return None

    def write_file(self, path, content, append=False):
        parent, name = self._split_path(path)
        if parent not in self.fs:
            return False
        
        if name in self.fs[parent]["files"]:
            file_info = self.fs[parent]["files"][name]
            if file_info.get("type") == "dir":
                return False
            if append:
                file_info["content"] = file_info.get("content", "") + content
            else:
                file_info["content"] = content
        else:
            self.fs[parent]["files"][name] = {
                "type": "file",
                "content": content
            }
        return True

    def mkdir(self, path):
        if self.exists(path):
            return False
        parent, name = self._split_path(path)
        if parent not in self.fs:
            return False
        
        self.fs[parent]["files"][name] = {
            "type": "dir"
        }
        self.fs[path] = {
            "type": "dir",
            "files": {}
        }
        return True

    def rm(self, path, recursive=False):
        if not self.exists(path):
            return False
        
        if path == "/":
            return False
            
        if self.is_dir(path):
            if not recursive:
                return False
            prefix = path + "/"
            subdirs = [p for p in self.fs if p.startswith(prefix) or p == path]
            for subdir in subdirs:
                self.fs.pop(subdir, None)
        
        parent, name = self._split_path(path)
        if parent in self.fs and name in self.fs[parent]["files"]:
            self.fs[parent]["files"].pop(name, None)
            
        return True

    def list_dir(self, path):
        if not self.is_dir(path):
            return None
        if path not in self.fs:
            return {}
        return self.fs[path]["files"]
