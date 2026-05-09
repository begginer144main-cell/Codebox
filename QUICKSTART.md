# Quick Start

Browser version:

```text
Open index.html
```

Python version:

```bash
python system_simulator.py
```

You should see a boot sequence, then:

```text
[/] >
```

## First Commands To Try

```text
help
status
whoami
uname
mission
ls
tree
cd home
cat readme.txt
cd /
mkdir lab
cd lab
write notes.txt "Hello from the simulator"
cat notes.txt
save
exit
```

## Common Commands

| Goal | Command |
| --- | --- |
| Show help | `help` |
| Show current path | `pwd` |
| List files | `ls` |
| Show directory tree | `tree` |
| Create directory | `mkdir name` |
| Create file | `touch file.txt` |
| Write file text | `write file.txt "some text"` |
| Append file text | `append file.txt "more text"` |
| Read file | `cat file.txt` |
| Change directory | `cd path` |
| Remove item | `rm path` |
| Show system status | `status` |
| Show identity | `whoami` |
| Show kernel info | `uname` |
| Show lab mission | `mission` |
| Ping fake host | `ping 10.0.0.5` |
| Scan fake host | `scan 10.0.0.5` |
| Simulated SSH | `ssh 10.0.0.5` |
| Leave remote session | `disconnect` |
| Firewall state | `firewall status` |
| Hash text | `hash "hello"` |
| Encode text | `encode "hello"` |
| Decode text | `decode aGVsbG8=` |
| Show processes | `ps` |
| Start process | `start worker.exe` |
| Kill process | `kill worker.exe` |
| Enable admin | `sudo unlock` |
| Disable admin | `sudo lock` |
| Ask AI core | `ai ask what is a shell` |
| Simulate virus | `inject virus` |
| Repair virus | `rebuild core` |
| Save state | `save` |
| Load state | `load` |
| Exit | `exit` |

## Cyber Lab Flow

```text
mission
scan 10.0.0.5
ping 10.0.0.5
ssh 10.0.0.5
whoami
netstat
disconnect
hash "operator:lab"
encode "incident report"
```

## Admin Flow

```text
sudo unlock
inject virus
status
rebuild core
sudo lock
```

## Notes

- Paths can be relative, like `cd home`, or absolute, like `cd /home`.
- Quoted text works: `write notes.txt "hello world"`.
- `system_state.json` is updated when you run `save`.

## Publish To Netlify

Push the project to GitHub, import it in Netlify, leave the build command empty, and publish the repository root.
