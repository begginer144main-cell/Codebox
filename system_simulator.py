#!/usr/bin/env python3
"""
System Simulator Core v2.0
A playful, dependency-free terminal OS simulator.
"""

import base64
import hashlib
import json
import os
import random
import shlex
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


SAVE_FILE = Path(__file__).with_name("system_state.json")
PROTECTED_PROCESSES = {"kernel.exe"}
PROTECTED_PATHS = {"/system"}


class UIRenderer:
    @staticmethod
    def clear_screen() -> None:
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def typing_effect(text: str, delay: float = 0.02) -> None:
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    @staticmethod
    def glitch_text(text: str, glitch_chance: float = 0.3) -> str:
        glitch_chars = ["#", "%", "@", "?", "/", "\\"]
        return "".join(
            random.choice(glitch_chars) if random.random() < glitch_chance else char
            for char in text
        )

    @staticmethod
    def draw_box(text: str, width: int = 64) -> None:
        inner = width - 2
        print("+" + "-" * inner + "+")
        print("|" + text.center(inner) + "|")
        print("+" + "-" * inner + "+")

    @staticmethod
    def draw_separator(width: int = 64) -> None:
        print("-" * width)

    @staticmethod
    def progress_bar(value: int, width: int = 24) -> str:
        value = max(0, min(100, value))
        filled = round((value / 100) * width)
        return "#" * filled + "." * (width - filled)

    @staticmethod
    def system_beep() -> None:
        print("\a", end="", flush=True)


class FileSystem:
    def __init__(self) -> None:
        self.root: Dict[str, Any] = {"type": "dir", "name": "/", "files": {}}
        self.current_path: List[str] = []
        self._init_sample_files()

    def _init_sample_files(self) -> None:
        self.root["files"] = {
            "system": {
                "type": "dir",
                "name": "system",
                "files": {
                    "config.sys": {
                        "type": "file",
                        "name": "config.sys",
                        "content": "[System Configuration]\nmode=simulation\nnetwork=virtual",
                    },
                    "boot.log": {
                        "type": "file",
                        "name": "boot.log",
                        "content": "System boot successful",
                    },
                },
            },
            "home": {
                "type": "dir",
                "name": "home",
                "files": {
                    "readme.txt": {
                        "type": "file",
                        "name": "readme.txt",
                        "content": "Welcome to System Simulator Core.",
                    }
                },
            },
        }

    def _split_path(self, path: str) -> List[str]:
        if path in ("", "/"):
            return []
        if path.startswith("/"):
            parts: List[str] = []
        else:
            parts = list(self.current_path)

        for raw_part in path.split("/"):
            part = raw_part.strip()
            if not part or part == ".":
                continue
            if part == "..":
                if parts:
                    parts.pop()
                continue
            parts.append(part)
        return parts

    def _get_dir_by_parts(self, parts: List[str]) -> Optional[Dict[str, Any]]:
        node = self.root
        for part in parts:
            child = node.get("files", {}).get(part)
            if not child or child.get("type") != "dir":
                return None
            node = child
        return node

    def _get_parent_and_name(self, path: str) -> tuple[Optional[Dict[str, Any]], str]:
        parts = self._split_path(path)
        if not parts:
            return None, ""
        return self._get_dir_by_parts(parts[:-1]), parts[-1]

    @staticmethod
    def _path_from_parts(parts: List[str]) -> str:
        return "/" if not parts else "/" + "/".join(parts)

    def get_current_dir(self) -> Dict[str, Any]:
        current = self._get_dir_by_parts(self.current_path)
        if current is None:
            self.current_path = []
            return self.root
        return current

    def pwd(self) -> str:
        return self._path_from_parts(self.current_path)

    def ls(self, path: str = "") -> str:
        directory = self._get_dir_by_parts(self._split_path(path)) if path else self.get_current_dir()
        if directory is None:
            return f"Error: Directory '{path}' not found"
        if not directory["files"]:
            return "(empty directory)"

        output = []
        for name, obj in sorted(directory["files"].items()):
            label = "[DIR] " if obj["type"] == "dir" else "[FILE]"
            suffix = "/" if obj["type"] == "dir" else ""
            output.append(f"{label} {name}{suffix}")
        return "\n".join(output)

    def mkdir(self, path: str) -> str:
        parent, dirname = self._get_parent_and_name(path)
        if parent is None or not dirname:
            return f"Error: Invalid directory path '{path}'"
        if dirname in parent["files"]:
            return f"Error: '{dirname}' already exists"

        parent["files"][dirname] = {"type": "dir", "name": dirname, "files": {}}
        return f"Directory '{dirname}' created"

    def touch(self, path: str) -> str:
        parent, filename = self._get_parent_and_name(path)
        if parent is None or not filename:
            return f"Error: Invalid file path '{path}'"
        if filename in parent["files"]:
            return f"Error: '{filename}' already exists"

        parent["files"][filename] = {"type": "file", "name": filename, "content": ""}
        return f"File '{filename}' created"

    def write(self, path: str, content: str, append: bool = False) -> str:
        parent, filename = self._get_parent_and_name(path)
        if parent is None or not filename:
            return f"Error: Invalid file path '{path}'"

        if filename not in parent["files"]:
            parent["files"][filename] = {"type": "file", "name": filename, "content": ""}

        file_obj = parent["files"][filename]
        if file_obj["type"] != "file":
            return f"Error: '{filename}' is not a file"

        if append and file_obj["content"]:
            file_obj["content"] += "\n" + content
        elif append:
            file_obj["content"] = content
        else:
            file_obj["content"] = content

        action = "Appended to" if append else "Wrote"
        return f"{action} '{filename}'"

    def cd(self, path: str) -> str:
        target_parts = self._split_path(path)
        if self._get_dir_by_parts(target_parts) is None:
            return f"Error: Directory '{path}' not found"
        self.current_path = target_parts
        return f"Changed to {self.pwd()}"

    def cat(self, path: str) -> str:
        parent, filename = self._get_parent_and_name(path)
        if parent is None or filename not in parent["files"]:
            return f"Error: '{path}' not found"
        obj = parent["files"][filename]
        if obj["type"] != "file":
            return f"Error: '{path}' is not a file"
        return obj["content"] if obj["content"] else "(empty file)"

    def rm(self, path: str, admin_mode: bool = False) -> str:
        parent, name = self._get_parent_and_name(path)
        full_path = self._path_from_parts(self._split_path(path))
        if parent is None or name not in parent["files"]:
            return f"Error: '{path}' not found"
        if full_path in PROTECTED_PATHS and not admin_mode:
            return f"Error: '{full_path}' is protected. Use 'sudo unlock' first."

        del parent["files"][name]
        return f"'{name}' removed"

    def tree(self, path: str = "") -> str:
        parts = self._split_path(path) if path else self.current_path
        directory = self._get_dir_by_parts(parts)
        if directory is None:
            return f"Error: Directory '{path}' not found"

        lines = [self._path_from_parts(parts)]

        def walk(node: Dict[str, Any], prefix: str = "") -> None:
            entries = sorted(node["files"].items())
            for index, (name, child) in enumerate(entries):
                last = index == len(entries) - 1
                branch = "`-- " if last else "|-- "
                suffix = "/" if child["type"] == "dir" else ""
                lines.append(prefix + branch + name + suffix)
                if child["type"] == "dir":
                    walk(child, prefix + ("    " if last else "|   "))

        walk(directory)
        return "\n".join(lines)


class SystemState:
    def __init__(self) -> None:
        self.cpu_usage = 15
        self.ram_usage = 32
        self.storage_usage = 45
        self.processes = [
            {"name": "kernel.exe", "status": "running", "cpu": 5},
            {"name": "ui_service.exe", "status": "running", "cpu": 8},
            {"name": "network.sys", "status": "running", "cpu": 2},
        ]
        self.admin_mode = False
        self.system_corrupted = False
        self.corruption_level = 0
        self.start_time = datetime.now()
        self.hostname = "corebox"
        self.user = "operator"
        self.firewall_enabled = True
        self.remote_host: Optional[str] = None
        self.network_hosts = {
            "10.0.0.5": {
                "name": "dev-node",
                "os": "Linux 5.15",
                "ports": [(22, "ssh"), (80, "http"), (8080, "dev-http")],
                "risk": "medium",
            },
            "10.0.0.23": {
                "name": "db-vault",
                "os": "Unix-like",
                "ports": [(22, "ssh"), (5432, "postgres")],
                "risk": "high",
            },
            "192.168.1.10": {
                "name": "printer-lab",
                "os": "Embedded RTOS",
                "ports": [(80, "http"), (9100, "jetdirect")],
                "risk": "low",
            },
        }

    def update_stats(self) -> None:
        process_load = sum(proc["cpu"] for proc in self.processes if proc["status"] == "running")
        corruption_penalty = self.corruption_level // 8 if self.system_corrupted else 0
        self.cpu_usage = max(5, min(99, process_load + random.randint(0, 18) + corruption_penalty))
        self.ram_usage = max(20, min(96, self.ram_usage + random.randint(-4, 7) + corruption_penalty // 2))
        self.storage_usage = max(1, min(99, self.storage_usage + random.randint(0, 1)))

    def get_uptime_seconds(self) -> int:
        return int((datetime.now() - self.start_time).total_seconds())

    def get_uptime_str(self) -> str:
        seconds = self.get_uptime_seconds()
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs}s"


class ProcessManager:
    def __init__(self, system_state: SystemState) -> None:
        self.system_state = system_state

    def ps(self) -> str:
        output = ["PID   NAME                 STATUS       CPU%", "-" * 48]
        for pid, proc in self._process_rows():
            output.append(
                f"{pid:<5} {proc['name'][:20]:<20} {proc['status']:<12} {proc['cpu']:>3}"
            )
        return "\n".join(output)

    def start_process(self, name: str) -> str:
        name = name.strip()
        for index, proc in enumerate(self.system_state.processes):
            if proc["name"].lower() == name.lower():
                proc["status"] = "running"
                return f"Process '{proc['name']}' started (PID: {1000 + index})"

        pid = 1000 + len(self.system_state.processes)
        self.system_state.processes.append(
            {"name": name, "status": "running", "cpu": random.randint(1, 10)}
        )
        return f"Process '{name}' started (PID: {pid})"

    def kill(self, name_or_pid: str, admin_mode: bool = False) -> str:
        target = name_or_pid.strip()
        for index, proc in enumerate(list(self.system_state.processes)):
            pid = 1000 + index
            matches = target == str(pid) or proc["name"].lower() == target.lower()
            if not matches:
                continue
            if proc["name"].lower() in PROTECTED_PROCESSES and not admin_mode:
                return f"Error: '{proc['name']}' is protected. Use 'sudo unlock' first."
            self.system_state.processes.remove(proc)
            return f"Process '{proc['name']}' terminated"
        return f"Error: Process '{target}' not found"

    def _process_rows(self) -> List[tuple[int, Dict[str, Any]]]:
        return [(1000 + index, proc) for index, proc in enumerate(self.system_state.processes)]


class CommandExecutor:
    def __init__(self, fs: FileSystem, system_state: SystemState) -> None:
        self.fs = fs
        self.system_state = system_state
        self.process_manager = ProcessManager(system_state)
        self.event_log: List[tuple[str, str]] = []
        self.command_history: List[str] = []

    def execute(self, command: str) -> str:
        command = command.strip()
        if not command:
            return ""

        self.command_history.append(command)

        try:
            parts = shlex.split(command)
        except ValueError as exc:
            return f"Error: {exc}"

        if not parts:
            return ""

        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == "help":
            return self._help()
        if cmd == "time":
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if cmd == "whoami":
            return self._whoami()
        if cmd == "hostname":
            return self._hostname()
        if cmd == "uname":
            return "SystemSim 2.1 virtual-kernel x86_64 terminal-lab"
        if cmd == "clear":
            UIRenderer.clear_screen()
            return ""
        if cmd == "echo":
            return " ".join(args)
        if cmd == "exit":
            return "EXIT"

        if cmd == "pwd":
            return self.fs.pwd()
        if cmd == "ls":
            return self.fs.ls(args[0] if args else "")
        if cmd == "tree":
            return self.fs.tree(args[0] if args else "")
        if cmd == "mkdir":
            return self._requires_args("mkdir", args) or self.fs.mkdir(args[0])
        if cmd == "touch":
            return self._requires_args("touch", args) or self.fs.touch(args[0])
        if cmd == "write":
            return self._write(args, append=False)
        if cmd == "append":
            return self._write(args, append=True)
        if cmd == "cd":
            return self._requires_args("cd", args) or self.fs.cd(args[0])
        if cmd == "cat":
            return self._requires_args("cat", args) or self.fs.cat(args[0])
        if cmd == "rm":
            return self._requires_args("rm", args) or self.fs.rm(args[0], self.system_state.admin_mode)

        if cmd == "status":
            return self._status()
        if cmd == "ps":
            return self.process_manager.ps()
        if cmd == "uptime":
            return f"System uptime: {self.system_state.get_uptime_str()}"
        if cmd == "log":
            return self._log()
        if cmd == "history":
            return self._history()
        if cmd == "mission":
            return self._mission()

        if cmd == "ping":
            return self._requires_args("ping", args) or self._ping(args[0])
        if cmd == "trace":
            return self._requires_args("trace", args) or self._trace(args[0])
        if cmd == "scan":
            return self._requires_args("scan", args) or self._scan(args[0])
        if cmd == "netstat":
            return self._netstat()
        if cmd == "ssh":
            return self._requires_args("ssh", args) or self._ssh(args[0])
        if cmd == "disconnect":
            return self._disconnect()
        if cmd == "firewall":
            return self._firewall(args)
        if cmd == "hash":
            return self._requires_args("hash", args) or self._hash(" ".join(args))
        if cmd == "encode":
            return self._requires_args("encode", args) or self._encode(" ".join(args))
        if cmd == "decode":
            return self._requires_args("decode", args) or self._decode(" ".join(args))

        if cmd == "start":
            return self._requires_args("start", args) or self.process_manager.start_process(" ".join(args))
        if cmd == "kill":
            return self._requires_args("kill", args) or self.process_manager.kill(
                args[0], self.system_state.admin_mode
            )

        if cmd == "sudo":
            return self._sudo(args)
        if cmd == "ai":
            return self._ai_response(args)
        if cmd == "inject":
            return self._inject(args)
        if cmd == "rebuild":
            return self._rebuild(args)
        if cmd == "save":
            return self._save_state()
        if cmd == "load":
            return self._load_state()

        return f"Error: Unknown command '{cmd}'. Type 'help' for commands."

    @staticmethod
    def _requires_args(command: str, args: List[str]) -> str:
        return "" if args else f"Error: {command} requires an argument"

    def _write(self, args: List[str], append: bool = False) -> str:
        if len(args) < 2:
            command = "append" if append else "write"
            return f"Error: {command} requires a file and text"
        return self.fs.write(args[0], " ".join(args[1:]), append=append)

    def _help(self) -> str:
        return """
+--------------------------------------------------------------+
|                  SYSTEM SIMULATOR COMMANDS                   |
+--------------------------------------------------------------+

SYSTEM:
  help                  Show this help
  time                  Display current time
  whoami                Show current simulated user
  hostname              Show local or remote host name
  uname                 Show simulated kernel info
  status                Show CPU/RAM/storage and security state
  uptime                Show system uptime
  ps                    List running processes
  log                   Show recent system events
  history               Show command history
  mission               Show cyber lab objectives
  clear                 Clear the screen
  exit                  Shutdown simulator

FILES:
  pwd                   Print working directory
  ls [path]             List directory contents
  tree [path]           Show a directory tree
  mkdir <path>          Create directory
  touch <path>          Create empty file
  write <file> <text>   Write text to a file
  append <file> <text>  Append text to a file
  cd <path>             Change directory
  cat <file>            Read file contents
  rm <path>             Remove file or directory

PROCESSES:
  start <process>       Start a process
  kill <name|pid>       Kill a process

NETWORK / CYBER LAB:
  ping <host>           Send simulated ICMP packets
  trace <host>          Show simulated route hops
  scan <host>           Run a fake port scan
  netstat               Show fake active connections
  ssh <host>            Open a simulated remote session
  disconnect            Leave simulated remote session
  firewall status       Show firewall state
  firewall on|off       Toggle firewall (admin only)
  hash <text>           SHA-256 hash text
  encode <text>         Base64 encode text
  decode <text>         Base64 decode text

ADMIN / ADVANCED:
  sudo unlock           Enable admin mode
  sudo lock             Disable admin mode
  ai ask <query>        Ask the simulated AI core
  inject virus          Start corruption simulation
  rebuild core          Repair corruption (admin only)
  save                  Save system state
  load                  Load system state
"""

    def _status(self) -> str:
        self.system_state.update_stats()
        corruption = (
            f"CORRUPTED ({self.system_state.corruption_level}%)"
            if self.system_state.system_corrupted
            else "STABLE"
        )
        return f"""
+--------------------------------------------------------------+
|                     SYSTEM STATUS REPORT                     |
+--------------------------------------------------------------+

CPU USAGE:     [{UIRenderer.progress_bar(self.system_state.cpu_usage)}] {self.system_state.cpu_usage}%
RAM USAGE:     [{UIRenderer.progress_bar(self.system_state.ram_usage)}] {self.system_state.ram_usage}%
STORAGE USED:  [{UIRenderer.progress_bar(self.system_state.storage_usage)}] {self.system_state.storage_usage}%

UPTIME:        {self.system_state.get_uptime_str()}
PROCESSES:     {len(self.system_state.processes)}
ADMIN MODE:    {'ENABLED' if self.system_state.admin_mode else 'DISABLED'}
FIREWALL:      {'ON' if self.system_state.firewall_enabled else 'OFF'}
SESSION:       {self.system_state.remote_host or 'local'}
SYSTEM STATE:  {corruption}
"""

    def _whoami(self) -> str:
        host = self.system_state.remote_host or self.system_state.hostname
        return f"{self.system_state.user}@{host}"

    def _hostname(self) -> str:
        if self.system_state.remote_host:
            host = self.system_state.network_hosts.get(self.system_state.remote_host, {})
            return host.get("name", self.system_state.remote_host)
        return self.system_state.hostname

    def _ping(self, host: str) -> str:
        lines = [f"PING {host} with 32 bytes of data:"]
        known = host in self.system_state.network_hosts or host in ("localhost", "127.0.0.1")
        for _ in range(4):
            if known or random.random() > 0.2:
                lines.append(f"Reply from {host}: bytes=32 time={random.randint(2, 90)}ms TTL={random.randint(48, 64)}")
            else:
                lines.append("Request timed out.")
        return "\n".join(lines)

    def _trace(self, host: str) -> str:
        hops = [
            ("10.0.0.1", "edge-router"),
            ("10.12.4.1", "lab-switch"),
            ("172.16.8.7", "security-gateway"),
            (host, self.system_state.network_hosts.get(host, {}).get("name", "target")),
        ]
        lines = [f"Tracing route to {host}", ""]
        for index, (ip_addr, name) in enumerate(hops, start=1):
            lines.append(f"{index:>2}  {random.randint(1, 80):>3} ms  {ip_addr:<15} {name}")
        return "\n".join(lines)

    def _scan(self, host: str) -> str:
        target = self.system_state.network_hosts.get(host)
        if not target:
            self.event_log.append(("SCAN", f"No response from {host}"))
            return f"Starting simulated scan against {host}\nHost appears down or filtered."

        lines = [
            f"Starting simulated scan against {host} ({target['name']})",
            f"Host OS hint: {target['os']}",
            f"Risk rating: {target['risk']}",
            "",
            "PORT      STATE  SERVICE",
        ]
        for port, service in target["ports"]:
            state = "open" if not self.system_state.firewall_enabled or port in (22, 80, 443) else "filtered"
            lines.append(f"{port:<9} {state:<6} {service}")
        self.event_log.append(("SCAN", f"Port scan completed for {host}"))
        return "\n".join(lines)

    def _netstat(self) -> str:
        connections = [
            ("tcp", "127.0.0.1:4040", "127.0.0.1:0", "LISTEN"),
            ("tcp", "10.0.0.2:51512", "10.0.0.5:22", "ESTABLISHED" if self.system_state.remote_host else "CLOSED"),
            ("udp", "10.0.0.2:5353", "*:*", "LISTEN"),
        ]
        lines = ["Proto  Local Address       Foreign Address     State"]
        for proto, local, foreign, state in connections:
            lines.append(f"{proto:<6} {local:<19} {foreign:<19} {state}")
        return "\n".join(lines)

    def _ssh(self, host: str) -> str:
        if host not in self.system_state.network_hosts:
            return f"ssh: connect to host {host} port 22: No route to host"
        ports = [port for port, _ in self.system_state.network_hosts[host]["ports"]]
        if 22 not in ports:
            return f"ssh: connect to host {host} port 22: Connection refused"
        self.system_state.remote_host = host
        self.event_log.append(("AUTH", f"Simulated SSH session opened to {host}"))
        return f"Connected to {host}. Remote prompt identity: {self._whoami()}"

    def _disconnect(self) -> str:
        if not self.system_state.remote_host:
            return "No remote session active."
        host = self.system_state.remote_host
        self.system_state.remote_host = None
        self.event_log.append(("AUTH", f"Disconnected from {host}"))
        return f"Disconnected from {host}"

    def _firewall(self, args: List[str]) -> str:
        if not args or args[0].lower() == "status":
            return f"Firewall is {'ON' if self.system_state.firewall_enabled else 'OFF'}"
        action = args[0].lower()
        if action not in ("on", "off"):
            return "Error: Use 'firewall status', 'firewall on', or 'firewall off'."
        if not self.system_state.admin_mode:
            return "Error: Admin mode required. Type 'sudo unlock' first."
        self.system_state.firewall_enabled = action == "on"
        self.event_log.append(("SECURITY", f"Firewall turned {action.upper()}"))
        return f"Firewall turned {action.upper()}"

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _encode(self, text: str) -> str:
        return base64.b64encode(text.encode("utf-8")).decode("ascii")

    def _decode(self, text: str) -> str:
        try:
            return base64.b64decode(text.encode("ascii"), validate=True).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return "Error: Input is not valid UTF-8 base64 text"

    def _mission(self) -> str:
        return """
CYBER LAB OBJECTIVES:
  1. Run 'scan 10.0.0.5' and identify open services.
  2. Use 'ssh 10.0.0.5' to open a simulated remote session.
  3. Run 'netstat' and 'log' to inspect activity.
  4. Use 'hash "operator:lab"' and 'encode "incident report"'.
  5. Unlock admin mode, toggle the firewall, then restore it.
  6. Try 'inject virus', inspect 'status', then run 'rebuild core'.
"""

    def _sudo(self, args: List[str]) -> str:
        subcommand = " ".join(args).lower()
        if subcommand == "unlock":
            self.system_state.admin_mode = True
            UIRenderer.system_beep()
            return "ADMIN MODE UNLOCKED\nProtected commands are now available."
        if subcommand == "lock":
            self.system_state.admin_mode = False
            return "Admin mode locked"
        return "Error: Unknown sudo command. Try 'sudo unlock' or 'sudo lock'."

    def _ai_response(self, args: List[str]) -> str:
        if not args or args[0].lower() != "ask" or len(args) < 2:
            return "Error: Use 'ai ask <query>'"

        query = " ".join(args[1:])
        responses = [
            "PROCESSING QUERY...\n[NEURAL NET] Query received\n[ML MODEL] Analyzing context...\nResult: "
            + query[::-1][:40]
            + "...",
            "RUNNING INFERENCE ENGINE\n- Tokenizing input\n- Searching memory map\n- Generating response\nConfidence: "
            + str(random.randint(60, 99))
            + "%",
            "AI CORE ONLINE\nQuery: "
            + query
            + "\nResponse: This simulator is faking just enough intelligence to feel alive.",
        ]
        return random.choice(responses)

    def _inject(self, args: List[str]) -> str:
        if not args or args[0].lower() != "virus":
            return "Error: Unknown injection type. Try 'inject virus'."
        if not self.system_state.admin_mode:
            return "Error: Admin mode required. Type 'sudo unlock' first."

        self.system_state.system_corrupted = True
        lines = ["", "!!! VIRUS DETECTED !!!", "Initiating system corruption...", ""]
        for i in range(5):
            lines.append("  " + UIRenderer.glitch_text("SYSTEM_ERROR", glitch_chance=0.5))
            self.system_state.corruption_level = (i + 1) * 20

        self.event_log.append(("CRITICAL", "Virus injection detected"))
        lines.extend(
            [
                "",
                f"CORRUPTION LEVEL: {self.system_state.corruption_level}%",
                "Type 'rebuild core' to restore system.",
            ]
        )
        return "\n".join(lines)

    def _rebuild(self, args: List[str]) -> str:
        if not args or args[0].lower() != "core":
            return "Error: Unknown rebuild target. Try 'rebuild core'."
        if not self.system_state.admin_mode:
            return "Error: Admin mode required. Type 'sudo unlock' first."
        if not self.system_state.system_corrupted:
            return "Core integrity verified. No rebuild needed."

        self.system_state.system_corrupted = False
        self.system_state.corruption_level = 0
        self.system_state.cpu_usage = max(10, self.system_state.cpu_usage - 20)
        self.system_state.ram_usage = max(20, self.system_state.ram_usage - 10)
        self.event_log.append(("RECOVERY", "Core rebuilt successfully"))
        return "Core rebuilt successfully. System state is STABLE."

    def _log(self) -> str:
        if not self.event_log:
            return "(event log empty)"
        recent = self.event_log[-10:]
        return "\n".join(f"[{level}] {message}" for level, message in recent)

    def _history(self) -> str:
        if not self.command_history:
            return "(history empty)"
        return "\n".join(
            f"{index:>3}: {command}" for index, command in enumerate(self.command_history[-20:], start=1)
        )

    def _save_state(self) -> str:
        state_data = {
            "version": 2,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "fs_root": self.fs.root,
            "fs_path": self.fs.current_path,
            "cpu": self.system_state.cpu_usage,
            "ram": self.system_state.ram_usage,
            "storage": self.system_state.storage_usage,
            "uptime": self.system_state.get_uptime_seconds(),
            "processes": self.system_state.processes,
            "admin_mode": self.system_state.admin_mode,
            "system_corrupted": self.system_state.system_corrupted,
            "corruption_level": self.system_state.corruption_level,
            "event_log": self.event_log[-50:],
            "command_history": self.command_history[-50:],
            "hostname": self.system_state.hostname,
            "user": self.system_state.user,
            "firewall_enabled": self.system_state.firewall_enabled,
            "remote_host": self.system_state.remote_host,
        }

        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as file:
                json.dump(state_data, file, indent=2)
            return f"System state saved to {SAVE_FILE.name}"
        except OSError as exc:
            return f"Error saving state: {exc}"

    def _load_state(self) -> str:
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as file:
                state_data = json.load(file)

            self.fs.root = state_data["fs_root"]
            raw_path = state_data.get("fs_path", [])
            self.fs.current_path = raw_path[1:] if raw_path and raw_path[0] == "root" else raw_path
            if self.fs._get_dir_by_parts(self.fs.current_path) is None:
                self.fs.current_path = []

            self.system_state.cpu_usage = state_data.get("cpu", 15)
            self.system_state.ram_usage = state_data.get("ram", 32)
            self.system_state.storage_usage = state_data.get("storage", 45)
            self.system_state.processes = state_data.get("processes", self.system_state.processes)
            self.system_state.admin_mode = state_data.get("admin_mode", False)
            self.system_state.system_corrupted = state_data.get("system_corrupted", False)
            self.system_state.corruption_level = state_data.get("corruption_level", 0)
            self.system_state.start_time = datetime.now() - timedelta(seconds=state_data.get("uptime", 0))
            self.event_log = [tuple(item) for item in state_data.get("event_log", [])]
            self.command_history = state_data.get("command_history", [])
            self.system_state.hostname = state_data.get("hostname", "corebox")
            self.system_state.user = state_data.get("user", "operator")
            self.system_state.firewall_enabled = state_data.get("firewall_enabled", True)
            self.system_state.remote_host = state_data.get("remote_host")
            return "System state loaded successfully"
        except FileNotFoundError:
            return "Error: No saved state found"
        except (OSError, KeyError, json.JSONDecodeError, TypeError) as exc:
            return f"Error loading state: {exc}"


class EventGenerator:
    def __init__(self, executor: CommandExecutor) -> None:
        self.executor = executor
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._event_loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.running = False

    def _event_loop(self) -> None:
        while self.running:
            time.sleep(random.randint(20, 40))
            if not self.running:
                break

            event = random.choice(self._get_random_events())
            print(f"\n[SYSTEM EVENT] {event}")
            self.executor.event_log.append(("EVENT", event))

    @staticmethod
    def _get_random_events() -> List[str]:
        return [
            "Memory spike detected (87%)",
            "Background process started: update_service.exe",
            "Unknown packet received from 192.168.1.X",
            "IDS notice: repeated login attempts on dev-node",
            "Firewall rule matched: drop inbound tcp/4444",
            "SSH key audit completed for operator",
            "Disk I/O increased by 25%",
            "Network latency spike: 250ms",
            "Security scan initiated",
            "Power fluctuation detected",
            "Connecting to remote server...",
            "Cache cleared (freed 256MB)",
            "Database optimization running",
        ]


class SystemSimulator:
    def __init__(self) -> None:
        self.fs = FileSystem()
        self.system_state = SystemState()
        self.executor = CommandExecutor(self.fs, self.system_state)
        self.event_generator = EventGenerator(self.executor)
        self.running = True

    def boot_sequence(self) -> None:
        UIRenderer.clear_screen()
        UIRenderer.draw_box("SYSTEM SIMULATOR CORE v2.0")
        print()
        UIRenderer.typing_effect("INITIATING BOOT SEQUENCE...", delay=0.02)
        time.sleep(0.25)

        boot_steps = [
            "Loading kernel...",
            "Initializing virtual hardware...",
            "Starting services...",
            "Mounting file system...",
            "Checking memory...",
            "Starting network stack...",
        ]
        for step in boot_steps:
            print(f"  [OK] {step}")
            time.sleep(0.15)

        print()
        UIRenderer.typing_effect("SYSTEM READY", delay=0.03)
        print()
        UIRenderer.draw_separator()
        print("Type 'help' for commands. Type 'exit' to shutdown.")
        UIRenderer.draw_separator()
        print()

    def run(self) -> None:
        self.boot_sequence()
        self.event_generator.start()

        try:
            while self.running:
                try:
                    user_input = input(f"[{self.fs.pwd()}] > ").strip()
                    result = self.executor.execute(user_input)
                    if result == "EXIT":
                        self.shutdown()
                        break
                    if result:
                        print(result)
                except KeyboardInterrupt:
                    print("\n\nReceived interrupt signal... shutting down...")
                    self.shutdown()
                    break
        except EOFError:
            self.shutdown()

    def shutdown(self) -> None:
        print()
        UIRenderer.typing_effect("INITIATING SHUTDOWN...", delay=0.02)
        for step in ["Stopping services...", "Flushing buffers...", "Unmounting file system...", "Powering down..."]:
            print(f"  [OK] {step}")
            time.sleep(0.12)

        print()
        UIRenderer.draw_box("SYSTEM OFFLINE")
        print()
        self.running = False
        self.event_generator.stop()


if __name__ == "__main__":
    SystemSimulator().run()
