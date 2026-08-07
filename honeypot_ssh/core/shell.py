import shlex
import time
import re
import os
import io
import sys
import random
from services.log_service import LogService

def parse_command_line(cmd_line):
    """Splits command line by separators ;, &&, ||, respecting quotes."""
    segments = []
    current = []
    i = 0
    in_single = False
    in_double = False
    n = len(cmd_line)
    
    while i < n:
        c = cmd_line[i]
        if c == "'" and not in_double:
            in_single = not in_single
            current.append(c)
            i += 1
        elif c == '"' and not in_single:
            in_double = not in_double
            current.append(c)
            i += 1
        elif not in_single and not in_double:
            if cmd_line[i:i+2] == "&&":
                segments.append(("".join(current).strip(), "&&"))
                current = []
                i += 2
            elif cmd_line[i:i+2] == "||":
                segments.append(("".join(current).strip(), "||"))
                current = []
                i += 2
            elif c == ";":
                segments.append(("".join(current).strip(), ";"))
                current = []
                i += 1
            else:
                current.append(c)
                i += 1
        else:
            current.append(c)
            i += 1
            
    if current:
        segments.append(("".join(current).strip(), None))
    return segments

def parse_segment(segment):
    """Splits a single command segment by pipes and stdout redirection."""
    pipe_cmds = []
    redirect_file = None
    append = False
    
    current = []
    in_single = False
    in_double = False
    i = 0
    n = len(segment)
    
    while i < n:
        c = segment[i]
        if c == "'" and not in_double:
            in_single = not in_single
            current.append(c)
            i += 1
        elif c == '"' and not in_single:
            in_double = not in_double
            current.append(c)
            i += 1
        elif not in_single and not in_double:
            if segment[i:i+2] == ">>":
                if current:
                    pipe_cmds.append("".join(current).strip())
                redirect_file = segment[i+2:].strip()
                append = True
                break
            elif c == ">":
                if current:
                    pipe_cmds.append("".join(current).strip())
                redirect_file = segment[i+1:].strip()
                append = False
                break
            elif c == "|":
                pipe_cmds.append("".join(current).strip())
                current = []
                i += 1
            else:
                current.append(c)
                i += 1
        else:
            current.append(c)
            i += 1
            
    if not redirect_file:
        pipe_cmds.append("".join(current).strip())
        
    return pipe_cmds, redirect_file, append

class Shell:
    def __init__(self, vfs, chan, commands_config, client_ip):
        self.vfs = vfs
        self.chan = chan
        self.commands_config = commands_config
        self.client_ip = client_ip
        self.logger = LogService()
        self.current_dir = "/home/ubuntu"
        self.state = "NORMAL" # NORMAL, NANO, TOP, PING, PYTHON, SSH_PASSWORD
        
        # PTY State
        self.buffer = ""
        self.cursor_idx = 0
        self.history = []
        self.history_idx = 0
        self.env = {
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "USER": "ubuntu",
            "HOME": "/home/ubuntu",
            "SHELL": "/bin/bash",
            "PWD": self.current_dir,
            "TERM": "xterm-256color"
        }
        self.installed_packages = set()
        
        # Nested SSH emulation state
        self.nested_ssh = False
        self.ssh_host = ""
        self.ssh_user = ""
        self.ssh_pass_buf = ""
        
        # Nano state
        self.nano_filepath = ""
        self.nano_filename = ""
        self.nano_lines = []
        self.nano_row = 0
        self.nano_col = 0
        self.nano_scroll = 0
        
        # Python REPL state
        self.python_globals = {}
        
        # Ping state
        self.ping_host = ""
        self.ping_seq = 0
        self.ping_sent = 0
        self.ping_recv = 0
        self.ping_start_time = 0.0

    def run(self):
        """Main SSH shell session loop."""
        self.chan.send(self.get_prompt())
        ansi_seq = ""
        
        while True:
            try:
                # If we are in TOP or PING, we need non-blocking reads to update displays
                if self.state in ("TOP", "PING"):
                    char = self.read_char(timeout=1.0)
                    if char is None:
                        if self.state == "TOP":
                            self.draw_top()
                        elif self.state == "PING":
                            self.run_ping_step()
                        continue
                else:
                    char = self.read_char()
                    if not char:
                        continue
                
                # Check for escape sequences
                if ansi_seq:
                    ansi_seq += char
                    if len(ansi_seq) >= 3 and (ansi_seq[-1].isalpha() or ansi_seq[-1] == "~"):
                        self.handle_ansi_seq(ansi_seq)
                        ansi_seq = ""
                    continue
                
                if char == "\x1b":
                    ansi_seq = char
                    continue
                
                # Input multiplexing based on state
                if self.state == "NORMAL":
                    self.handle_normal_char(char)
                elif self.state == "NANO":
                    self.handle_nano_char(char)
                elif self.state == "TOP":
                    self.handle_top_char(char)
                elif self.state == "PYTHON":
                    self.handle_python_char(char)
                elif self.state == "PING":
                    self.handle_ping_char(char)
                elif self.state == "SSH_PASSWORD":
                    self.handle_ssh_password_char(char)
                    
            except EOFError:
                break
            except Exception as e:
                break

    def read_char(self, timeout=None):
        """Reads a single character from the channel, returning None on timeout."""
        if timeout is not None:
            t = 0.0
            while not self.chan.recv_ready():
                time.sleep(0.05)
                t += 0.05
                if t >= timeout:
                    return None
        data = self.chan.recv(1)
        if not data:
            raise EOFError()
        return data.decode('utf-8', errors='ignore')

    def handle_normal_char(self, char):
        """Process keyboard keys in the normal Bash prompt state."""
        if char in ('\r', '\n'):
            self.chan.send("\r\n")
            cmd = self.buffer.strip()
            if cmd:
                # Add to history
                if not self.history or self.history[-1] != cmd:
                    self.history.append(cmd)
                self.history_idx = len(self.history)
                
                try:
                    self.execute(cmd)
                except EOFError:
                    raise EOFError()
            
            self.buffer = ""
            self.cursor_idx = 0
            if self.state == "NORMAL":
                self.chan.send(self.get_prompt())
                
        elif char in ('\x7f', '\x08'):  # Backspace
            if self.cursor_idx > 0:
                self.buffer = self.buffer[:self.cursor_idx-1] + self.buffer[self.cursor_idx:]
                self.cursor_idx -= 1
                self.redraw_line()
                
        elif char == '\t':  # Tab Autocomplete
            self.handle_autocomplete()
            
        elif char == '\x03':  # Ctrl+C
            self.chan.send("^C\r\n")
            self.buffer = ""
            self.cursor_idx = 0
            self.chan.send(self.get_prompt())
            
        elif char == '\x04':  # Ctrl+D
            if not self.buffer:
                if self.nested_ssh:
                    self.exit_nested_ssh()
                else:
                    self.chan.send("exit\r\n")
                    raise EOFError()
            
        elif char == '\x0c':  # Ctrl+L
            self.chan.send("\x1b[2J\x1b[H")
            self.redraw_line()
            
        elif ord(char) >= 32:  # Printable character
            self.buffer = self.buffer[:self.cursor_idx] + char + self.buffer[self.cursor_idx:]
            self.cursor_idx += 1
            self.redraw_line()

    def handle_ansi_seq(self, seq):
        """Processes ANSI escape sequences (arrows, home, end, delete)."""
        if self.state in ("NORMAL", "PYTHON"):
            if seq == "\x1b[A":  # Up Arrow
                if self.history:
                    if self.history_idx > 0:
                        self.history_idx -= 1
                        self.buffer = self.history[self.history_idx]
                        self.cursor_idx = len(self.buffer)
                        self.redraw_line()
            elif seq == "\x1b[B":  # Down Arrow
                if self.history:
                    if self.history_idx < len(self.history) - 1:
                        self.history_idx += 1
                        self.buffer = self.history[self.history_idx]
                        self.cursor_idx = len(self.buffer)
                    else:
                        self.history_idx = len(self.history)
                        self.buffer = ""
                        self.cursor_idx = 0
                    self.redraw_line()
            elif seq == "\x1b[C":  # Right Arrow
                if self.cursor_idx < len(self.buffer):
                    self.cursor_idx += 1
                    self.chan.send("\x1b[C")
            elif seq == "\x1b[D":  # Left Arrow
                if self.cursor_idx > 0:
                    self.cursor_idx -= 1
                    self.chan.send("\x1b[D")
            elif seq in ("\x1b[H", "\x1b[1~"):  # Home
                if self.cursor_idx > 0:
                    self.chan.send("\x1b[D" * self.cursor_idx)
                    self.cursor_idx = 0
            elif seq in ("\x1b[F", "\x1b[4~"):  # End
                if self.cursor_idx < len(self.buffer):
                    self.chan.send("\x1b[C" * (len(self.buffer) - self.cursor_idx))
                    self.cursor_idx = len(self.buffer)
            elif seq == "\x1b[3~":  # Delete
                if self.cursor_idx < len(self.buffer):
                    self.buffer = self.buffer[:self.cursor_idx] + self.buffer[self.cursor_idx+1:]
                    self.redraw_line()
        elif self.state == "NANO":
            self.handle_nano_ansi(seq)

    def redraw_line(self):
        """Redraws the command line on the terminal, keeping cursor in place."""
        prompt = self.get_prompt() if self.state == "NORMAL" else ">>> "
        self.chan.send("\r" + prompt + self.buffer + "\x1b[K")
        back_steps = len(self.buffer) - self.cursor_idx
        if back_steps > 0:
            self.chan.send("\x1b[D" * back_steps)

    def get_prompt(self):
        """Dynamic bash prompt based on PWD and nested SSH state."""
        user = self.env.get("USER", "ubuntu")
        host = self.env.get("HOSTNAME", "ubuntu-server")
        if self.nested_ssh:
            prompt_char = "#" if user == "root" else "$"
            display_dir = self.current_dir
            if user == "root" and display_dir == "/root":
                display_dir = "~"
            elif display_dir == f"/home/{user}":
                display_dir = "~"
            return f"{user}@{host}:{display_dir}{prompt_char} "
        else:
            display_dir = self.current_dir
            if display_dir == "/home/ubuntu":
                display_dir = "~"
            elif display_dir.startswith("/home/ubuntu/"):
                display_dir = "~" + display_dir[len("/home/ubuntu"):]
            return f"ubuntu@server:{display_dir}$ "

    def handle_autocomplete(self):
        """Autocomplete commands or paths in the command line."""
        current_input = self.buffer[:self.cursor_idx]
        
        # Check if we are completing a command or a path
        is_cmd = False
        if " " not in current_input:
            is_cmd = True
        else:
            # Check if after logical separators or sudo
            tokens = current_input.split()
            if tokens and tokens[-1] in ("&&", ";", "||", "|", "sudo"):
                is_cmd = True
        
        if is_cmd:
            prefix = current_input.split()[-1] if current_input.split() else ""
            # Gather all possible command names
            all_cmds = [
                "cd", "pwd", "ls", "cat", "echo", "mkdir", "rm", "touch", "cp", "mv",
                "chmod", "chown", "find", "grep", "wc", "head", "tail", "whoami", "id",
                "uname", "df", "free", "ifconfig", "ip", "uptime", "ps", "top", "env",
                "printenv", "history", "clear", "ping", "wget", "curl", "nc", "netcat",
                "ssh", "apt", "apt-get", "dpkg", "nano", "vi", "vim", "python", "python3",
                "exit", "logout", "su"
            ]
            # Add files in /bin, /usr/bin, /sbin, /usr/sbin if they exist in VFS
            for path in ("/bin", "/usr/bin", "/sbin", "/usr/sbin"):
                if self.vfs.is_dir(path):
                    files = self.vfs.list_dir(path)
                    if files:
                        all_cmds.extend(files.keys())
            
            all_cmds = sorted(list(set(all_cmds)))
            matches = [c for c in all_cmds if c.startswith(prefix)]
            
            if not matches:
                self.chan.send("\x07")
                return
            
            if len(matches) == 1:
                completed = matches[0][len(prefix):] + " "
                self.buffer = self.buffer[:self.cursor_idx] + completed + self.buffer[self.cursor_idx:]
                self.cursor_idx += len(completed)
                self.redraw_line()
            else:
                common = self._get_common_prefix(matches)
                if common and len(common) > len(prefix):
                    completed = common[len(prefix):]
                    self.buffer = self.buffer[:self.cursor_idx] + completed + self.buffer[self.cursor_idx:]
                    self.cursor_idx += len(completed)
                    self.redraw_line()
                else:
                    self.chan.send("\r\n" + "  ".join(matches) + "\r\n")
                    self.redraw_line()
        else:
            # Path completion
            last_word = current_input.split()[-1] if (current_input and not current_input.endswith(" ")) else ""
            
            if "/" in last_word:
                r_idx = last_word.rfind("/")
                parent_part = last_word[:r_idx+1]
                prefix = last_word[r_idx+1:]
            else:
                parent_part = ""
                prefix = last_word
                
            resolved_parent = self.vfs.resolve_path(self.current_dir, parent_part)
            if not self.vfs.is_dir(resolved_parent):
                self.chan.send("\x07")
                return
                
            files = self.vfs.list_dir(resolved_parent)
            if not files:
                self.chan.send("\x07")
                return
                
            matches = [name for name in files.keys() if name.startswith(prefix)]
            if not matches:
                self.chan.send("\x07")
                return
                
            if len(matches) == 1:
                match_name = matches[0]
                full_path = resolved_parent + "/" + match_name if resolved_parent != "/" else "/" + match_name
                is_dir = self.vfs.is_dir(full_path)
                completed = match_name[len(prefix):] + ("/" if is_dir else " ")
                self.buffer = self.buffer[:self.cursor_idx] + completed + self.buffer[self.cursor_idx:]
                self.cursor_idx += len(completed)
                self.redraw_line()
            else:
                common = self._get_common_prefix(matches)
                if common and len(common) > len(prefix):
                    completed = common[len(prefix):]
                    self.buffer = self.buffer[:self.cursor_idx] + completed + self.buffer[self.cursor_idx:]
                    self.cursor_idx += len(completed)
                    self.redraw_line()
                else:
                    self.chan.send("\r\n" + "  ".join(matches) + "\r\n")
                    self.redraw_line()

    def _get_common_prefix(self, strings):
        if not strings:
            return ""
        s1 = min(strings)
        s2 = max(strings)
        for i, c in enumerate(s1):
            if i >= len(s2) or s2[i] != c:
                return s1[:i]
        return s1

    # ==========================================
    # Command Parser & Runner
    # ==========================================
    def execute(self, cmd_line):
        """Executes a command line containing logic operators (;, &&, ||)."""
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return
            
        self.logger.log_command(self.client_ip, cmd_line)
        
        segments = parse_command_line(cmd_line)
        success = True
        skip_to_next_chain = False
        next_chain_op = None
        
        i = 0
        while i < len(segments):
            segment, op = segments[i]
            
            if skip_to_next_chain:
                if next_chain_op == "&&" and op == "||":
                    skip_to_next_chain = False
                elif next_chain_op == "||" and op == "&&":
                    skip_to_next_chain = False
                elif op == ";":
                    skip_to_next_chain = False
                i += 1
                continue
                
            success, _ = self._run_segment(segment)
            
            if op == "&&" and not success:
                skip_to_next_chain = True
                next_chain_op = "&&"
            elif op == "||" and success:
                skip_to_next_chain = True
                next_chain_op = "||"
                
            i += 1

    def _run_segment(self, segment):
        """Runs a command segment supporting pipes and redirection."""
        pipe_cmds, redirect_file, append = parse_segment(segment)
        if not pipe_cmds:
            return True, ""
            
        success, output = self._run_single_command(pipe_cmds[0])
        
        for pipe_cmd in pipe_cmds[1:]:
            success, output = self._run_pipe_command(pipe_cmd, output)
            if not success:
                break
                
        if redirect_file:
            redirect_file = redirect_file.strip("'\"")
            resolved_redirect = self.vfs.resolve_path(self.current_dir, redirect_file)
            if output and not output.endswith("\n"):
                output += "\n"
            write_success = self.vfs.write_file(resolved_redirect, output or "", append=append)
            if not write_success:
                self.chan.send(f"-bash: {redirect_file}: No such file or directory\r\n")
                return False, ""
            return True, ""
        else:
            if output:
                output_crlf = output.replace("\r\n", "\n").replace("\n", "\r\n")
                self.chan.send(output_crlf)
            return success, output

    def _run_single_command(self, cmd_line):
        """Runs a single command. Expands variables and resolves VFS paths."""
        try:
            args = shlex.split(cmd_line)
        except ValueError:
            args = cmd_line.split()
            
        if not args:
            return True, ""
            
        # Inline assignments/exports
        if args[0] == "export":
            if len(args) > 1:
                parts = args[1].split("=", 1)
                if len(parts) == 2:
                    self.env[parts[0]] = parts[1]
            return True, ""
            
        if "=" in args[0] and not args[0].startswith("./") and not args[0].startswith("/"):
            for arg in args:
                if "=" in arg:
                    k, v = arg.split("=", 1)
                    self.env[k] = v
                else:
                    break
            return True, ""
            
        # Variable Expansion
        expanded = []
        for arg in args:
            def repl(match):
                return self.env.get(match.group(1), "")
            new_arg = re.sub(r'\$(\w+)', repl, arg)
            expanded.append(new_arg)
        args = expanded
        
        cmd_name = args[0]
        
        # Shell exit builtins
        if cmd_name in ("exit", "logout"):
            if self.nested_ssh:
                self.exit_nested_ssh()
                return True, ""
            else:
                raise EOFError()
                
        # Command execution path lookup
        # Check standard paths if not starting with slash or dot
        cmd_path = None
        if cmd_name.startswith("/") or cmd_name.startswith("./") or cmd_name.startswith("../"):
            resolved = self.vfs.resolve_path(self.current_dir, cmd_name)
            if self.vfs.exists(resolved) and self.vfs.is_file(resolved):
                cmd_path = resolved
        else:
            # Check builtins first
            builtin_methods = {
                "cd": self._cmd_cd,
                "pwd": self._cmd_pwd,
                "ls": self._cmd_ls,
                "cat": self._cmd_cat,
                "echo": self._cmd_echo,
                "mkdir": self._cmd_mkdir,
                "rm": self._cmd_rm,
                "touch": self._cmd_touch,
                "cp": self._cmd_cp,
                "mv": self._cmd_mv,
                "chmod": self._cmd_chmod,
                "chown": self._cmd_chown,
                "find": self._cmd_find,
                "grep": self._cmd_grep,
                "wc": self._cmd_wc,
                "head": self._cmd_head,
                "tail": self._cmd_tail,
                "whoami": self._cmd_whoami,
                "id": self._cmd_id,
                "uname": self._cmd_uname,
                "df": self._cmd_df,
                "free": self._cmd_free,
                "ifconfig": self._cmd_ifconfig,
                "ip": self._cmd_ip,
                "uptime": self._cmd_uptime,
                "ps": self._cmd_ps,
                "top": self._cmd_top,
                "env": self._cmd_env,
                "printenv": self._cmd_env,
                "history": self._cmd_history,
                "clear": self._cmd_clear,
                "ping": self._cmd_ping,
                "wget": self._cmd_wget,
                "curl": self._cmd_curl,
                "apt": self._cmd_apt,
                "apt-get": self._cmd_apt,
                "dpkg": self._cmd_dpkg,
                "nano": self._cmd_nano,
                "vi": self._cmd_nano,
                "vim": self._cmd_nano,
                "python": self._cmd_python,
                "python3": self._cmd_python,
                "ssh": self._cmd_ssh,
                "nc": self._cmd_nc,
                "netcat": self._cmd_nc,
                "sudo": self._cmd_sudo,
                "su": self._cmd_sudo,
                "passwd": self._cmd_passwd
            }
            if cmd_name in builtin_methods:
                return builtin_methods[cmd_name](args)
                
            # Scan PATH directories in VFS
            paths = self.env.get("PATH", "").split(":")
            for p in paths:
                check_path = self.vfs.resolve_path(p, cmd_name)
                if self.vfs.exists(check_path) and self.vfs.is_file(check_path):
                    cmd_path = check_path
                    break
                    
        if cmd_path:
            # Script or custom payload execution
            content = self.vfs.read_file(cmd_path) or ""
            # If shebang is present or script is .sh
            if content.startswith("#!") or cmd_path.endswith(".sh"):
                lines = content.splitlines()
                script_output = []
                for line in lines:
                    if line.startswith("#!"):
                        continue
                    if line.strip():
                        # We capture the prints sent inside script
                        # For simple simulation, run recursively
                        self.execute(line)
                return True, ""
            else:
                return True, f"bash: {cmd_name}: cannot execute binary file: Exec format error\n"
                
        # Check command registry in commands.json
        cmd_str = " ".join(args)
        if cmd_str in self.commands_config.get("commands", {}):
            return True, self.commands_config["commands"][cmd_str]["output"]
        if cmd_name in self.commands_config.get("commands", {}):
            return True, self.commands_config["commands"][cmd_name]["output"]
            
        default_error = self.commands_config.get("default_error", "bash: {cmd}: command not found\n")
        return False, default_error.format(cmd=cmd_name)

    def _run_pipe_command(self, pipe_cmd, input_text):
        """Passes input_text through standard pipeline tools."""
        parts = pipe_cmd.split()
        if not parts:
            return True, input_text
        cmd = parts[0]
        
        if cmd == "grep":
            case_insensitive = any("i" in p for p in parts[1:] if p.startswith("-"))
            invert = any("v" in p for p in parts[1:] if p.startswith("-"))
            terms = [p for p in parts[1:] if not p.startswith("-")]
            if not terms:
                return True, input_text
            term = terms[0].strip("'\"")
            
            lines = input_text.splitlines()
            matching = []
            for line in lines:
                found = term.lower() in line.lower() if case_insensitive else term in line
                if found if not invert else not found:
                    matching.append(line)
            return True, "\n".join(matching) + ("\n" if matching else "")
            
        elif cmd == "wc":
            lines = input_text.splitlines()
            if len(parts) > 1 and "l" in parts[1]:
                return True, f"{len(lines)}\n"
            words = len(input_text.split())
            chars = len(input_text)
            return True, f"      {len(lines)}       {words}      {chars}\n"
            
        elif cmd == "head":
            n = 10
            if len(parts) > 2 and parts[1] == "-n":
                try: n = int(parts[2])
                except ValueError: pass
            lines = input_text.splitlines()
            return True, "\n".join(lines[:n]) + ("\n" if lines else "")
            
        elif cmd == "tail":
            n = 10
            if len(parts) > 2 and parts[1] == "-n":
                try: n = int(parts[2])
                except ValueError: pass
            lines = input_text.splitlines()
            return True, "\n".join(lines[-n:]) + ("\n" if lines else "")
            
        return True, input_text

    # ==========================================
    # Command Implementations
    # ==========================================
    def _cmd_cd(self, args):
        target = args[1] if len(args) > 1 else "~"
        if target == "~":
            target = self.env.get("HOME", "/home/ubuntu")
        resolved = self.vfs.resolve_path(self.current_dir, target)
        if self.vfs.exists(resolved):
            if self.vfs.is_dir(resolved):
                self.current_dir = resolved
                self.env["PWD"] = self.current_dir
                return True, ""
            else:
                return False, f"bash: cd: {target}: Not a directory\n"
        else:
            return False, f"bash: cd: {target}: No such file or directory\n"

    def _cmd_pwd(self, args):
        return True, self.current_dir + "\n"

    def _cmd_ls(self, args):
        flags = []
        targets = []
        for arg in args[1:]:
            if arg.startswith("-"):
                flags.extend(list(arg[1:]))
            else:
                targets.append(arg)
                
        target_dir = targets[0] if targets else "."
        if target_dir == "~":
            target_dir = self.env.get("HOME", "/home/ubuntu")
            
        resolved_dir = self.vfs.resolve_path(self.current_dir, target_dir)
        if not self.vfs.exists(resolved_dir):
            return False, f"ls: cannot access '{target_dir}': No such file or directory\n"
            
        show_all = "a" in flags
        show_long = "l" in flags
        
        # Mode converter helper
        def mode_str(mode, is_dir):
            rwx = ["---", "--x", "-w-", "-wx", "r--", "r-x", "rw-", "rwx"]
            u = rwx[(mode >> 6) & 7]
            g = rwx[(mode >> 3) & 7]
            o = rwx[mode & 7]
            prefix = "d" if is_dir else "-"
            return prefix + u + g + o

        if not self.vfs.is_dir(resolved_dir):
            stat_info = self.vfs.stat(resolved_dir)
            _, name = self.vfs._split_path(resolved_dir)
            if show_long:
                perm = mode_str(stat_info["mode"], False)
                date = time.strftime("%b %d %H:%M", time.localtime(stat_info["mtime"]))
                return True, f"{perm} 1 {stat_info['owner']} {stat_info['group']} {stat_info['size']} {date} {name}\n"
            else:
                return True, name + "\n"
                
        files = self.vfs.list_dir(resolved_dir)
        names = sorted(files.keys())
        if show_all:
            names = [".", ".."] + names
            
        if show_long:
            lines = []
            total_blocks = len(files) * 4
            lines.append(f"total {total_blocks}")
            for name in names:
                if name == ".":
                    p_stat = self.vfs.stat(resolved_dir)
                    perm = mode_str(p_stat["mode"], True)
                    date = time.strftime("%b %d %H:%M", time.localtime(p_stat["mtime"]))
                    lines.append(f"{perm} 2 {p_stat['owner']} {p_stat['group']} 4096 {date} .")
                    continue
                if name == "..":
                    parent, _ = self.vfs._split_path(resolved_dir)
                    p_stat = self.vfs.stat(parent) if self.vfs.exists(parent) else self.vfs.stat(resolved_dir)
                    perm = mode_str(p_stat["mode"], True)
                    date = time.strftime("%b %d %H:%M", time.localtime(p_stat["mtime"]))
                    lines.append(f"{perm} 2 {p_stat['owner']} {p_stat['group']} 4096 {date} ..")
                    continue
                child_path = resolved_dir + "/" + name if resolved_dir != "/" else "/" + name
                stat_info = self.vfs.stat(child_path)
                perm = mode_str(stat_info["mode"], self.vfs.is_dir(child_path))
                date = time.strftime("%b %d %H:%M", time.localtime(stat_info["mtime"]))
                lines.append(f"{perm} 1 {stat_info['owner']} {stat_info['group']} {stat_info['size']} {date} {name}")
            return True, "\n".join(lines) + "\n"
        else:
            if not names:
                return True, ""
            return True, "  ".join(names) + "\n"

    def _cmd_cat(self, args):
        if len(args) < 2:
            return True, ""
        outputs = []
        success = True
        for target in args[1:]:
            resolved = self.vfs.resolve_path(self.current_dir, target)
            if not self.vfs.exists(resolved):
                outputs.append(f"cat: {target}: No such file or directory")
                success = False
            elif self.vfs.is_dir(resolved):
                outputs.append(f"cat: {target}: Is a directory")
                success = False
            else:
                outputs.append(self.vfs.read_file(resolved) or "")
        return success, "\n".join(outputs) + "\n"

    def _cmd_echo(self, args):
        n_flag = False
        e_flag = False
        start_idx = 1
        
        while start_idx < len(args) and args[start_idx].startswith("-"):
            opt = args[start_idx]
            if "n" in opt: n_flag = True
            if "e" in opt: e_flag = True
            start_idx += 1
            
        content = " ".join(args[start_idx:])
        
        if e_flag:
            # Basic backslash escape evaluation
            content = content.replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")
            
        if not n_flag:
            content += "\n"
        return True, content

    def _cmd_mkdir(self, args):
        if len(args) < 2:
            return False, "mkdir: missing operand\n"
        errs = []
        for target in args[1:]:
            if target.startswith("-"):
                continue
            resolved = self.vfs.resolve_path(self.current_dir, target)
            if not self.vfs.mkdir(resolved):
                errs.append(f"mkdir: cannot create directory '{target}': File exists or parent does not exist")
        if errs:
            return False, "\n".join(errs) + "\n"
        return True, ""

    def _cmd_rm(self, args):
        if len(args) < 2:
            return False, "rm: missing operand\n"
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
            return False, "\n".join(errs) + "\n"
        return True, ""

    def _cmd_touch(self, args):
        if len(args) < 2:
            return False, "touch: missing file operand\n"
        for target in args[1:]:
            if target.startswith("-"):
                continue
            resolved = self.vfs.resolve_path(self.current_dir, target)
            if not self.vfs.exists(resolved):
                self.vfs.write_file(resolved, "")
            else:
                # Update mtime
                self.vfs.chmod(resolved, self.vfs.stat(resolved)["mode"])
        return True, ""

    def _cmd_cp(self, args):
        if len(args) < 3:
            return False, "cp: missing file operand\n"
        src = self.vfs.resolve_path(self.current_dir, args[1])
        dst = self.vfs.resolve_path(self.current_dir, args[2])
        if not self.vfs.exists(src) or self.vfs.is_dir(src):
            return False, f"cp: cannot stat '{args[1]}': No such file or directory\n"
        
        # If dst is directory, copy inside
        if self.vfs.exists(dst) and self.vfs.is_dir(dst):
            _, fname = self.vfs._split_path(src)
            dst = dst + "/" + fname if dst != "/" else "/" + fname
            
        content = self.vfs.read_file(src)
        success = self.vfs.write_file(dst, content)
        # Match permissions
        if success:
            self.vfs.chmod(dst, self.vfs.stat(src)["mode"])
        return success, ""

    def _cmd_mv(self, args):
        if len(args) < 3:
            return False, "mv: missing file operand\n"
        src = self.vfs.resolve_path(self.current_dir, args[1])
        dst = self.vfs.resolve_path(self.current_dir, args[2])
        if not self.vfs.exists(src):
            return False, f"mv: cannot stat '{args[1]}': No such file or directory\n"
            
        if self.vfs.exists(dst) and self.vfs.is_dir(dst):
            _, fname = self.vfs._split_path(src)
            dst = dst + "/" + fname if dst != "/" else "/" + fname
            
        if self.vfs.is_dir(src):
            # Move directory (simplified rm/mkdir)
            # For simplicity inside the VFS:
            return False, "mv: directory moving not fully implemented\n"
            
        content = self.vfs.read_file(src)
        if self.vfs.write_file(dst, content):
            self.vfs.chmod(dst, self.vfs.stat(src)["mode"])
            self.vfs.rm(src)
            return True, ""
        return False, "mv: failed to move\n"

    def _cmd_chmod(self, args):
        if len(args) < 3:
            return False, "chmod: missing operand\n"
        mode = args[1]
        target = self.vfs.resolve_path(self.current_dir, args[2])
        if self.vfs.chmod(target, mode):
            return True, ""
        return False, f"chmod: cannot access '{args[2]}': No such file or directory\n"

    def _cmd_chown(self, args):
        if len(args) < 3:
            return False, "chown: missing operand\n"
        owner_part = args[1]
        target = self.vfs.resolve_path(self.current_dir, args[2])
        
        owner = owner_part
        group = None
        if ":" in owner_part:
            owner, group = owner_part.split(":", 1)
            
        if self.vfs.chown(target, owner, group):
            return True, ""
        return False, f"chown: cannot access '{args[2]}': No such file or directory\n"

    def _cmd_find(self, args):
        target_dir = args[1] if len(args) > 1 and not args[1].startswith("-") else "."
        resolved = self.vfs.resolve_path(self.current_dir, target_dir)
        if not self.vfs.exists(resolved):
            return False, f"find: '{target_dir}': No such file or directory\n"
            
        # Recursive list helper
        results = []
        def recurse(path):
            results.append(path)
            if self.vfs.is_dir(path):
                files = self.vfs.list_dir(path)
                for f in sorted(files.keys()):
                    child = path + "/" + f if path != "/" else "/" + f
                    recurse(child)
        recurse(resolved)
        
        # Check filters (e.g. -name "*.txt")
        name_pattern = None
        if "-name" in args:
            idx = args.index("-name")
            if idx + 1 < len(args):
                name_pattern = args[idx+1].replace("*", ".*")
                
        filtered = []
        for r in results:
            _, fname = self.vfs._split_path(r)
            if name_pattern:
                if re.match(name_pattern, fname):
                    filtered.append(r)
            else:
                filtered.append(r)
                
        # output relative paths matching target_dir
        out_lines = []
        for path in filtered:
            if target_dir == ".":
                # Convert absolute resolved path to relative '.'
                rel = "." + path[len(resolved):]
                out_lines.append(rel)
            else:
                out_lines.append(path)
        return True, "\n".join(out_lines) + "\n"

    def _cmd_grep(self, args):
        # Grep standalone (reading files)
        case_insensitive = "-i" in args
        invert = "-v" in args
        show_lines = "-n" in args
        
        cleaned_args = [a for a in args[1:] if not a.startswith("-")]
        if len(cleaned_args) < 2:
            return False, "grep: pattern or file missing\n"
            
        pattern = cleaned_args[0].strip("'\"")
        file_args = cleaned_args[1:]
        
        outputs = []
        for f in file_args:
            resolved = self.vfs.resolve_path(self.current_dir, f)
            if not self.vfs.exists(resolved):
                outputs.append(f"grep: {f}: No such file or directory")
                continue
            if self.vfs.is_dir(resolved):
                outputs.append(f"grep: {f}: Is a directory")
                continue
                
            content = self.vfs.read_file(resolved) or ""
            for idx, line in enumerate(content.splitlines()):
                found = pattern.lower() in line.lower() if case_insensitive else pattern in line
                if found if not invert else not found:
                    prefix = f"{f}:{idx+1}:" if show_lines else ""
                    outputs.append(prefix + line)
        return True, "\n".join(outputs) + "\n"

    def _cmd_wc(self, args):
        l_flag = "-l" in args
        cleaned_args = [a for a in args[1:] if not a.startswith("-")]
        if not cleaned_args:
            return True, ""
        
        outputs = []
        for f in cleaned_args:
            resolved = self.vfs.resolve_path(self.current_dir, f)
            if not self.vfs.exists(resolved) or self.vfs.is_dir(resolved):
                outputs.append(f"wc: {f}: No such file or directory")
                continue
            content = self.vfs.read_file(resolved) or ""
            lines = content.splitlines()
            if l_flag:
                outputs.append(f"{len(lines)} {f}")
            else:
                words = len(content.split())
                chars = len(content)
                outputs.append(f" {len(lines)}  {words} {chars} {f}")
        return True, "\n".join(outputs) + "\n"

    def _cmd_head(self, args):
        n = 10
        if "-n" in args:
            try: n = int(args[args.index("-n")+1])
            except (ValueError, IndexError): pass
        cleaned_args = [a for a in args[1:] if not a.startswith("-") and a != str(n)]
        if not cleaned_args: return True, ""
        resolved = self.vfs.resolve_path(self.current_dir, cleaned_args[0])
        content = self.vfs.read_file(resolved) or ""
        lines = content.splitlines()
        return True, "\n".join(lines[:n]) + "\n"

    def _cmd_tail(self, args):
        n = 10
        if "-n" in args:
            try: n = int(args[args.index("-n")+1])
            except (ValueError, IndexError): pass
        cleaned_args = [a for a in args[1:] if not a.startswith("-") and a != str(n)]
        if not cleaned_args: return True, ""
        resolved = self.vfs.resolve_path(self.current_dir, cleaned_args[0])
        content = self.vfs.read_file(resolved) or ""
        lines = content.splitlines()
        return True, "\n".join(lines[-n:]) + "\n"

    def _cmd_whoami(self, args):
        return True, self.env.get("USER", "ubuntu") + "\n"

    def _cmd_id(self, args):
        user = self.env.get("USER", "ubuntu")
        if user == "root":
            return True, "uid=0(root) gid=0(root) groups=0(root)\n"
        return True, "uid=1000(ubuntu) gid=1000(ubuntu) groups=1000(ubuntu),27(sudo)\n"

    def _cmd_uname(self, args):
        if "-a" in args:
            host = self.env.get("HOSTNAME", "ubuntu-server")
            return True, f"Linux {host} 5.15.0-76-generic #83-Ubuntu SMP Thu Jun 15 19:16:32 UTC 2023 x86_64 x86_64 x86_64 GNU/Linux\n"
        return True, "Linux\n"

    def _cmd_df(self, args):
        h_flag = "-h" in args
        if h_flag:
            out = "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        49G   12G   34G  27% /\ntmpfs           2.0G     0  2.0G   0% /dev/shm\ntmpfs           785M  824K  785M   1% /run\n"
        else:
            out = "Filesystem     1K-blocks     Used Available Use% Mounted on\n/dev/sda1       50257024 12582912  35114112  27% /\ntmpfs            2009216        0   2009216   0% /dev/shm\ntmpfs             803688      824    802864   1% /run\n"
        return True, out

    def _cmd_free(self, args):
        h_flag = "-h" in args
        m_flag = "-m" in args
        if h_flag:
            out = "               total        used        free      shared  buff/cache   available\nMem:           3.8Gi       850Mi       1.2Gi        10Mi       1.8Gi       2.8Gi\nSwap:          2.0Gi          0B       2.0Gi\n"
        elif m_flag:
            out = "              total        used        free      shared  buff/cache   available\nMem:           3924         850        1240          10        1834        2810\nSwap:          2047           0        2047\n"
        else:
            out = "              total        used        free      shared  buff/cache   available\nMem:        4018432      870400     1269760       10240     1878272     2877440\nSwap:       2097148           0     2097148\n"
        return True, out

    def _cmd_ifconfig(self, args):
        out = "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n        inet 192.168.1.105  netmask 255.255.255.0  broadcast 192.168.1.255\n        inet6 fe80::a00:27ff:fe8a:8d2b  prefixlen 64  scopeid 0x20<link>\n        ether 08:00:27:8a:8d:2b  txqueuelen 1000  (Ethernet)\n        RX packets 12053  bytes 910403 (910.4 KB)\n        TX packets 8540  bytes 820301 (820.3 KB)\n\nlo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536\n        inet 127.0.0.1  netmask 255.0.0.0\n        inet6 ::1  prefixlen 128  scopeid 0x10<host>\n        loop  txqueuelen 1000  (Local Loopback)\n        RX packets 102  bytes 8160 (8.1 KB)\n        TX packets 102  bytes 8160 (8.1 KB)\n"
        return True, out

    def _cmd_ip(self, args):
        out = "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000\n    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00\n    inet 127.0.0.1/8 scope host lo\n       valid_lft forever preferred_lft forever\n    inet6 ::1/128 scope host \n       valid_lft forever preferred_lft forever\n2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000\n    link/ether 08:00:27:8a:8d:2b brd ff:ff:ff:ff:ff:ff\n    inet 192.168.1.105/24 brd 192.168.1.255 scope global dynamic eth0\n       valid_lft 86120sec preferred_lft 86120sec\n    inet6 fe80::a00:27ff:fe8a:8d2b/64 scope link \n       valid_lft forever preferred_lft forever\n"
        return True, out

    def _cmd_uptime(self, args):
        now = time.strftime("%H:%M:%S")
        return True, f" {now} up 1:24,  1 user,  load average: 0.05, 0.03, 0.01\n"

    def _cmd_ps(self, args):
        out = "  PID TTY          TIME CMD\n"
        out += " 1129 pts/0    00:00:00 bash\n"
        if self.state != "NORMAL":
            out += f" 1250 pts/0    00:00:00 {self.state.lower()}\n"
        else:
            out += " 1284 pts/0    00:00:00 ps\n"
        return True, out

    def _cmd_env(self, args):
        out = []
        for k, v in self.env.items():
            out.append(f"{k}={v}")
        return True, "\n".join(out) + "\n"

    def _cmd_history(self, args):
        out = []
        for idx, cmd in enumerate(self.history):
            out.append(f"  {idx+1}  {cmd}")
        return True, "\n".join(out) + "\n"

    def _cmd_clear(self, args):
        self.chan.send("\x1b[2J\x1b[H")
        return True, ""

    def _cmd_wget(self, args):
        url = None
        for arg in args[1:]:
            if arg.startswith("http://") or arg.startswith("https://"):
                url = arg
                break
        if not url:
            return False, "wget: missing URL\n"
            
        filename = "index.html"
        if "/" in url:
            parts = url.split("/")
            if parts[-1]:
                filename = parts[-1].split("?")[0]
        
        resolved_file = self.vfs.resolve_path(self.current_dir, filename)
        self.logger.log_download(self.client_ip, url, resolved_file)
        
        self.chan.send(f"--{time.strftime('%Y-%m-%d %H:%M:%S')}--  {url}\r\n")
        host = url.split("/")[2] if len(url.split("/")) > 2 else "localhost"
        self.chan.send(f"Resolving {host}... 192.0.2.1\r\n")
        self.chan.send(f"Connecting to {host}|192.0.2.1|:80... connected.\r\n")
        self.chan.send("HTTP request sent, awaiting response... 200 OK\r\n")
        self.chan.send("Length: 2048 (2.0K) [application/x-sh]\r\n")
        self.chan.send(f"Saving to: '{filename}'\r\n\r\n")
        
        for k in range(1, 101, 10):
            self.chan.send(f" {k}% " + "." * (k // 10) + "\r")
            time.sleep(0.1)
            
        self.chan.send("\r\n\r\n")
        self.chan.send(f"{time.strftime('%Y-%m-%d %H:%M:%S')} (1.2 MB/s) - '{filename}' saved [2048/2048]\r\n")
        
        dummy_content = f"#!/bin/bash\n# Simulated payload downloaded from {url}\necho 'Error: system architecture not supported'\n"
        self.vfs.write_file(resolved_file, dummy_content)
        return True, ""

    def _cmd_curl(self, args):
        url = None
        for arg in args[1:]:
            if arg.startswith("http://") or arg.startswith("https://"):
                url = arg
                break
        if not url:
            return False, "curl: missing URL\n"
            
        filename = "index.html"
        if "/" in url:
            parts = url.split("/")
            if parts[-1]:
                filename = parts[-1].split("?")[0]
        
        resolved_file = self.vfs.resolve_path(self.current_dir, filename)
        self.logger.log_download(self.client_ip, url, resolved_file)
        
        self.chan.send("  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current\r\n")
        self.chan.send("                                 Dload  Upload   Total   Spent    Left  Speed\r\n")
        self.chan.send("100  2048  100  2048    0     0  10240      0 --:--:-- --:--:-- --:--:-- 10240\r\n")
        
        dummy_content = f"#!/bin/bash\n# Simulated payload downloaded from {url}\necho 'Error: system architecture not supported'\n"
        self.vfs.write_file(resolved_file, dummy_content)
        return True, ""

    def _cmd_apt(self, args):
        sub = args[1] if len(args) > 1 else ""
        if sub == "update":
            self.chan.send("Hit:1 http://archive.ubuntu.com/ubuntu jammy InRelease\r\n")
            self.chan.send("Get:2 http://archive.ubuntu.com/ubuntu jammy-updates InRelease [114 kB]\r\n")
            self.chan.send("Get:3 http://security.ubuntu.com/ubuntu jammy-security InRelease [110 kB]\r\n")
            self.chan.send("Fetched 224 kB in 1s (224 kB/s)\r\n")
            self.chan.send("Reading package lists... Done\r\n")
            self.chan.send("Building dependency tree... Done\r\n")
            self.chan.send("Reading state information... Done\r\n")
            return True, ""
        elif sub == "install":
            if len(args) < 3:
                return False, "apt: missing package name\n"
            pkg = args[2]
            self.chan.send(f"Reading package lists... Done\r\n")
            self.chan.send(f"Building dependency tree... Done\r\n")
            self.chan.send(f"Reading state information... Done\r\n")
            self.chan.send(f"The following NEW packages will be installed:\r\n  {pkg}\r\n")
            self.chan.send(f"0 upgraded, 1 newly installed, 0 to remove and 12 not upgraded.\r\n")
            self.chan.send(f"Need to get 102 kB of archives.\r\n")
            self.chan.send(f"After this operation, 345 kB of additional disk space will be used.\r\n")
            self.chan.send(f"Get:1 http://archive.ubuntu.com/ubuntu jammy/main amd64 {pkg} [102 kB]\r\n")
            time.sleep(0.5)
            self.chan.send(f"Fetched 102 kB in 0s (450 kB/s)\r\n")
            self.chan.send(f"Selecting previously unselected package {pkg}.\r\n")
            self.chan.send(f"(Reading database ... 124500 files and directories currently installed.)\r\n")
            self.chan.send(f"Preparing to unpack .../{pkg}_amd64.deb ...\r\n")
            self.chan.send(f"Unpacking {pkg} ...\r\n")
            self.chan.send(f"Setting up {pkg} ...\r\n")
            
            # Install mock binary in VFS /usr/bin/ so that it's now runnable
            self.installed_packages.add(pkg)
            self.vfs.write_file(f"/usr/bin/{pkg}", f"#!/bin/bash\necho 'Simulated tool: {pkg}'\n")
            self.vfs.chmod(f"/usr/bin/{pkg}", 0o755)
            return True, ""
        return True, ""

    def _cmd_dpkg(self, args):
        l_flag = "-l" in args
        if l_flag:
            out = "Desired=Unknown/Install/Remove/Purge/Hold\n| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend\n|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)\n||/ Name           Version      Architecture Description\n+++-==============-============-============-=================================\n"
            out += "ii  bash           5.1-6ubuntu1 amd64        GNU Bourne Again SHell\n"
            out += "ii  coreutils      8.32-4.1ubun amd64        GNU core utilities\n"
            for pkg in self.installed_packages:
                out += f"ii  {pkg:<14} 1.0-1       amd64        Simulated package {pkg}\n"
            return True, out
        return True, ""

    def _cmd_sudo(self, args):
        sub_args = args[1:]
        if not sub_args:
            return True, ""
        # Skip flags
        while sub_args and sub_args[0].startswith("-"):
            sub_args.pop(0)
        if not sub_args:
            return True, ""
        cmd_line = " ".join(sub_args)
        # Sudo acts as root
        old_user = self.env["USER"]
        self.env["USER"] = "root"
        success, out = self._run_single_command(cmd_line)
        self.env["USER"] = old_user
        return success, out

    def _cmd_passwd(self, args):
        self.chan.send("Enter new UNIX password: ")
        # read password (no echoing)
        p1 = self._read_silent_line()
        self.chan.send("\r\nRetype new UNIX password: ")
        p2 = self._read_silent_line()
        self.chan.send("\r\n")
        if p1 == p2:
            return True, "passwd: password updated successfully\n"
        return False, "passwd: Authentication token manipulation error\npasswd: password unchanged\n"

    def _read_silent_line(self):
        buf = ""
        while True:
            char = self.read_char()
            if char in ('\r', '\n'):
                break
            elif char in ('\x7f', '\x08'):
                if buf: buf = buf[:-1]
            else:
                buf += char
        return buf

    # ==========================================
    # Interactive Nano Simulator
    # ==========================================
    def _cmd_nano(self, args):
        if len(args) < 2:
            return False, "nano: missing file operand\n"
        filename = args[1]
        resolved = self.vfs.resolve_path(self.current_dir, filename)
        
        # Load content if file exists
        if self.vfs.exists(resolved):
            if self.vfs.is_dir(resolved):
                return False, f"nano: '{filename}' is a directory\n"
            content = self.vfs.read_file(resolved) or ""
            self.nano_lines = content.splitlines() if content else [""]
        else:
            # Check parent directory
            parent, name = self.vfs._split_path(resolved)
            if not self.vfs.is_dir(parent):
                return False, f"nano: cannot create '{filename}': No such file or directory\n"
            self.nano_lines = [""]
            
        self.nano_filepath = resolved
        self.nano_filename = filename
        self.nano_row = 0
        self.nano_col = 0
        self.nano_scroll = 0
        self.state = "NANO"
        
        self.draw_nano()
        return True, ""

    def draw_nano(self, message=""):
        # Clear screen
        self.chan.send("\x1b[2J\x1b[H")
        # Header bar (line 1)
        self.chan.send("\x1b[7m  GNU nano 6.2           File: " + self.nano_filename + " " * 30 + "\x1b[0m\r\n")
        
        # Draw text area (20 lines max)
        max_rows = 20
        for i in range(max_rows):
            line_idx = self.nano_scroll + i
            if line_idx < len(self.nano_lines):
                line = self.nano_lines[line_idx]
                self.chan.send(line[:80] + "\r\n")
            else:
                self.chan.send("\r\n")
                
        # Status/message bar (line 22)
        if message:
            self.chan.send(f"\x1b[7m[ {message} ]\x1b[0m" + " " * (80 - len(message) - 4) + "\r\n")
        else:
            self.chan.send("\r\n")
            
        # Shortcuts bar (lines 23-24)
        self.chan.send("\x1b[7m^G Get Help  ^O Write Out ^R Read File ^Y Prev Pg   ^K Cut Text  ^C Cur Pos   \x1b[0m\r\n")
        self.chan.send("\x1b[7m^X Exit      ^J Justify   ^W Where Is  ^V Next Pg   ^U Uncut Text^T To Spell  \x1b[0m")
        
        # Position Cursor
        term_row = 2 + (self.nano_row - self.nano_scroll)
        term_col = 1 + self.nano_col
        self.chan.send(f"\x1b[{term_row};{term_col}H")

    def handle_nano_char(self, char):
        if char == "\x18":  # Ctrl+X
            self.state = "NORMAL"
            self.chan.send("\x1b[2J\x1b[H") # clear
        elif char == "\x0f":  # Ctrl+O
            content = "\n".join(self.nano_lines)
            self.vfs.write_file(self.nano_filepath, content)
            self.draw_nano(message=f"Wrote {len(self.nano_lines)} lines")
        elif char in ('\r', '\n'):
            line = self.nano_lines[self.nano_row]
            self.nano_lines[self.nano_row] = line[:self.nano_col]
            self.nano_lines.insert(self.nano_row + 1, line[self.nano_col:])
            self.nano_row += 1
            self.nano_col = 0
            # Scroll down if cursor falls below screen
            if self.nano_row - self.nano_scroll >= 20:
                self.nano_scroll += 1
            self.draw_nano()
        elif char in ('\x7f', '\x08'):  # Backspace
            if self.nano_col > 0:
                line = self.nano_lines[self.nano_row]
                self.nano_lines[self.nano_row] = line[:self.nano_col-1] + line[self.nano_col:]
                self.nano_col -= 1
                self.draw_nano()
            elif self.nano_row > 0:
                prev_line = self.nano_lines[self.nano_row-1]
                cur_line = self.nano_lines[self.nano_row]
                self.nano_col = len(prev_line)
                self.nano_lines[self.nano_row-1] = prev_line + cur_line
                self.nano_lines.pop(self.nano_row)
                self.nano_row -= 1
                if self.nano_scroll > 0:
                    self.nano_scroll -= 1
                self.draw_nano()
        elif ord(char) >= 32:
            line = self.nano_lines[self.nano_row]
            self.nano_lines[self.nano_row] = line[:self.nano_col] + char + line[self.nano_col:]
            self.nano_col += 1
            self.draw_nano()

    def handle_nano_ansi(self, seq):
        if seq == "\x1b[A":  # Up
            if self.nano_row > 0:
                self.nano_row -= 1
                self.nano_col = min(self.nano_col, len(self.nano_lines[self.nano_row]))
                if self.nano_row < self.nano_scroll:
                    self.nano_scroll -= 1
                self.draw_nano()
        elif seq == "\x1b[B":  # Down
            if self.nano_row < len(self.nano_lines) - 1:
                self.nano_row += 1
                self.nano_col = min(self.nano_col, len(self.nano_lines[self.nano_row]))
                if self.nano_row - self.nano_scroll >= 20:
                    self.nano_scroll += 1
                self.draw_nano()
        elif seq == "\x1b[C":  # Right
            if self.nano_col < len(self.nano_lines[self.nano_row]):
                self.nano_col += 1
                self.draw_nano()
            elif self.nano_row < len(self.nano_lines) - 1:
                self.nano_row += 1
                self.nano_col = 0
                if self.nano_row - self.nano_scroll >= 20:
                    self.nano_scroll += 1
                self.draw_nano()
        elif seq == "\x1b[D":  # Left
            if self.nano_col > 0:
                self.nano_col -= 1
                self.draw_nano()
            elif self.nano_row > 0:
                self.nano_row -= 1
                self.nano_col = len(self.nano_lines[self.nano_row])
                if self.nano_row < self.nano_scroll:
                    self.nano_scroll -= 1
                self.draw_nano()

    # ==========================================
    # Interactive Top Simulator
    # ==========================================
    def _cmd_top(self, args):
        self.state = "TOP"
        self.draw_top()
        return True, ""

    def draw_top(self):
        # Clear screen
        self.chan.send("\x1b[2J\x1b[H")
        now = time.strftime("%H:%M:%S")
        
        # System statistics
        self.chan.send(f"top - {now} up 1:24,  1 user,  load average: {random.uniform(0.01, 0.09):.2f}, {random.uniform(0.01, 0.05):.2f}, 0.01\r\n")
        self.chan.send("Tasks:  98 total,   1 running,  97 sleeping,   0 stopped,   0 zombie\r\n")
        self.chan.send(f"%Cpu(s):  {random.uniform(0.5, 2.5):.1f} us,  {random.uniform(0.2, 1.0):.1f} sy,  0.0 ni, 98.3 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st\r\n")
        self.chan.send("MiB Mem :   3924.0 total,   1240.2 free,    850.1 used,   1833.7 buff/cache\r\n")
        self.chan.send("MiB Swap:   2047.0 total,   2047.0 free,      0.0 used.   2810.1 avail Mem\r\n\r\n")
        
        # Process list header
        self.chan.send("\x1b[7m  PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND      \x1b[0m\r\n")
        
        # Draw process rows
        procs = [
            ("1", "root", "20", "0", "168340", "9520", "6104", "S", "0.0", "0.2", "0:02.45", "systemd"),
            ("2", "root", "20", "0", "0", "0", "0", "S", "0.0", "0.0", "0:00.00", "kthreadd"),
            ("12", "root", "20", "0", "0", "0", "0", "I", f"{random.uniform(0.0, 0.2):.1f}", "0.0", "0:01.12", "kworker/0:1"),
            ("842", "root", "20", "0", "45620", "4102", "3120", "S", "0.0", "0.1", "0:00.45", "cron"),
            ("1124", "root", "20", "0", "78400", "8120", "5120", "S", "0.0", "0.2", "0:05.18", "sshd"),
            ("1128", "ubuntu", "20", "0", "98340", "9200", "6100", "S", f"{random.uniform(0.1, 0.5):.1f}", "0.2", "0:01.32", "sshd"),
            ("1129", "ubuntu", "20", "0", "22340", "4120", "3100", "S", "0.0", "0.1", "0:00.54", "bash"),
            ("1250", "ubuntu", "20", "0", "18400", "3200", "2800", "R", f"{random.uniform(1.0, 3.5):.1f}", "0.1", "0:00.12", "top"),
        ]
        
        for p in procs:
            self.chan.send(f"{p[0]:>5} {p[1]:<9} {p[2]:>2} {p[3]:>3} {p[4]:>7} {p[5]:>6} {p[6]:>6} {p[7]} {p[8]:>5} {p[9]:>5} {p[10]:>9} {p[11]}\r\n")
            
        self.chan.send("\r\nPress 'q' or ESC to exit.")

    def handle_top_char(self, char):
        if char in ('q', '\x1b', '\x03'):
            self.state = "NORMAL"
            self.chan.send("\x1b[2J\x1b[H")

    # ==========================================
    # Interactive Ping Simulator
    # ==========================================
    def _cmd_ping(self, args):
        if len(args) < 2:
            return False, "ping: missing host operand\n"
        self.ping_host = args[1]
        self.ping_seq = 0
        self.ping_sent = 0
        self.ping_recv = 0
        self.ping_start_time = time.time()
        self.state = "PING"
        self.chan.send(f"PING {self.ping_host} ({self.ping_host}) 56(84) bytes of data.\r\n")
        self.run_ping_step()
        return True, ""

    def run_ping_step(self):
        self.ping_seq += 1
        self.ping_sent += 1
        self.ping_recv += 1
        time_ms = random.uniform(8.5, 18.2)
        self.chan.send(f"64 bytes from {self.ping_host}: icmp_seq={self.ping_seq} ttl=64 time={time_ms:.1f} ms\r\n")

    def handle_ping_char(self, char):
        if char == "\x03":  # Ctrl+C
            self.state = "NORMAL"
            total_time = int((time.time() - self.ping_start_time) * 1000)
            self.chan.send(f"\r\n--- {self.ping_host} ping statistics ---\r\n")
            self.chan.send(f"{self.ping_sent} packets transmitted, {self.ping_recv} received, 0% packet loss, time {total_time}ms\r\n")
            self.chan.send("rtt min/avg/max/mdev = 8.512/12.450/18.210/2.320 ms\r\n")

    # ==========================================
    # Interactive Python REPL Simulator
    # ==========================================
    def _cmd_python(self, args):
        self.state = "PYTHON"
        self.buffer = ""
        self.cursor_idx = 0
        self.chan.send("Python 3.10.6 (main, May 29 2023, 11:10:38) \r\n[GCC 11.3.0] on linux\r\n")
        self.chan.send("Type \"help\", \"copyright\", \"credits\" or \"license\" for more information.\r\n>>> ")
        return True, ""

    def handle_python_char(self, char):
        if char in ('\r', '\n'):
            self.chan.send("\r\n")
            cmd = self.buffer.strip()
            if cmd in ("exit()", "quit()"):
                self.state = "NORMAL"
                self.buffer = ""
                self.cursor_idx = 0
                return
                
            if cmd:
                # Execution in dedicated namespace
                old_stdout = sys.stdout
                redirected = io.StringIO()
                sys.stdout = redirected
                try:
                    try:
                        val = eval(cmd, self.python_globals)
                        if val is not None:
                            print(val)
                    except SyntaxError:
                        exec(cmd, self.python_globals)
                except Exception as e:
                    print(f"{type(e).__name__}: {e}")
                finally:
                    sys.stdout = old_stdout
                
                output = redirected.getvalue()
                if output:
                    self.chan.send(output.replace("\n", "\r\n"))
            
            self.buffer = ""
            self.cursor_idx = 0
            self.chan.send(">>> ")
            
        elif char in ('\x7f', '\x08'):  # Backspace
            if self.cursor_idx > 0:
                self.buffer = self.buffer[:self.cursor_idx-1] + self.buffer[self.cursor_idx:]
                self.cursor_idx -= 1
                self.redraw_line()
                
        elif char == '\x04':  # Ctrl+D
            self.state = "NORMAL"
            self.buffer = ""
            self.cursor_idx = 0
            self.chan.send("\r\n")
            
        elif ord(char) >= 32:
            self.buffer = self.buffer[:self.cursor_idx] + char + self.buffer[self.cursor_idx:]
            self.cursor_idx += 1
            self.redraw_line()

    # ==========================================
    # SSH Client Honeypot (decoy node)
    # ==========================================
    def _cmd_ssh(self, args):
        if len(args) < 2:
            return False, "ssh: missing host operand\n"
        target = args[1]
        
        user = "root"
        host = target
        if "@" in target:
            user, host = target.split("@", 1)
            
        self.ssh_user = user
        self.ssh_host = host
        self.state = "SSH_PASSWORD"
        self.ssh_pass_buf = ""
        self.chan.send(f"{user}@{host}'s password: ")
        return True, ""

    def handle_ssh_password_char(self, char):
        if char in ('\r', '\n'):
            self.chan.send("\r\n")
            # Setup nested SSH PTY parameters
            self.nested_ssh = True
            self.state = "NORMAL"
            self.env["USER"] = self.ssh_user
            self.env["HOSTNAME"] = self.ssh_host
            self.current_dir = "/root" if self.ssh_user == "root" else f"/home/{self.ssh_user}"
            
            # Create root folder if doesn't exist
            if not self.vfs.exists(self.current_dir):
                self.vfs.mkdir(self.current_dir)
                
            self.chan.send(f"Welcome to Debian GNU/Linux 11 (bullseye) on {self.ssh_host}\r\n")
            self.chan.send("Last login: Mon Jul 13 10:14:02 2026 from 192.168.1.100\r\n")
            
        elif char in ('\x7f', '\x08'):
            if self.ssh_pass_buf:
                self.ssh_pass_buf = self.ssh_pass_buf[:-1]
        else:
            self.ssh_pass_buf += char

    def exit_nested_ssh(self):
        self.chan.send(f"Connection to {self.ssh_host} closed.\r\n")
        self.nested_ssh = False
        self.env["USER"] = "ubuntu"
        self.env["HOSTNAME"] = "ubuntu-server"
        self.current_dir = "/home/ubuntu"
        self.state = "NORMAL"

    # ==========================================
    # Netcat / Listen Simulator
    # ==========================================
    def _cmd_nc(self, args):
        l_flag = "-l" in args
        p_flag = "-p" in args
        
        port = "4444"
        if p_flag:
            try:
                port = args[args.index("-p")+1]
            except (ValueError, IndexError):
                pass
        else:
            # look for numeric port in args
            for a in args[1:]:
                if a.isdigit():
                    port = a
                    break
                    
        if l_flag:
            self.chan.send(f"Listening on [0.0.0.0] (family 0, port {port})\r\n")
            # Wait for Ctrl+C
            while True:
                char = self.read_char()
                if char == "\x03":
                    self.chan.send("^C\r\n")
                    break
            return True, ""
        else:
            # Client mode, print connection refused or hang
            host = args[1] if len(args) > 1 else "localhost"
            self.chan.send(f"nc: connect to {host} port {port} (tcp) failed: Connection refused\r\n")
            return False, ""
