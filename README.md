# File Organiser — Bash + Python

**Sort 2,000+ downloaded files into project folders by type and date. Save ~15 minutes a week.**

A hybrid Bash + Python tool that turns a chaotic `~/Downloads` folder into a clean, searchable archive. Handles 2000+ files efficiently with smart date parsing, project detection, and duplicate safety.

### What it does

- **By Type:** Images, Documents, Videos, Audio, Code, Archives, etc. (40+ extensions)
- **By Date:** `2024/2024-03/` structure using filename dates or file mtime
- **By Project:** Detects projects from filename keywords (configurable)
- **Combined:** `Projects/Website-Redesign/Images/2024/2024-03/` — the default `all` mode

### Result Structure

```
~/Organized/
├── Images/
│   ├── 2024/2024-03/
│   └── 2023/2023-12/
├── Documents/2024/2024-02/
├── Videos/
├── Code/
├── Projects/
│   ├── Website-Redesign/
│   │   ├── Design/2024/2024-03/
│   │   └── Images/2024/2024-03/
│   ├── Tax-2024/Documents/2024/2024-01/
│   └── _Unsorted/
└── _logs/
```

### Quick Start

```bash
# 1. Clone / download this folder
chmod +x organize.sh organizer.py

# 2. Preview (always do this first!)
./organize.sh --dry-run --verbose

# 3. Organize for real
./organize.sh

# 4. Auto-run every Monday 9am
./organize.sh --setup-cron
```

#### Python only:

```bash
python3 organizer.py --source ~/Downloads --dest ~/Organized --dry-run
python3 organizer.py --by project --copy --verbose
python3 organizer.py --source ./my-mess --dest ./clean --limit 100
```

### Options

| Flag | Description |
|------|-------------|
| `-s, --source` | Source folder (default: `~/Downloads`) |
| `-d, --dest` | Destination (default: `~/Organized`) |
| `-m, --by` | `type`, `date`, `project`, `all` (default) |
| `-n, --dry-run` | Preview, don't move |
| `-c, --copy` | Copy instead of move (safer) |
| `-r, --recursive` | Scan subfolders |
| `-v, --verbose` | Show every file |
| `--limit N` | Process only N files (testing) |
| `--setup-cron` | Install weekly cron job |
| `--install` | Check/install deps |

### ⚙️ Configuration

Edit `config.yaml` to add your projects:

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

Any file with those keywords goes to `Projects/MyStartup/...`

### Smart Features for 2000+ Files

- **Fast:** No external deps, pure Python stdlib + optional PyYAML, processes 2000 files in ~2-5s
- **Date parsing:** Detects `2024-03-15`, `20240315`, `03-15-2024` in filenames, falls back to mtime
- **Duplicate safe:** `photo.jpg` + `photo.jpg` → `photo_1.jpg`, never overwrites
- **Progress:** Shows % every 100 files, full list in verbose/dry-run
- **Logs:** Each run writes to `_logs/organize_YYYY-MM-DD_HH-MM.log`
- **Cross-filesystem:** Handles move across drives (copy+delete fallback)
- **Time saved:** Calculates ~0.5s manual/file vs automated

### Time Saved Math

- Manual: 2,000 files × 30 sec (find, decide, drag) = ~16.6 hours to clean once
- Weekly: ~50 new downloads × 30 sec = 25 mins/week sorting
- **Automated: 2,000 files in ~5 seconds, weekly in <1 second**
- **You save ~15 mins/week = 13 hours/year**

### Demo — Generate 2000 Test Files

```bash
python3 demo.py --count 2000 --source ./test_downloads
./organize.sh --source ./test_downloads --dest ./test_organized --dry-run
./organize.sh --source ./test_downloads --dest ./test_organized --copy --verbose
```

### Safety

- Always run `--dry-run` first
- Use `--copy` if you want to keep originals
- Ignores hidden files (`.DS_Store`) unless `--include-hidden`
- Never overwrites — auto-renames duplicates
- Skips its own script/config files

### Requirements

- Bash 4+, Python 3.8+
- Optional: `PyYAML` (`pip install pyyaml`) for YAML config, falls back to JSON

### Automation

**Cron (Linux/macOS):**
```bash
./organize.sh --setup-cron
# 0 9 * * 1 ~/file-organiser/organize.sh
```

**Manual alias (add to ~/.zshrc or ~/.bashrc):**
```bash
alias tidy=" ~/file-organiser/organize.sh --source ~/Downloads"
```

### License

MIT — do what you want, save time.

---
Built for Adelaide, 2026. For people with 2,000+ files in Downloads and no time to sort them.
