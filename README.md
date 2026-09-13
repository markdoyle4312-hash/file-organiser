# File Organiser

Organises a downloads folder into a clean, searchable archive by type, date and project. Python core with a Bash wrapper; no dependencies required.

## What it does

- **By type** — images, documents, videos, audio, code, archives, spreadsheets, presentations and more (40+ extensions, extensible via config).
- **By date** — a `YYYY/YYYY-MM/` structure, using a date in the filename when present (e.g. `2024-03-15`, `20240315`, `03-15-2024`) and falling back to the file's modification time.
- **By project** — detects projects from configurable filename keywords (`invoice-…` → `Tax-2024`).
- **Combined** — the default `all` mode produces `Projects/<Project>/<Type>/YYYY/YYYY-MM/`.

### Result structure

```
~/Organized/
├── Images/2024/2024-03/
├── Documents/2024/2024-02/
├── Videos/2023/2023-12/
├── Code/2024/2024-01/
├── Projects/
│   ├── Website-Redesign/
│   │   ├── Code/2024/2024-03/
│   │   └── Images/2024/2024-03/
│   ├── Tax-2024/Documents/2024/2024-01/
│   └── _Unsorted/            ← files that match no project keyword
└── _logs/
    └── organize_2024-03-15_09-00-00.log
```

## Quick start

```bash
chmod +x organize.sh organizer.py
./organize.sh --dry-run --verbose   # preview first
./organize.sh                       # organise for real
./organize.sh --setup-cron          # optional: run weekly (Mondays 9am)
```

### Python only

```bash
python3 organizer.py --source ~/Downloads --dest ~/Organized --dry-run
python3 organizer.py --by project --copy --verbose
python3 organizer.py --source ./my-mess --dest ./clean --limit 100
```

## Options

| Flag | Description |
|------|-------------|
| `-s, --source PATH` | Source folder (default: `~/Downloads`) |
| `-d, --dest PATH` | Destination folder (default: `~/Organized`) |
| `--config PATH` | Config file for projects & custom types (default: `config.yaml`) |
| `-m, --by MODE` | `type`, `date`, `project` or `all` (default) |
| `-n, --dry-run` | Preview — nothing is moved or created |
| `-c, --copy` | Copy files instead of moving them |
| `-r, --recursive` | Scan subfolders recursively |
| `-v, --verbose` | Show every file and its destination |
| `--limit N` | Process only the first N files |
| `--include-hidden` | Include hidden files and folders |
| `--setup-cron` | Install a weekly cron job (Mondays 9am) |
| `--install` | Check dependencies and set execute permissions |
| `-h, --help` | Show help |

## Configuration

Edit `config.yaml` to add your own projects. Keywords are matched case-insensitively against filenames:

```yaml
projects:
  MyStartup:
    - startup
    - pitchdeck
    - investor
  Holiday-Japan:
    - japan
    - tokyo
    - itinerary
```

Custom file-type categories:

```yaml
file_types:
  3D-Models: [.blend, .fbx, .obj, .stl]
  Ebooks: [.epub, .mobi, .azw3]
```

The bundled config is parsed by a built-in YAML parser, so the tool works with no dependencies. Installing [PyYAML](https://pypi.org/project/PyYAML/) (`pip3 install pyyaml`) enables the full YAML parser for more complex configs.

## Behaviour

- **Duplicate-safe** — `photo.jpg` + `photo.jpg` → `photo.jpg` + `photo_1.jpg`; nothing is ever overwritten.
- **Logging** — every run writes `_logs/organize_<timestamp>.log`.
- **Cross-filesystem** — falls back to copy + delete when a move crosses drives.
- **Safety** — refuses to run if the destination is inside the source, skips symlinks and hidden files, and never touches its own files.
- **Dry-run** — `--dry-run` moves and creates nothing.

## Demo

```bash
python3 demo.py --count 2000 --source ./test_downloads
./organize.sh --source ./test_downloads --dest ./test_organized --dry-run
./organize.sh --source ./test_downloads --dest ./test_organized --copy --verbose
```

See [EXAMPLE.md](EXAMPLE.md) for a full annotated run.

## Requirements

- Python 3.8+ and Bash 4+ (Linux/macOS; Windows via WSL or Git Bash).
- Optional: [PyYAML](https://pypi.org/project/PyYAML/) for advanced YAML configs.

## Automation

**Cron (Linux/macOS):**

```bash
./organize.sh --setup-cron
# 0 9 * * 1 /path/to/organize.sh --source ~/Downloads --dest ~/Organized
```

**Alias (add to `~/.zshrc` or `~/.bashrc`):**

```bash
alias tidy="~/file-organiser/organize.sh --source ~/Downloads"
```

## License

[MIT](LICENSE)
