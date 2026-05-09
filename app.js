const terminal = document.querySelector("#terminal");
const form = document.querySelector("#commandForm");
const input = document.querySelector("#commandInput");
const promptEl = document.querySelector("#prompt");
const titleEl = document.querySelector(".title");
const adminEl = document.querySelector("#statusAdmin");
const firewallEl = document.querySelector("#statusFirewall");
const sessionEl = document.querySelector("#statusSession");
const threatEl = document.querySelector("#threatBadge");
const missionList = document.querySelector("#missionList");
const missionCount = document.querySelector("#missionCount");
const canvas = document.querySelector("#networkCanvas");
const ctx = canvas.getContext("2d");

const STORAGE_KEY = "corebox-terminal-lab-save";

const initialFs = () => ({
  type: "dir",
  files: {
    home: {
      type: "dir",
      files: {
        "readme.txt": {
          type: "file",
          content: "Welcome to CoreBox Terminal Lab. Type mission to begin."
        }
      }
    },
    system: {
      type: "dir",
      files: {
        "boot.log": { type: "file", content: "Boot sequence complete. Network lab armed." },
        "config.sys": { type: "file", content: "mode=simulation\nnetwork=lab\nfirewall=enabled" }
      }
    },
    var: {
      type: "dir",
      files: {
        log: {
          type: "dir",
          files: {
            "auth.log": { type: "file", content: "Accepted publickey for operator from 10.0.0.2\nFailed password for guest from 10.0.0.5" },
            "ids.log": { type: "file", content: "IDS ready. No live systems are contacted by this simulator." }
          }
        }
      }
    }
  }
});

const hosts = {
  "10.0.0.5": { name: "dev-node", os: "Linux 5.15", risk: "medium", ports: [[22, "ssh"], [80, "http"], [8080, "dev-http"]], x: 314, y: 88 },
  "10.0.0.23": { name: "db-vault", os: "Unix-like", risk: "high", ports: [[22, "ssh"], [5432, "postgres"]], x: 312, y: 180 },
  "192.168.1.10": { name: "printer-lab", os: "Embedded RTOS", risk: "low", ports: [[80, "http"], [9100, "jetdirect"]], x: 104, y: 186 }
};

const missionItems = [
  ["scan", "Scan 10.0.0.5"],
  ["ssh", "Open a simulated SSH session"],
  ["netstat", "Inspect network connections"],
  ["hash", "Hash a credential string"],
  ["firewall", "Toggle the firewall"],
  ["rebuild", "Corrupt and rebuild the core"]
];

let state = freshState();
let history = [];
let historyIndex = 0;
let booted = false;

function freshState() {
  return {
    fs: initialFs(),
    cwd: [],
    user: "operator",
    hostname: "corebox",
    admin: false,
    firewall: true,
    corrupted: false,
    corruption: 0,
    remote: null,
    processes: [
      { name: "kernel.exe", cpu: 5 },
      { name: "ui_service.exe", cpu: 8 },
      { name: "network.sys", cpu: 2 }
    ],
    log: [],
    mission: {},
    startedAt: Date.now()
  };
}

function print(text = "", type = "system") {
  const line = document.createElement("div");
  line.className = `line ${type}`;
  line.textContent = text;
  terminal.appendChild(line);
  terminal.scrollTop = terminal.scrollHeight;
}

function printBlock(text, type = "system") {
  String(text).split("\n").forEach((line) => print(line, type));
}

function cwdPath(parts = state.cwd) {
  return parts.length ? `/${parts.join("/")}` : "/";
}

function updatePrompt() {
  const host = state.remote || state.hostname;
  promptEl.textContent = `[${cwdPath()}] >`;
  titleEl.textContent = `${state.user}@${host}:${cwdPath()}`;
  adminEl.textContent = `ADMIN: ${state.admin ? "ON" : "OFF"}`;
  firewallEl.textContent = `FW: ${state.firewall ? "ON" : "OFF"}`;
  sessionEl.textContent = `SESSION: ${state.remote || "LOCAL"}`;
  threatEl.textContent = state.corrupted ? `CORRUPT ${state.corruption}%` : "STABLE";
  renderMissions();
}

function renderMissions() {
  missionList.innerHTML = "";
  let done = 0;
  missionItems.forEach(([key, label]) => {
    const li = document.createElement("li");
    li.textContent = label;
    if (state.mission[key]) {
      li.className = "done";
      done += 1;
    }
    missionList.appendChild(li);
  });
  missionCount.textContent = `${done}/${missionItems.length}`;
}

function parseCommand(inputText) {
  const matches = inputText.match(/(?:[^\s"]+|"[^"]*")+/g) || [];
  return matches.map((part) => part.startsWith('"') && part.endsWith('"') ? part.slice(1, -1) : part);
}

function splitPath(path) {
  let parts = path.startsWith("/") ? [] : [...state.cwd];
  path.split("/").forEach((part) => {
    if (!part || part === ".") return;
    if (part === "..") parts.pop();
    else parts.push(part);
  });
  return parts;
}

function getDir(parts = state.cwd) {
  let node = state.fs;
  for (const part of parts) {
    node = node.files?.[part];
    if (!node || node.type !== "dir") return null;
  }
  return node;
}

function parentAndName(path) {
  const parts = splitPath(path);
  if (!parts.length) return [null, ""];
  return [getDir(parts.slice(0, -1)), parts[parts.length - 1]];
}

function listDir(path = "") {
  const dir = path ? getDir(splitPath(path)) : getDir();
  if (!dir) return `Error: Directory '${path}' not found`;
  const names = Object.keys(dir.files).sort();
  if (!names.length) return "(empty directory)";
  return names.map((name) => `${dir.files[name].type === "dir" ? "[DIR] " : "[FILE]"} ${name}${dir.files[name].type === "dir" ? "/" : ""}`).join("\n");
}

function tree(path = "") {
  const parts = path ? splitPath(path) : state.cwd;
  const dir = getDir(parts);
  if (!dir) return `Error: Directory '${path}' not found`;
  const lines = [cwdPath(parts)];
  const walk = (node, prefix = "") => {
    const entries = Object.entries(node.files).sort(([a], [b]) => a.localeCompare(b));
    entries.forEach(([name, child], index) => {
      const last = index === entries.length - 1;
      lines.push(`${prefix}${last ? "`--" : "|--"} ${name}${child.type === "dir" ? "/" : ""}`);
      if (child.type === "dir") walk(child, prefix + (last ? "    " : "|   "));
    });
  };
  walk(dir);
  return lines.join("\n");
}

async function sha256(text) {
  const data = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function encode64(text) {
  return btoa(unescape(encodeURIComponent(text)));
}

function decode64(text) {
  try {
    return decodeURIComponent(escape(atob(text)));
  } catch {
    return "Error: Input is not valid base64 text";
  }
}

function addLog(level, message) {
  state.log.push(`[${level}] ${message}`);
  state.log = state.log.slice(-50);
}

function saveLocal() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  return "Game saved to browser storage.";
}

function loadLocal() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return "No browser save found.";
  state = JSON.parse(raw);
  updatePrompt();
  return "Game loaded from browser storage.";
}

function missionText() {
  return `CYBER LAB OBJECTIVES\n  1. scan 10.0.0.5\n  2. ssh 10.0.0.5\n  3. netstat\n  4. hash "operator:lab"\n  5. sudo unlock, firewall off, firewall on\n  6. inject virus, status, rebuild core`;
}

async function execute(raw) {
  const parts = parseCommand(raw);
  const cmd = (parts[0] || "").toLowerCase();
  const args = parts.slice(1);
  if (!cmd) return "";

  switch (cmd) {
    case "help":
      return `SYSTEM\n  help time whoami hostname uname status uptime ps log history mission clear\nFILES\n  pwd ls tree cd mkdir touch write append cat rm\nCYBER LAB\n  ping trace scan netstat ssh disconnect firewall hash encode decode\nADMIN\n  sudo unlock | sudo lock | inject virus | rebuild core | save | load | reset`;
    case "time": return new Date().toLocaleString();
    case "whoami": return `${state.user}@${state.remote || state.hostname}`;
    case "hostname": return state.remote ? hosts[state.remote]?.name || state.remote : state.hostname;
    case "uname": return "CoreBox WebOS 1.0 virtual-kernel wasm-free x86_64";
    case "clear": terminal.innerHTML = ""; return "";
    case "pwd": return cwdPath();
    case "ls": return listDir(args[0] || "");
    case "tree": return tree(args[0] || "");
    case "cd": {
      if (!args[0]) return "Error: cd requires a path";
      const parts = splitPath(args[0]);
      if (!getDir(parts)) return `Error: Directory '${args[0]}' not found`;
      state.cwd = parts;
      updatePrompt();
      return `Changed to ${cwdPath()}`;
    }
    case "mkdir": {
      if (!args[0]) return "Error: mkdir requires a path";
      const [parent, name] = parentAndName(args[0]);
      if (!parent || !name) return "Error: Invalid path";
      if (parent.files[name]) return `Error: '${name}' already exists`;
      parent.files[name] = { type: "dir", files: {} };
      return `Directory '${name}' created`;
    }
    case "touch": {
      if (!args[0]) return "Error: touch requires a file";
      const [parent, name] = parentAndName(args[0]);
      if (!parent || !name) return "Error: Invalid path";
      if (parent.files[name]) return `Error: '${name}' already exists`;
      parent.files[name] = { type: "file", content: "" };
      return `File '${name}' created`;
    }
    case "write":
    case "append": {
      if (args.length < 2) return `Error: ${cmd} requires a file and text`;
      const [parent, name] = parentAndName(args[0]);
      if (!parent || !name) return "Error: Invalid path";
      if (!parent.files[name]) parent.files[name] = { type: "file", content: "" };
      if (parent.files[name].type !== "file") return `Error: '${name}' is not a file`;
      parent.files[name].content = cmd === "append" && parent.files[name].content ? `${parent.files[name].content}\n${args.slice(1).join(" ")}` : args.slice(1).join(" ");
      return `${cmd === "append" ? "Appended to" : "Wrote"} '${name}'`;
    }
    case "cat": {
      if (!args[0]) return "Error: cat requires a file";
      const [parent, name] = parentAndName(args[0]);
      const file = parent?.files?.[name];
      if (!file) return `Error: '${args[0]}' not found`;
      if (file.type !== "file") return `Error: '${args[0]}' is not a file`;
      return file.content || "(empty file)";
    }
    case "rm": {
      if (!args[0]) return "Error: rm requires a path";
      if (args[0] === "/system" && !state.admin) return "Error: '/system' is protected. Use sudo unlock first.";
      const [parent, name] = parentAndName(args[0]);
      if (!parent?.files?.[name]) return `Error: '${args[0]}' not found`;
      delete parent.files[name];
      return `'${name}' removed`;
    }
    case "status": {
      const cpu = Math.min(99, state.processes.reduce((sum, proc) => sum + proc.cpu, 0) + Math.floor(Math.random() * 22) + Math.floor(state.corruption / 8));
      const ram = Math.min(96, 30 + state.processes.length * 4 + Math.floor(state.corruption / 5));
      return `CPU: ${cpu}%\nRAM: ${ram}%\nPROCESSES: ${state.processes.length}\nADMIN: ${state.admin ? "ON" : "OFF"}\nFIREWALL: ${state.firewall ? "ON" : "OFF"}\nSESSION: ${state.remote || "local"}\nCORE: ${state.corrupted ? `CORRUPTED ${state.corruption}%` : "STABLE"}`;
    }
    case "uptime": return `${Math.floor((Date.now() - state.startedAt) / 1000)} seconds`;
    case "ps": return ["PID   NAME                 CPU%", "-----------------------------", ...state.processes.map((p, i) => `${1000 + i}  ${p.name.padEnd(20)} ${p.cpu}`)].join("\n");
    case "log": return state.log.length ? state.log.join("\n") : "(event log empty)";
    case "history": return history.map((item, i) => `${String(i + 1).padStart(3)}: ${item}`).join("\n") || "(history empty)";
    case "mission": return missionText();
    case "ping": {
      if (!args[0]) return "Error: ping requires a host";
      state.mission.scan = state.mission.scan || args[0] === "10.0.0.5";
      return [`PING ${args[0]} with 32 bytes of data:`, ...[1, 2, 3, 4].map(() => `Reply from ${args[0]}: bytes=32 time=${Math.floor(Math.random() * 80) + 2}ms TTL=64`)].join("\n");
    }
    case "trace": {
      if (!args[0]) return "Error: trace requires a host";
      return `Tracing route to ${args[0]}\n 1   4 ms  10.0.0.1        edge-router\n 2  18 ms  10.12.4.1       lab-switch\n 3  31 ms  172.16.8.7      security-gateway\n 4  44 ms  ${args[0]}      ${hosts[args[0]]?.name || "target"}`;
    }
    case "scan": {
      if (!args[0]) return "Error: scan requires a host";
      const target = hosts[args[0]];
      addLog("SCAN", `Port scan completed for ${args[0]}`);
      if (args[0] === "10.0.0.5") state.mission.scan = true;
      if (!target) return `Starting simulated scan against ${args[0]}\nHost appears down or filtered.`;
      return [`Starting simulated scan against ${args[0]} (${target.name})`, `Host OS hint: ${target.os}`, `Risk rating: ${target.risk}`, "", "PORT      STATE    SERVICE", ...target.ports.map(([port, service]) => `${String(port).padEnd(9)} ${(state.firewall && ![22, 80, 443].includes(port) ? "filtered" : "open").padEnd(8)} ${service}`)].join("\n");
    }
    case "netstat":
      state.mission.netstat = true;
      return `Proto  Local Address       Foreign Address     State\ntcp    127.0.0.1:4040      127.0.0.1:0         LISTEN\ntcp    10.0.0.2:51512      10.0.0.5:22        ${state.remote ? "ESTABLISHED" : "CLOSED"}\nudp    10.0.0.2:5353       *:*                 LISTEN`;
    case "ssh": {
      if (!args[0]) return "Error: ssh requires a host";
      const target = hosts[args[0]];
      if (!target) return `ssh: connect to host ${args[0]} port 22: No route to host`;
      if (!target.ports.some(([port]) => port === 22)) return `ssh: connect to host ${args[0]} port 22: Connection refused`;
      state.remote = args[0];
      state.mission.ssh = true;
      addLog("AUTH", `Simulated SSH session opened to ${args[0]}`);
      updatePrompt();
      return `Connected to ${args[0]}. Identity: ${state.user}@${args[0]}`;
    }
    case "disconnect": {
      if (!state.remote) return "No remote session active.";
      const old = state.remote;
      state.remote = null;
      addLog("AUTH", `Disconnected from ${old}`);
      updatePrompt();
      return `Disconnected from ${old}`;
    }
    case "firewall": {
      const action = (args[0] || "status").toLowerCase();
      if (action === "status") return `Firewall is ${state.firewall ? "ON" : "OFF"}`;
      if (!["on", "off"].includes(action)) return "Error: Use firewall status, firewall on, or firewall off.";
      if (!state.admin) return "Error: Admin mode required. Type sudo unlock first.";
      state.firewall = action === "on";
      state.mission.firewall = true;
      addLog("SECURITY", `Firewall turned ${action.toUpperCase()}`);
      updatePrompt();
      return `Firewall turned ${action.toUpperCase()}`;
    }
    case "hash":
      if (!args.length) return "Error: hash requires text";
      state.mission.hash = true;
      return sha256(args.join(" "));
    case "encode": return args.length ? encode64(args.join(" ")) : "Error: encode requires text";
    case "decode": return args.length ? decode64(args.join(" ")) : "Error: decode requires base64 text";
    case "sudo":
      if (args.join(" ").toLowerCase() === "unlock") { state.admin = true; updatePrompt(); return "ADMIN MODE UNLOCKED"; }
      if (args.join(" ").toLowerCase() === "lock") { state.admin = false; updatePrompt(); return "Admin mode locked"; }
      return "Error: Unknown sudo command.";
    case "inject":
      if ((args[0] || "").toLowerCase() !== "virus") return "Error: Unknown injection type. Try inject virus.";
      if (!state.admin) return "Error: Admin mode required. Type sudo unlock first.";
      state.corrupted = true;
      state.corruption = 100;
      addLog("CRITICAL", "Virus injection detected");
      updatePrompt();
      return "!!! VIRUS DETECTED !!!\nSYSTEM_ERROR\nSYST?M_ERR@R\nCORRUPTION LEVEL: 100%\nType rebuild core to restore system.";
    case "rebuild":
      if ((args[0] || "").toLowerCase() !== "core") return "Error: Unknown rebuild target. Try rebuild core.";
      if (!state.admin) return "Error: Admin mode required. Type sudo unlock first.";
      state.corrupted = false;
      state.corruption = 0;
      state.mission.rebuild = true;
      addLog("RECOVERY", "Core rebuilt successfully");
      updatePrompt();
      return "Core rebuilt successfully. System state is STABLE.";
    case "save": return saveLocal();
    case "load": return loadLocal();
    case "reset": state = freshState(); updatePrompt(); return "Simulation reset.";
    case "start":
      if (!args.length) return "Error: start requires a process";
      state.processes.push({ name: args.join(" "), cpu: Math.floor(Math.random() * 8) + 1 });
      return `Process '${args.join(" ")}' started (PID: ${999 + state.processes.length})`;
    case "kill":
      if (!args.length) return "Error: kill requires a name or PID";
      return killProcess(args[0]);
    case "ai":
      if ((args[0] || "").toLowerCase() !== "ask" || args.length < 2) return "Error: Use ai ask <query>";
      return `AI CORE ONLINE\nQuery: ${args.slice(1).join(" ")}\nResponse: Simulated intelligence confirms the terminal is operational.`;
    default: return `Error: Unknown command '${cmd}'. Type help for commands.`;
  }
}

function killProcess(target) {
  const index = state.processes.findIndex((proc, i) => proc.name.toLowerCase() === target.toLowerCase() || String(1000 + i) === target);
  if (index < 0) return `Error: Process '${target}' not found`;
  if (state.processes[index].name === "kernel.exe" && !state.admin) return "Error: kernel.exe is protected. Use sudo unlock first.";
  const [proc] = state.processes.splice(index, 1);
  return `Process '${proc.name}' terminated`;
}

async function runCommand(command) {
  print(`${promptEl.textContent} ${command}`, "command");
  history.push(command);
  historyIndex = history.length;
  const output = await execute(command);
  if (output) printBlock(output, state.corrupted ? "danger" : "system");
  updatePrompt();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const command = input.value.trim();
  input.value = "";
  if (command) await runCommand(command);
});

input.addEventListener("keydown", (event) => {
  if (event.key === "ArrowUp") {
    event.preventDefault();
    historyIndex = Math.max(0, historyIndex - 1);
    input.value = history[historyIndex] || "";
  }
  if (event.key === "ArrowDown") {
    event.preventDefault();
    historyIndex = Math.min(history.length, historyIndex + 1);
    input.value = history[historyIndex] || "";
  }
});

document.querySelectorAll("[data-command]").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.command;
    input.focus();
  });
});

function drawNetwork() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#090d10";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "#26343c";
  ctx.lineWidth = 1;
  for (let x = 20; x < canvas.width; x += 32) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, canvas.height);
    ctx.stroke();
  }
  for (let y = 20; y < canvas.height; y += 32) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(canvas.width, y);
    ctx.stroke();
  }

  const core = { x: 208, y: 132, name: "corebox" };
  Object.entries(hosts).forEach(([ip, host]) => {
    ctx.strokeStyle = state.remote === ip ? "#51e58a" : "#38505c";
    ctx.beginPath();
    ctx.moveTo(core.x, core.y);
    ctx.lineTo(host.x, host.y);
    ctx.stroke();
    drawNode(host.x, host.y, host.name, ip, state.remote === ip ? "#51e58a" : "#66d9ef");
  });
  drawNode(core.x, core.y, core.name, "local", state.corrupted ? "#ff6b6b" : "#f2c36b");
  requestAnimationFrame(drawNetwork);
}

function drawNode(x, y, label, sub, color) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, 8, 0, Math.PI * 2);
  ctx.fill();
  ctx.font = "12px Cascadia Mono, Consolas, monospace";
  ctx.fillStyle = "#d8f3e4";
  ctx.fillText(label, x + 12, y - 2);
  ctx.fillStyle = "#8aa29a";
  ctx.fillText(sub, x + 12, y + 13);
}

function boot() {
  if (booted) return;
  booted = true;
  updatePrompt();
  printBlock("COREBOX WEB TERMINAL v1.0\nBoot sequence complete. Type help or mission.");
  drawNetwork();
}

setInterval(() => {
  const events = [
    "IDS notice: repeated login attempts on dev-node",
    "Firewall rule matched: drop inbound tcp/4444",
    "Cache sweep completed",
    "Synthetic packet capture rotated",
    "Operator session heartbeat acknowledged"
  ];
  const event = events[Math.floor(Math.random() * events.length)];
  addLog("EVENT", event);
}, 18000);

boot();
