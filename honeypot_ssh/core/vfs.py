import json
import time

class VirtualFileSystem:
    def __init__(self, commands_config):
        self.fs = {}
        initial_fs = commands_config.get("fs", {})
        
        for path, info in initial_fs.items():
            self.fs[path] = {
                "type": info.get("type", "dir"),
                "files": dict(info.get("files", {}))
            }
            
        # Initialize default metadata
        self._init_metadata()

    def _get_default_metadata(self, path, is_dir_type=False):
        is_root = path == "/" or any(path.startswith(prefix) for prefix in ["/root", "/etc", "/bin", "/sbin", "/boot", "/var/log", "/usr", "/proc", "/sys", "/dev", "/run"])
        owner = "root" if is_root else "ubuntu"
        group = "root" if is_root else "ubuntu"
        mode = 0o755 if is_dir_type else 0o644
        mtime = 1782705600.0  # June 28, 2026
        return {
            "owner": owner,
            "group": group,
            "mode": mode,
            "mtime": mtime
        }

    def _init_metadata(self):
        for path in list(self.fs.keys()):
            meta = self._get_default_metadata(path, is_dir_type=True)
            self.fs[path].update(meta)
            
            for name, file_info in list(self.fs[path]["files"].items()):
                child_path = path + "/" + name if path != "/" else "/" + name
                is_dir = file_info.get("type") == "dir"
                meta = self._get_default_metadata(child_path, is_dir_type=is_dir)
                for k, v in meta.items():
                    if k not in file_info:
                        file_info[k] = v

    def _update_node_meta(self, path, meta_updates):
        node = self.fs.get(path)
        if node:
            node.update(meta_updates)
            
        parent, name = self._split_path(path)
        if parent in self.fs and name in self.fs[parent]["files"]:
            self.fs[parent]["files"][name].update(meta_updates)

    def chmod(self, path, mode_str):
        if not self.exists(path):
            return False
        node = self._get_node(path)
        if not node:
            return False
        
        current_mode = node.get("mode", 0o755 if self.is_dir(path) else 0o644)
        
        try:
            if isinstance(mode_str, int):
                new_mode = mode_str
            elif mode_str.isdigit():
                new_mode = int(mode_str, 8)
            else:
                new_mode = self._parse_symbolic_mode(current_mode, mode_str)
            
            self._update_node_meta(path, {"mode": new_mode, "mtime": time.time()})
            return True
        except Exception:
            return False

    def _parse_symbolic_mode(self, current_mode, mode_str):
        u = (current_mode >> 6) & 7
        g = (current_mode >> 3) & 7
        o = current_mode & 7
        
        parts = mode_str.split(',')
        for part in parts:
            if not part:
                continue
            op_idx = -1
            for op in ('+', '-', '='):
                op_idx = part.find(op)
                if op_idx != -1:
                    operator = op
                    break
            if op_idx == -1:
                continue
            
            who = part[:op_idx] or 'a'
            perms = part[op_idx+1:]
            
            mask = 0
            if 'r' in perms: mask |= 4
            if 'w' in perms: mask |= 2
            if 'x' in perms: mask |= 1
            
            target_u = 'u' in who or 'a' in who
            target_g = 'g' in who or 'a' in who
            target_o = 'o' in who or 'a' in who
            
            if operator == '+':
                if target_u: u |= mask
                if target_g: g |= mask
                if target_o: o |= mask
            elif operator == '-':
                if target_u: u &= ~mask
                if target_g: g &= ~mask
                if target_o: o &= ~mask
            elif operator == '=':
                if target_u: u = mask
                if target_g: g = mask
                if target_o: o = mask
        return (u << 6) | (g << 3) | o

    def chown(self, path, owner, group=None):
        if not self.exists(path):
            return False
        updates = {"mtime": time.time()}
        if owner:
            updates["owner"] = owner
        if group:
            updates["group"] = group
        if updates:
            self._update_node_meta(path, updates)
            return True
        return False

    def _get_node(self, path):
        if path == "/":
            return self.fs.get("/")
        parent, name = self._split_path(path)
        if parent in self.fs and name in self.fs[parent]["files"]:
            return self.fs[parent]["files"][name]
        if path in self.fs:
            return self.fs[path]
        return None

    def stat(self, path):
        if not self.exists(path):
            return None
        node = self._get_node(path)
        if not node:
            return None
        
        is_directory = self.is_dir(path)
        size = 4096 if is_directory else len(node.get("content", ""))
        
        return {
            "type": node.get("type", "dir" if is_directory else "file"),
            "owner": node.get("owner", "ubuntu"),
            "group": node.get("group", "ubuntu"),
            "mode": node.get("mode", 0o755 if is_directory else 0o644),
            "mtime": node.get("mtime", 1782705600.0),
            "size": size
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
            file_info["mtime"] = time.time()
        else:
            meta = self._get_default_metadata(path, is_dir_type=False)
            self.fs[parent]["files"][name] = {
                "type": "file",
                "content": content,
                **meta
            }
        return True

    def mkdir(self, path):
        if self.exists(path):
            return False
        parent, name = self._split_path(path)
        if parent not in self.fs:
            return False
        
        meta = self._get_default_metadata(path, is_dir_type=True)
        self.fs[parent]["files"][name] = {
            "type": "dir",
            **meta
        }
        self.fs[path] = {
            "type": "dir",
            "files": {},
            **meta
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
