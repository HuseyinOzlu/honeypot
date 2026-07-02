import shlex
import time
from services.log_service import LogService

class Shell:
    def __init__(self, vfs, chan, commands_config, client_ip):
        self.vfs = vfs
        self.chan = chan
        self.commands_config = commands_config
        self.client_ip = client_ip
        self.logger = LogService()
        self.current_dir = "/home/ubuntu"

    def execute(self, cmd_line):
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return
            
        self.logger.log_command(self.client_ip, cmd_line)
        
        append = False
        redirect_file = None
        
        if ">>" in cmd_line:
            parts = cmd_line.rsplit(">>", 1)
            cmd_line = parts[0].strip()
            redirect_file = parts[1].strip()
            append = True
        elif ">" in cmd_line:
            parts = cmd_line.rsplit(">", 1)
            cmd_line = parts[0].strip()
            redirect_file = parts[1].strip()
            append = False
            
        pipe_cmds = []
        if "|" in cmd_line:
            pipe_cmds = [c.strip() for c in cmd_line.split("|")]
            cmd_line = pipe_cmds[0]
            pipe_cmds = pipe_cmds[1:]
            
        output = self._run_command(cmd_line)
        
        for pipe_cmd in pipe_cmds:
            output = self._run_pipe_command(pipe_cmd, output)
            
        if redirect_file:
            resolved_redirect = self.vfs.resolve_path(self.current_dir, redirect_file)
            if output and not output.endswith("\n"):
                output += "\n"
            success = self.vfs.write_file(resolved_redirect, output or "", append=append)
            if not success:
                self.chan.send(f"-bash: {redirect_file}: No such file or directory\r\n")
        else:
            if output:
                output_crlf = output.replace("\r\n", "\n").replace("\n", "\r\n")
                self.chan.send(output_crlf)

    def _run_command(self, cmd_line):
        try:
            args = shlex.split(cmd_line)
        except ValueError:
            args = cmd_line.split()
            
        if not args:
            return ""
            
        cmd_name = args[0]
        
        if cmd_name in ("exit", "logout"):
            raise EOFError()
            
        elif cmd_name == "cd":
            target = args[1] if len(args) > 1 else "~"
            if target == "~":
                target = "/home/ubuntu"
            resolved = self.vfs.resolve_path(self.current_dir, target)
            if self.vfs.exists(resolved):
                if self.vfs.is_dir(resolved):
                    self.current_dir = resolved
                    return ""
                else:
                    return f"bash: cd: {target}: Not a directory\n"
            else:
                return f"bash: cd: {target}: No such file or directory\n"
                
        elif cmd_name == "pwd":
            return self.current_dir + "\n"
            
        elif cmd_name == "ls":
            flags = []
            targets = []
            for arg in args[1:]:
                if arg.startswith("-"):
                    for char in arg[1:]:
                        flags.append(char)
                else:
                    targets.append(arg)
            
            target_dir = targets[0] if targets else "."
            if target_dir == "~":
                target_dir = "/home/ubuntu"
                
            resolved_dir = self.vfs.resolve_path(self.current_dir, target_dir)
            
            if not self.vfs.exists(resolved_dir):
                return f"ls: cannot access '{target_dir}': No such file or directory\n"
                
            if not self.vfs.is_dir(resolved_dir):
                if "l" in flags:
                    content = self.vfs.read_file(resolved_dir) or ""
                    size = len(content)
                    _, name = self.vfs._split_path(resolved_dir)
                    return f"-rw-r--r-- 1 ubuntu ubuntu {size} Jun 28 09:30 {name}\n"
                else:
                    _, name = self.vfs._split_path(resolved_dir)
                    return name + "\n"
                    
            files = self.vfs.list_dir(resolved_dir)
            if files is None:
                return f"ls: cannot access '{target_dir}': No such file or directory\n"
                
            show_all = "a" in flags
            show_long = "l" in flags
            
            names = sorted(files.keys())
            if show_all:
                names = [".", ".."] + names
                
            if show_long:
                lines = []
                total_blocks = len(files) * 4
                lines.append(f"total {total_blocks}")
                for name in names:
                    if name == ".":
                        lines.append("drwxr-xr-x 2 ubuntu ubuntu 4096 Jun 28 09:30 .")
                        continue
                    if name == "..":
                        lines.append("drwxr-xr-x 2 ubuntu ubuntu 4096 Jun 28 09:30 ..")
                        continue
                    info = files[name]
                    ftype = info.get("type", "file")
                    perm = "drwxr-xr-x" if ftype == "dir" else "-rw-r--r--"
                    size = 4096 if ftype == "dir" else len(info.get("content", ""))
                    lines.append(f"{perm} 1 ubuntu ubuntu {size} Jun 28 09:30 {name}")
                return "\n".join(lines) + "\n"
            else:
                if not names:
                    return ""
                return "  ".join(names) + "\n"
                
        elif cmd_name == "cat":
            if len(args) < 2:
                return ""
            outputs = []
            for target_file in args[1:]:
                resolved = self.vfs.resolve_path(self.current_dir, target_file)
                if not self.vfs.exists(resolved):
                    outputs.append(f"cat: {target_file}: No such file or directory")
                elif self.vfs.is_dir(resolved):
                    outputs.append(f"cat: {target_file}: Is a directory")
                else:
                    content = self.vfs.read_file(resolved) or ""
                    outputs.append(content)
            return "\n".join(outputs) + "\n"
            
        elif cmd_name == "echo":
            n_flag = False
            start_idx = 1
            if len(args) > 1 and args[1] == "-n":
                n_flag = True
                start_idx = 2
            elif len(args) > 1 and args[1] == "-e":
                start_idx = 2
                
            content = " ".join(args[start_idx:])
            if not n_flag:
                content += "\n"
            return content
            
        elif cmd_name == "mkdir":
            if len(args) < 2:
                return "mkdir: missing operand\n"
            errs = []
            for target in args[1:]:
                if target.startswith("-"):
                    continue
                resolved = self.vfs.resolve_path(self.current_dir, target)
                if not self.vfs.mkdir(resolved):
                    errs.append(f"mkdir: cannot create directory '{target}': File exists or parent does not exist")
            if errs:
                return "\n".join(errs) + "\n"
            return ""
            
        elif cmd_name == "rm":
            if len(args) < 2:
                return "rm: missing operand\n"
            recursive = False
            targets = []
            for arg in args[1:]:
                if arg.startswith("-"):
                    if "r" in arg or "f" in arg:
                        recursive = True
                else:
                    targets.append(arg)
            errs = []
            for target in targets:
                resolved = self.vfs.resolve_path(self.current_dir, target)
                if not self.vfs.exists(resolved):
                    if not recursive:
                        errs.append(f"rm: cannot remove '{target}': No such file or directory")
                    continue
                if self.vfs.is_dir(resolved) and not recursive:
                    errs.append(f"rm: cannot remove '{target}': Is a directory")
                    continue
                if not self.vfs.rm(resolved, recursive=recursive):
                    errs.append(f"rm: cannot remove '{target}': Permission denied")
            if errs:
                return "\n".join(errs) + "\n"
            return ""
            
        elif cmd_name == "touch":
            if len(args) < 2:
                return "touch: missing file operand\n"
            for target in args[1:]:
                if target.startswith("-"):
                    continue
                resolved = self.vfs.resolve_path(self.current_dir, target)
                if not self.vfs.exists(resolved):
                    self.vfs.write_file(resolved, "")
            return ""
            
        elif cmd_name in ("wget", "curl"):
            url = None
            for arg in args[1:]:
                if arg.startswith("http://") or arg.startswith("https://"):
                    url = arg
                    break
            if not url:
                return f"{cmd_name}: missing URL\n"
                
            filename = "index.html"
            if "/" in url:
                parts = url.split("/")
                if parts[-1]:
                    filename = parts[-1].split("?")[0]
            
            resolved_file = self.vfs.resolve_path(self.current_dir, filename)
            
            self.logger.log_download(self.client_ip, url, resolved_file)
            
            if cmd_name == "wget":
                self.chan.send(f"--{time.strftime('%Y-%m-%d %H:%M:%S')}--  {url}\r\n")
                host = url.split("/")[2] if len(url.split("/")) > 2 else "localhost"
                self.chan.send(f"Resolving {host}... 192.0.2.1\r\n")
                self.chan.send(f"Connecting to {host}|192.0.2.1|:80... connected.\r\n")
                self.chan.send("HTTP request sent, awaiting response... 200 OK\r\n")
                self.chan.send("Length: 2048 (2.0K) [application/x-sh]\r\n")
                self.chan.send(f"Saving to: '{filename}'\r\n\r\n")
                self.chan.send("     0K .......... .......... .......... .......... ..........  50%\r\n")
                self.chan.send("    50K .......... .......... .......... .......... .......... 100%\r\n\r\n")
                self.chan.send(f"{time.strftime('%Y-%m-%d %H:%M:%S')} (1.2 MB/s) - '{filename}' saved [2048/2048]\r\n")
            else:
                self.chan.send("  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\r\n")
                self.chan.send("                                 Dload  Upload   Total   Spent    Left  Speed\r\n")
                self.chan.send("100  2048  100  2048    0     0  10240      0 --:--:-- --:--:-- --:--:-- 10240\r\n")
                
            dummy_content = f"#!/bin/bash\n# Simulated payload downloaded from {url}\necho 'Error: system architecture not supported'\n"
            self.vfs.write_file(resolved_file, dummy_content)
            return ""
            
        elif cmd_name in ("apt", "apt-get"):
            if len(args) > 1 and args[1] == "update":
                self.chan.send("Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease\r\n")
                self.chan.send("Get:2 http://archive.ubuntu.com/ubuntu jammy-updates InRelease [114 kB]\r\n")
                self.chan.send("Get:3 http://security.ubuntu.com/ubuntu jammy-security InRelease [110 kB]\r\n")
                self.chan.send("Fetched 224 kB in 1s (224 kB/s)\r\n")
                self.chan.send("Reading package lists... Done\r\n")
                self.chan.send("Building dependency tree... Done\r\n")
                self.chan.send("Reading state information... Done\r\n")
                return ""
            elif len(args) > 2 and args[1] == "install":
                pkg = args[2]
                self.chan.send(f"Reading package lists... Done\r\n")
                self.chan.send(f"Building dependency tree... Done\r\n")
                self.chan.send(f"Reading state information... Done\r\n")
                self.chan.send(f"The following NEW packages will be installed:\r\n  {pkg}\r\n")
                self.chan.send(f"0 upgraded, 1 newly installed, 0 to remove and 12 not upgraded.\r\n")
                self.chan.send(f"Need to get 102 kB of archives.\r\n")
                self.chan.send(f"After this operation, 345 kB of additional disk space will be used.\r\n")
                self.chan.send(f"Get:1 http://archive.ubuntu.com/ubuntu jammy/main amd64 {pkg} [102 kB]\r\n")
                self.chan.send(f"Fetched 102 kB in 0s (450 kB/s)\r\n")
                self.chan.send(f"Selecting previously unselected package {pkg}.\r\n")
                self.chan.send(f"(Reading database ... 124500 files and directories currently installed.)\r\n")
                self.chan.send(f"Preparing to unpack .../{pkg}_amd64.deb ...\r\n")
                self.chan.send(f"Unpacking {pkg} ...\r\n")
                self.chan.send(f"Setting up {pkg} ...\r\n")
                return ""
            return ""
            
        elif cmd_name in ("sudo", "su"):
            sub_args = args[1:]
            if not sub_args or sub_args[0] in ("-i", "-", "su"):
                if not sub_args:
                    return ""
                while sub_args and sub_args[0].startswith("-"):
                    sub_args.pop(0)
                if not sub_args:
                    return ""
            sub_cmd_line = " ".join(sub_args)
            return self._run_command(sub_cmd_line)
            
        cmd_str = " ".join(args)
        if cmd_str in self.commands_config.get("commands", {}):
            return self.commands_config["commands"][cmd_str]["output"]
            
        if cmd_name in self.commands_config.get("commands", {}):
            return self.commands_config["commands"][cmd_name]["output"]
            
        default_error = self.commands_config.get("default_error", "bash: {cmd}: command not found\n")
        return default_error.format(cmd=cmd_name)

    def _run_pipe_command(self, pipe_cmd, input_text):
        if not input_text:
            return ""
            
        parts = pipe_cmd.split()
        if not parts:
            return input_text
            
        cmd = parts[0]
        
        if cmd == "grep":
            terms = [p for p in parts[1:] if not p.startswith("-")]
            if not terms:
                return input_text
            term = terms[0].strip("'\"")
            case_insensitive = any("i" in p for p in parts[1:] if p.startswith("-"))
            
            lines = input_text.splitlines()
            matching_lines = []
            for line in lines:
                if case_insensitive:
                    if term.lower() in line.lower():
                        matching_lines.append(line)
                else:
                    if term in line:
                        matching_lines.append(line)
            return "\n".join(matching_lines) + ("\n" if matching_lines else "")
            
        elif cmd == "wc":
            lines = input_text.splitlines()
            if len(parts) > 1 and "l" in parts[1]:
                return f"{len(lines)}\n"
            words = len(input_text.split())
            chars = len(input_text)
            return f"      {len(lines)}       {words}      {chars}\n"
            
        elif cmd == "head":
            lines = input_text.splitlines()
            n = 10
            if len(parts) > 2 and parts[1] == "-n":
                try:
                    n = int(parts[2])
                except ValueError:
                    pass
            return "\n".join(lines[:n]) + "\n"
            
        elif cmd == "tail":
            lines = input_text.splitlines()
            n = 10
            if len(parts) > 2 and parts[1] == "-n":
                try:
                    n = int(parts[2])
                except ValueError:
                    pass
            return "\n".join(lines[-n:]) + "\n"
            
        return input_text

    def get_prompt(self):
        if self.current_dir == "/home/ubuntu":
            display_dir = "~"
        elif self.current_dir.startswith("/home/ubuntu/"):
            display_dir = "~" + self.current_dir[len("/home/ubuntu"):]
        else:
            display_dir = self.current_dir
        return f"ubuntu@server:{display_dir}$ "
