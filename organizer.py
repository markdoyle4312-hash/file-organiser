#!/usr/bin/env python3
"""
File Organiser - Sorts 2000+ files by type, date, and project
Bash + Python hybrid - Core engine

Saves ~15 mins/week by auto-organizing Downloads folder.
"""

import argparse
import json
import os
import re
import shutil
import sys
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path

# Try to import yaml, fallback to json config
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# File type definitions - easily extensible
FILE_TYPES = {
    "Images": {
        "exts": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg", ".heic", ".raw", ".psd", ".ai"},
        "icon": "🖼️"
    },
    "Documents": {
        "exts": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages", ".md", ".tex"},
        "icon": "📄"
    },
    "Spreadsheets": {
        "exts": {".xls", ".xlsx", ".csv", ".ods", ".numbers"},
        "icon": "📊"
    },
    "Presentations": {
        "exts": {".ppt", ".pptx", ".key", ".odp"},
        "icon": "📑"
    },
    "Archives": {
        "exts": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".dmg", ".iso"},
        "icon": "📦"
    },
    "Videos": {
        "exts": {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v", ".mpeg"},
        "icon": "🎬"
    },
    "Audio": {
        "exts": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".aiff"},
        "icon": "🎵"
    },
    "Code": {
        "exts": {".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".sh", ".bash", ".java", ".cpp", ".c", ".go", ".rs", ".php", ".rb", ".sql", ".ipynb"},
        "icon": "💻"
    },
    "Design": {
        "exts": {".fig", ".sketch", ".xd", ".psd", ".ai", ".indd", ".blend", ".fbx", ".obj"},
        "icon": "🎨"
    },
    "Executables": {
        "exts": {".exe", ".app", ".msi", ".deb", ".rpm", ".apk"},
        "icon": "⚙️"
    },
}

# Default project keywords - user customizable via config.yaml
DEFAULT_PROJECTS = {
    "Website-Redesign": ["website", "redesign", "figma", "mockup", "landing"],
    "Tax-2024": ["tax", "invoice", "receipt", "ato", "expense", "w2", "1099"],
    "Uni-Research": ["thesis", "research", "paper", "dissertation", "uni", "assignment"],
    "Client-Photoshoot": ["photoshoot", "client", "wedding", "portrait", "lightroom"],
    "Side-Hustle": ["sidehustle", "etsy", "shopify", "product"],
}

def get_file_type(ext: str) -> str:
    """Return category for extension, or 'Other'"""
    ext = ext.lower()
    for category, data in FILE_TYPES.items():
        if ext in data["exts"]:
            return category
    return "Other"

def get_file_date(file_path: Path) -> datetime:
    """
    Smart date detection:
    1. Try to parse YYYY-MM-DD or YYYYMMDD from filename
    2. Fall back to file modification time
    """
    name = file_path.name
    
    # Pattern 1: 2024-03-15, 2024_03_15, 2024.03.15
    patterns = [
        r'(\d{4})[-_.](\d{1,2})[-_.](\d{1,2})',
        r'(\d{4})(\d{2})(\d{2})',  # 20240315
        r'(\d{2})[-_.](\d{1,2})[-_.](\d{4})',  # MM-DD-YYYY
    ]
    
    for pat in patterns:
        match = re.search(pat, name)
        if match:
            try:
                groups = match.groups()
                if len(groups[0]) == 4:  # YYYY first
                    y, m, d = map(int, groups[:3])
                else:
                    m, d, y = map(int, groups[:3])
                # Validate date
                if 1 <= m <= 12 and 1 <= d <= 31 and 2000 <= y <= 2030:
                    return datetime(y, m, d)
            except:
                pass
    
    # Fallback to mtime
    mtime = file_path.stat().st_mtime
    return datetime.fromtimestamp(mtime)

def detect_project(filename: str, projects: dict) -> str | None:
    """Detect project based on keywords in filename"""
    lower = filename.lower()
    for project, keywords in projects.items():
        # Ensure keywords is iterable
        if not isinstance(keywords, (list, tuple, set)):
            continue
        for kw in keywords:
            try:
                kw_str = str(kw).lower()
                if kw_str and kw_str in lower:
                    return project
            except:
                continue
    return None

def safe_move(src: Path, dest_dir: Path, dry_run: bool = False) -> Path:
    """Move file to dest_dir, handling duplicates by adding _1, _2 etc"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    
    if dest.exists():
        # File exists - check if identical
        if dest.stat().st_size == src.stat().st_size:
            # Likely duplicate - compare more? For speed, just skip if same size + name
            pass
        
        stem = src.stem
        suffix = src.suffix
        counter = 1
        while dest.exists():
            dest = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1
    
    if not dry_run:
        try:
            shutil.move(str(src), str(dest))
        except Exception as e:
            # Fallback: copy + delete (cross-filesystem)
            shutil.copy2(str(src), str(dest))
            src.unlink()
    
    return dest

def load_config(config_path: Path) -> dict:
    """Load projects and custom types from config"""
    projects = DEFAULT_PROJECTS.copy()
    custom_types = {}
    
    if not config_path.exists():
        return projects, custom_types
    
    try:
        if config_path.suffix in [".yaml", ".yml"] and HAS_YAML:
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}
        else:
            with open(config_path) as f:
                data = json.load(f)
        
        if "projects" in data:
            # Merge with defaults, user config overrides
            projects.update(data["projects"])
        if "file_types" in data:
            custom_types = data["file_types"]
    except Exception as e:
        print(f"⚠️  Warning: Could not load config {config_path}: {e}")
    
    return projects, custom_types

def format_size(num_bytes: int) -> str:
    for unit in ['B','KB','MB','GB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.1f}{unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f}TB"

def main():
    parser = argparse.ArgumentParser(
        description="Organize 2000+ downloaded files by type, date & project - Save 15 mins/week",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --source ~/Downloads --dest ~/Organized
  %(prog)s --dry-run --verbose
  %(prog)s --by project --move
  %(prog)s --source ./test_files --dest ./organized --copy
        """
    )
    parser.add_argument("--source", "-s", default=str(Path.home() / "Downloads"),
                        help="Source folder to organize (default: ~/Downloads)")
    parser.add_argument("--dest", "-d", default=str(Path.home() / "Organized"),
                        help="Destination folder (default: ~/Organized)")
    parser.add_argument("--config", "-c", default="config.yaml",
                        help="Config file for projects & custom types (default: config.yaml)")
    parser.add_argument("--by", choices=["type", "date", "project", "all"], default="all",
                        help="Organization method (default: all = type/date/project)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without moving files")
    parser.add_argument("--copy", action="store_true", help="Copy instead of move (safer)")
    parser.add_argument("--move", action="store_true", help="Force move (default)")
    parser.add_argument("--recursive", "-r", action="store_true", help="Scan subfolders recursively")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--limit", type=int, default=0, help="Limit files processed (0 = no limit, for testing)")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden files")
    
    args = parser.parse_args()
    
    source = Path(args.source).expanduser().resolve()
    dest = Path(args.dest).expanduser().resolve()
    
    # Resolve config path relative to script location or cwd
    script_dir = Path(__file__).parent
    config_candidates = [
        Path(args.config),
        script_dir / args.config,
        script_dir / "config.json",
        Path.cwd() / args.config,
    ]
    config_path = None
    for cand in config_candidates:
        if cand.exists():
            config_path = cand
            break
    if config_path is None:
        config_path = script_dir / args.config  # default path for creation hint
    
    if not source.exists():
        print(f"❌ Source folder does not exist: {source}")
        sys.exit(1)
    
    projects, custom_types = load_config(config_path)
    
    # Merge custom types
    if custom_types:
        for cat, exts in custom_types.items():
            if cat in FILE_TYPES:
                FILE_TYPES[cat]["exts"].update(set(e.lower() if e.startswith('.') else f'.{e.lower()}' for e in exts))
            else:
                FILE_TYPES[cat] = {"exts": set(e.lower() if e.startswith('.') else f'.{e.lower()}' for e in exts), "icon": "📁"}
    
    print(f"\n{'='*60}")
    print(f"📂 FILE ORGANISER - Save 15 mins/week")
    print(f"{'='*60}")
    print(f"Source:      {source}")
    print(f"Destination: {dest}")
    print(f"Mode:        {args.by} | {'COPY' if args.copy else 'MOVE'} | {'DRY-RUN' if args.dry_run else 'LIVE'}")
    print(f"Config:      {config_path} ({'found' if config_path.exists() else 'using defaults'})")
    print(f"{'='*60}\n")
    
    # Gather files
    if args.recursive:
        all_files = [p for p in source.rglob("*") if p.is_file()]
    else:
        all_files = [p for p in source.iterdir() if p.is_file()]
    
    if not args.include_hidden:
        all_files = [p for p in all_files if not p.name.startswith(".")]
    
    # Filter out the organizer itself and config
    script_name = Path(__file__).name
    all_files = [p for p in all_files if p.name not in [script_name, "config.yaml", "config.json", "organize.sh"]]
    
    total_found = len(all_files)
    if args.limit and args.limit > 0:
        all_files = all_files[:args.limit]
    
    if not all_files:
        print("✨ No files to organize. You're all tidy!")
        return
    
    print(f"🔍 Found {total_found} files ({len(all_files)} to process)")
    if args.dry_run:
        print("👀 DRY-RUN: No files will be moved\n")
    
    stats = Counter()
    type_counter = Counter()
    project_counter = Counter()
    total_size = 0
    errors = []
    
    # Progress tracking for 2000+ files
    for idx, file_path in enumerate(all_files, 1):
        try:
            ext = file_path.suffix
            ftype = get_file_type(ext)
            fdate = get_file_date(file_path)
            project = detect_project(file_path.name, projects)
            
            type_counter[ftype] += 1
            if project:
                project_counter[project] += 1
            
            total_size += file_path.stat().st_size
            
            # Build destination path based on mode
            if args.by == "type":
                dest_dir = dest / ftype
            elif args.by == "date":
                dest_dir = dest / str(fdate.year) / f"{fdate.year}-{fdate.month:02d}"
            elif args.by == "project":
                if project:
                    dest_dir = dest / "Projects" / project / ftype
                else:
                    dest_dir = dest / "Projects" / "_Unsorted" / ftype
            else:  # all
                if project:
                    dest_dir = dest / "Projects" / project / ftype / str(fdate.year) / f"{fdate.year}-{fdate.month:02d}"
                else:
                    dest_dir = dest / ftype / str(fdate.year) / f"{fdate.year}-{fdate.month:02d}"
            
            if args.verbose or args.dry_run:
                proj_str = f" -> {project}" if project else ""
                print(f"[{idx}/{len(all_files)}] {FILE_TYPES.get(ftype, {}).get('icon','📁')} {file_path.name} [{ftype} | {fdate.date()}]{proj_str}")
                if args.verbose:
                    print(f"       └─ {dest_dir}/")
            elif idx % 100 == 0 or idx == len(all_files):
                # Progress for large batches
                print(f"  ... processed {idx}/{len(all_files)} files ({idx/len(all_files)*100:.0f}%)")
            
            if args.copy:
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file = dest_dir / file_path.name
                # handle duplicate
                counter = 1
                while dest_file.exists() and not args.dry_run:
                    dest_file = dest_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
                    counter += 1
                if not args.dry_run:
                    shutil.copy2(str(file_path), str(dest_file))
            else:
                safe_move(file_path, dest_dir, dry_run=args.dry_run)
            
            stats["processed"] += 1
            
        except Exception as e:
            errors.append(f"{file_path.name}: {e}")
            stats["errors"] += 1
            if args.verbose:
                print(f"❌ Error with {file_path.name}: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"✅ ORGANIZATION COMPLETE")
    print(f"{'='*60}")
    print(f"Processed:   {stats['processed']} files")
    print(f"Total size:  {format_size(total_size)}")
    print(f"Errors:      {stats['errors']}")
    if args.dry_run:
        print(f"Mode:        DRY-RUN (no changes made)")
    
    print(f"\n📊 By Type:")
    for t, count in type_counter.most_common():
        icon = FILE_TYPES.get(t, {}).get('icon', '📁')
        print(f"  {icon} {t:15s} : {count:4d} files")
    
    if project_counter:
        print(f"\n🚀 By Project:")
        for proj, count in project_counter.most_common():
            print(f"  📁 {proj:20s} : {count:4d} files")
    
    # Time saved estimate: ~0.5 sec per file manual vs 0.01 sec automated
    # For 2000 files: manual ~16 mins, automated ~20 secs
    manual_mins = len(all_files) * 0.5 / 60
    saved_mins = manual_mins * 0.95  # 95% saved
    print(f"\n⏱️  Time saved: ~{saved_mins:.1f} mins this run")
    print(f"   Weekly (avg): ~15 mins | Monthly: ~60 mins | Yearly: ~13 hours!")
    
    if errors and args.verbose:
        print(f"\n⚠️  Errors ({len(errors)}):")
        for err in errors[:10]:
            print(f"  - {err}")
    
    # Log file
    log_dir = dest / "_logs" if not args.dry_run else Path.cwd()
    if not args.dry_run:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"organize_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.log"
        with open(log_file, 'w') as lf:
            lf.write(f"Source: {source}\nDest: {dest}\nFiles: {stats['processed']}\nSize: {format_size(total_size)}\n")
            lf.write(f"By Type: {dict(type_counter)}\n")
            lf.write(f"By Project: {dict(project_counter)}\n")
            if errors:
                lf.write(f"Errors: {errors}\n")
        print(f"\n📝 Log saved to: {log_file}")
    
    print(f"\n💡 Tip: Add to crontab for weekly auto-run:")
    print(f"   0 9 * * 1 {Path(__file__).parent / 'organize.sh'} --source ~/Downloads")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
