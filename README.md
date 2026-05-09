# CoreBox Terminal Lab

A publishable terminal-style cyber lab game. The repo includes a browser version for GitHub/Netlify and the original Python terminal simulator. Everything is simulated: fake files, fake processes, fake hosts, fake scans, missions, admin mode, save/load, and a reversible corruption event.

## Play In Browser

Open `index.html` in a browser. No build step is required.

For Netlify, publish the repository root. Leave the build command empty and set the publish directory to `/`.

## Run The Python Version

```bash
python system_simulator.py
```

Both versions use the same simulated terminal concept. Type `help` or `mission` inside the game to begin.

## Features

### Shell Commands

```text
help                  Show command reference
time                  Display current time
clear                 Clear the terminal
echo <text>           Print text
exit                  Shutdown simulator
history               Show recent commands
```

### File System

The fake file system supports relative and absolute paths.

```text
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
```

Example:

```text
[/] > mkdir projects
Directory 'projects' created

[/] > cd projects
Changed to /projects

[/projects] > write notes.txt "Build a tiny OS"
Wrote 'notes.txt'

[/projects] > cat notes.txt
Build a tiny OS
```

### System Monitoring

```text
status                Show CPU, RAM, storage, admin mode, firewall, session state
uptime                Show session uptime
ps                    List fake running processes
log                   Show recent system events
history               Show recent commands
mission               Show cyber lab objectives
whoami                Show current simulated identity
hostname              Show local or remote host name
uname                 Show simulated kernel info
```

### Process Management

```text
start <process>       Start a process
kill <name|pid>       Kill a process by name or PID
```

`kernel.exe` is protected unless admin mode is enabled.

### Cyber Lab Commands

These commands are fully simulated. They do not scan or connect to real machines.

```text
ping <host>           Simulate ICMP replies
trace <host>          Simulate route hops
scan <host>           Fake port scan against lab hosts
netstat               Show fake local connections
ssh <host>            Open a simulated remote session
disconnect            Close simulated remote session
firewall status       Show firewall state
firewall on|off       Toggle firewall, admin only
hash <text>           SHA-256 hash text
encode <text>         Base64 encode text
decode <text>         Base64 decode text
```

Built-in lab hosts:

```text
10.0.0.5        dev-node
10.0.0.23       db-vault
192.168.1.10    printer-lab
```

### Admin And Advanced Commands

```text
sudo unlock           Enable admin mode
sudo lock             Disable admin mode
ai ask <query>        Ask the simulated AI core
inject virus          Start corruption simulation, admin only
rebuild core          Repair corruption, admin only
save                  Save state to system_state.json
load                  Load state from system_state.json
```

Saved state includes:

- File system
- Current directory
- CPU/RAM/storage values
- Processes
- Admin mode
- Firewall state
- Remote session state
- Corruption state
- Recent event log
- Recent command history

## Initial File System

```text
/
|-- home/
|   `-- readme.txt
`-- system/
    |-- boot.log
    `-- config.sys
```

## Project Files

- `index.html` - Browser game entry point
- `styles.css` - Terminal UI and responsive layout
- `app.js` - Browser game logic
- `system_simulator.py` - Python terminal version
- `system_state.json` - Python save-state example
- `QUICKSTART.md` - Fast usage guide
- `WORKFLOWS.md` - Example playthroughs and expansion ideas

## Netlify Deploy

1. Push this folder to a GitHub repo.
2. In Netlify, choose Add new site, then Import from GitHub.
3. Select the repo.
4. Build command: leave blank.
5. Publish directory: `/`.
6. Deploy.

The browser game saves progress in `localStorage`.

## Good Next Ideas

- Add users and permissions
- Add fake networking commands like `ping` and `trace`
- Add a package manager simulation
- Add command aliases
- Add tests with `unittest`
- Split the single file into modules once the project grows
