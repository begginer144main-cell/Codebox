# System Simulator Workflows

## Build A Project Folder

```text
mkdir projects
cd projects
mkdir webapp
cd webapp
mkdir src
write README.md "Fake project running inside the simulator."
write src/main.py "print('hello')"
tree
save
```

## Explore The Starting System

```text
pwd
tree /
cd /system
ls
cat config.sys
cat boot.log
cd /home
cat readme.txt
```

## Simulate A Busy Machine

```text
status
ps
start database.exe
start webserver.exe
start backup.exe
ps
status
kill backup.exe
log
```

## Try Protected Operations

```text
kill kernel.exe
sudo unlock
kill kernel.exe
sudo lock
```

The kernel process is protected until admin mode is enabled.

## Corrupt And Recover

```text
sudo unlock
inject virus
status
log
rebuild core
status
sudo lock
```

## Save And Restore

```text
mkdir data
write data/notes.txt "Persistent simulator data"
start worker.exe
save
exit
```

Later:

```text
load
tree
ps
cat data/notes.txt
```

## Text File Workflow

```text
mkdir journal
write journal/day1.txt "Booted the simulator."
append journal/day1.txt "Created a few files."
cat journal/day1.txt
```

## AI Core

```text
ai ask what is a command shell
ai ask explain process management
```

The AI command is intentionally simulated. It gives playful terminal-flavored responses without using external services.

## Cyber Lab Recon

```text
mission
whoami
hostname
uname
scan 10.0.0.5
trace 10.0.0.5
ping 10.0.0.5
ssh 10.0.0.5
netstat
log
disconnect
```

## Firewall Drill

```text
firewall status
sudo unlock
firewall off
scan 10.0.0.23
firewall on
sudo lock
```

## Encoding And Hashing

```text
hash "operator:lab"
encode "incident report"
decode aW5jaWRlbnQgcmVwb3J0
```

## More Ideas To Build Next

- `tail <file>` for log-following flavor
- `grep <text> <file>` for terminal search
- `alias <name> <command>` for shell customization
- `nmap` as an alias for `scan` inside the fake lab
- `crack <hash>` as a cinematic fake password audit
- `users`, `passwd`, and `su` for multi-user simulation
- `jobs`, `fg`, and `bg` for richer process control
- `alerts` dashboard for security incidents
- Story missions with scores and completion states
