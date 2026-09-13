#!/usr/bin/env python3
"""
File Organiser.

Sorts a downloads folder into a clean, searchable archive, organised by
file type, date and/or project.

Pure Python standard library (Python 3.8+). PyYAML is optional: the
bundled YAML config is parsed by a small built-in parser when PyYAML is
not installed, so the tool works out of the box with zero dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    import yaml
    HAS_YAML = True
except ImportError:  # pragma: no cover - depends on the environment
    HAS_YAML = False

PROGRAM_NAME = "File Organiser"

# Files that ship with this repo. Never relocate them, even if the user
# points the organiser at the repo itself.
REPO_ROOT = Path(__file__).resolve().parent
REPO_FILES = {
    REPO_ROOT / name
    for name in (
        "organizer.py",
        "organize.sh",
        "demo.py",
        "config.yaml",
        "config.json",
        "README.md",
        "EXAMPLE.md",
        "LICENSE",
        ".gitignore",
        "requirements.txt",
        "pyproject.toml",
    )
}

# Extension -> category mapping.
FILE_TYPES: Dict[str, Set[str]] = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
               ".svg", ".heic", ".raw", ".psd", ".ai"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages",
                  ".md", ".tex"},
    "Spreadsheets": {".xls", ".xlsx", ".csv", ".ods", ".numbers"},
    "Presentations": {".ppt", ".pptx", ".key", ".odp"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
                 ".dmg", ".iso"},
    "Videos": {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm",
               ".m4v", ".mpeg", ".mpg"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a",
              ".aiff"},
    "Code": {".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json",
             ".xml", ".sh", ".bash", ".java", ".cpp", ".c", ".h", ".go",
             ".rs", ".php", ".rb", ".sql", ".ipynb", ".toml", ".yaml",
             ".yml"},
    "Design": {".fig", ".sketch", ".xd", ".indd", ".blend", ".fbx", ".obj"},
    "Executables": {".exe", ".app", ".msi", ".deb", ".rpm", ".apk"},
}

# Built-in project keywords, used when no config file is present.
DEFAULT_PROJECTS: Dict[str, List[str]] = {
    "Website-Redesign": ["website", "redesign", "figma", "mockup", "landing"],
    "Tax-2024": ["tax", "invoice", "receipt", "ato", "expense", "w2", "1099"],
    "Uni-Research": ["thesis", "research", "paper", "dissertation", "uni",
                     "assignment"],
    "Client-Photoshoot": ["photoshoot", "client", "wedding", "portrait",
                          "lightroom"],
    "Side-Hustle": ["sidehustle", "etsy", "shopify", "product"],
}

# Date patterns, tried in order. Lookarounds prevent matching the middle of
# longer digit runs (e.g. a 10-digit epoch in a filename).
DATE_PATTERNS = (
    re.compile(r"(?<!\d)(\d{4})[-_.](\d{1,2})[-_.](\d{1,2})(?!\d)"),   # 2024-03-15
    re.compile(r"(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)"),                 # 20240315
    re.compile(r"(?<!\d)(\d{1,2})[-_.](\d{1,2})[-_.](\d{4})(?!\d)"),   # 03-15-2024
)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def format_size(num_bytes: float) -> str:
    """Return a human-readable size, e.g. ``1.6 MB``."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(size) < 1024.0 or unit == "PB":
            if unit == "B":
                return f"{int(size)} B"
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"  # pragma: no cover - unreachable


def get_file_type(suffix: str) -> str:
    """Return the category for a file extension, or ``Other``."""
    suffix = suffix.lower()
    for category, extensions in FILE_TYPES.items():
        if suffix in extensions:
            return category
    return "Other"


def get_file_date(path: Path) -> datetime:
    """Detect a file's date.

    Prefers an explicit ``YYYY-MM-DD`` / ``YYYYMMDD`` / ``MM-DD-YYYY`` date in
    the filename, and falls back to the file modification time.
    """
    name = path.name
    for pattern in DATE_PATTERNS:
        match = pattern.search(name)
        if not match:
            continue
        groups = match.groups()
        try:
            if len(groups[0]) == 4:  # year first
                year, month, day = map(int, groups[:3])
            else:  # month, day, year
                month, day, year = map(int, groups[:3])
            if 2000 <= year <= 2099:
                return datetime(year, month, day)  # raises on invalid dates
        except ValueError:
            continue
    return datetime.fromtimestamp(path.stat().st_mtime)


def detect_project(filename: str, projects: Dict[str, List[str]]) -> Optional[str]:
    """Return the first project whose keywords match ``filename``."""
    lowered = filename.lower()
    for project, keywords in projects.items():
        for keyword in keywords:
            kw = str(keyword).strip().lower()
            if kw and kw in lowered:
                return project
    return None


# ---------------------------------------------------------------------------
# Configuration loading (works with or without PyYAML)
# ---------------------------------------------------------------------------

def _strip_yaml_comment(line: str) -> str:
    """Remove a YAML comment (a ``#`` at start-of-line or after whitespace)."""
    in_quote: Optional[str] = None
    for index, char in enumerate(line):
        if in_quote:
            if char == in_quote:
                in_quote = None
        elif char in "\"'":
            in_quote = char
        elif char == "#" and (index == 0 or line[index - 1] in " \t"):
            return line[:index]
    return line


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _parse_simple_yaml(text: str) -> dict:
    """Parse the small YAML subset used by ``config.yaml``.

    Supports comments, blank lines, top-level mappings (``projects:``,
    ``file_types:``), nested list owners (``  Website-Redesign:``), list
    items (``    - keyword``) and inline lists (``key: [a, b, c]``).

    This fallback keeps the tool dependency-free when PyYAML is absent.
    """
    result: dict = {}
    current_section: Optional[str] = None
    current_key: Optional[str] = None

    for raw_line in text.splitlines():
        line = _strip_yaml_comment(raw_line).rstrip()
        if not line.strip():
            continue

        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # A mapping key: "projects:" (top level) or "  Website-Redesign:".
        if stripped.endswith(":") and not stripped.startswith("-"):
            key = stripped[:-1].strip()
            if indent == 0:
                current_section = key
                current_key = None
                result.setdefault(key, {})
            else:
                current_key = key
                result.setdefault(current_section, {}).setdefault(key, [])
            continue

        # List item: "    - keyword".
        if stripped.startswith("-"):
            item = _unquote(stripped[1:].strip())
            if current_key is not None:
                result.setdefault(current_section, {}).setdefault(
                    current_key, []
                ).append(item)
            continue

        # Inline list: "  3D-Models: [.blend, .fbx]".
        if ":" in stripped:
            key, _, value = stripped.partition(":")
            value = value.strip()
            key = key.strip()
            if value.startswith("[") and value.endswith("]"):
                items = [
                    _unquote(part)
                    for part in value[1:-1].split(",")
                    if part.strip()
                ]
                if indent == 0:
                    result.setdefault(key, {}).update({"_inline": items})
                else:
                    result.setdefault(current_section, {}).setdefault(
                        key, []
                    ).extend(items)
    return result


def _read_config_file(config_path: Path) -> dict:
    """Read a ``.json`` or ``.yaml``/``.yml`` config into a dict."""
    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() == ".json":
        return json.loads(text)
    if HAS_YAML:
        return yaml.safe_load(text) or {}
    return _parse_simple_yaml(text)


def load_config(
    config_path: Path,
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Load project keywords and custom file types from the config file.

    Returns ``(projects, custom_types)``. Always succeeds: missing or
    unreadable configs degrade gracefully to the built-in defaults.
    """
    projects: Dict[str, List[str]] = dict(DEFAULT_PROJECTS)
    custom_types: Dict[str, List[str]] = {}

    if not config_path.exists():
        return projects, custom_types

    try:
        data = _read_config_file(config_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"warning: could not read config {config_path}: {exc}")
        print("         using built-in defaults")
        return projects, custom_types

    for name, keywords in (data.get("projects") or {}).items():
        if isinstance(keywords, (list, tuple)):
            projects[str(name)] = [str(kw) for kw in keywords]

    for category, extensions in (data.get("file_types") or {}).items():
        if isinstance(extensions, (list, tuple)):
            custom_types[str(category)] = [str(ext) for ext in extensions]

    return projects, custom_types


def apply_custom_types(custom_types: Dict[str, List[str]]) -> None:
    """Merge user-supplied file types into ``FILE_TYPES``.

    Custom mappings take priority: an extension assigned to a custom
    category is removed from every other category first, so the custom
    category always wins.
    """
    for category, extensions in custom_types.items():
        normalized = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}"
            for ext in extensions
            if ext and ext.strip()
        }
        if not normalized:
            continue
        for other_category in FILE_TYPES:
            if other_category != category:
                FILE_TYPES[other_category].difference_update(normalized)
        FILE_TYPES.setdefault(category, set()).update(normalized)


# ---------------------------------------------------------------------------
# Relocation (move / copy) with duplicate safety
# ---------------------------------------------------------------------------

def _unique_path(dest_dir: Path, filename: str, reserved: Set[Path]) -> Path:
    """Return a destination path that does not clash.

    Clashes are detected against both the filesystem and the ``reserved``
    set (so dry-runs can predict ``name_1``-style renames).
    """
    candidate = dest_dir / filename
    if candidate not in reserved and not candidate.exists():
        reserved.add(candidate)
        return candidate

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        candidate = dest_dir / f"{stem}_{counter}{suffix}"
        if candidate not in reserved and not candidate.exists():
            reserved.add(candidate)
            return candidate
        counter += 1


def _relocate(src: Path, dest_file: Path, action: str) -> None:
    """Move or copy ``src`` to ``dest_file``. Never overwrites (the caller
    has already picked a unique path)."""
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    if action == "copy":
        shutil.copy2(str(src), str(dest_file))
        return
    try:
        shutil.move(str(src), str(dest_file))
    except OSError:
        # Cross-filesystem move: copy then delete.
        shutil.copy2(str(src), str(dest_file))
        src.unlink()


def _destination_for(
    by: str, dest: Path, category: str, project: Optional[str], fdate: datetime
) -> Path:
    """Build the destination directory for a file based on the chosen mode."""
    year = str(fdate.year)
    month = f"{fdate.year}-{fdate.month:02d}"

    if by == "type":
        return dest / category
    if by == "date":
        return dest / year / month
    if by == "project":
        return dest / "Projects" / (project or "_Unsorted") / category
    # "all" (default)
    if project:
        return dest / "Projects" / project / category / year / month
    return dest / category / year / month


# ---------------------------------------------------------------------------
# Filesystem scanning
# ---------------------------------------------------------------------------

def _iter_files(source: Path, recursive: bool, include_hidden: bool):
    """Yield files to organise in a deterministic order.

    Symlinks and hidden files/directories are skipped (unless requested).
    """
    if recursive:
        for root, dirs, filenames in os.walk(source):
            dirs[:] = sorted(
                d for d in dirs if include_hidden or not d.startswith(".")
            )
            for name in sorted(filenames):
                if not include_hidden and name.startswith("."):
                    continue
                path = Path(root) / name
                if not path.is_symlink():
                    yield path
    else:
        for entry in sorted(source.iterdir(), key=lambda p: p.name.lower()):
            if entry.is_symlink() or not entry.is_file():
                continue
            if include_hidden or not entry.name.startswith("."):
                yield entry


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def _resolve_config(config_arg: str) -> Path:
    """Resolve the config path (cwd first, then the script directory)."""
    candidate = Path(config_arg).expanduser()
    if candidate.is_absolute():
        return candidate
    cwd_candidate = (Path.cwd() / candidate).resolve()
    if cwd_candidate.exists():
        return cwd_candidate
    return (REPO_ROOT / candidate).resolve()


def _parse_args(argv: Optional[List[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="organizer.py",
        description=(
            "Organise files by type, date and project. "
            "Pure Python, zero required dependencies."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  organizer.py --source ~/Downloads --dest ~/Organized\n"
            "  organizer.py --dry-run --verbose\n"
            "  organizer.py --by project --copy\n"
            "  organizer.py --source ./my-mess --dest ./clean --limit 100\n"
        ),
    )
    parser.add_argument("--source", "-s", default=str(Path.home() / "Downloads"),
                        help="Source folder (default: ~/Downloads)")
    parser.add_argument("--dest", "-d", default=str(Path.home() / "Organized"),
                        help="Destination folder (default: ~/Organized)")
    parser.add_argument("--config", default="config.yaml",
                        help="Config file for projects & custom types")
    parser.add_argument("--by", choices=["type", "date", "project", "all"],
                        default="all",
                        help="Organisation method (default: all)")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Preview without moving or creating anything")
    parser.add_argument("--copy", "-c", action="store_true",
                        help="Copy files instead of moving them")
    parser.add_argument("--move", action="store_true",
                        help="Move files (this is the default)")
    parser.add_argument("--recursive", "-r", action="store_true",
                        help="Scan subfolders recursively")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show every file and its destination")
    parser.add_argument("--limit", type=int, default=0,
                        help="Process only N files (0 = no limit)")
    parser.add_argument("--include-hidden", action="store_true",
                        help="Include hidden files and folders")
    return parser.parse_args(argv)


def _print_header(args: argparse.Namespace, source: Path, dest: Path,
                  config_path: Path) -> None:
    action = "copy" if args.copy else "move"
    mode = "dry-run" if args.dry_run else "live"
    config_state = "found" if config_path.exists() else "using defaults"
    print(PROGRAM_NAME)
    print(f"  Source:       {source}")
    print(f"  Destination:  {dest}")
    print(f"  Mode:         {args.by} | {action} | {mode}")
    print(f"  Config:       {config_path} ({config_state})")
    print()


def organize(args: argparse.Namespace, source: Path, dest: Path,
             config_path: Path) -> int:
    """Run the organiser. Returns a process exit code."""
    projects, custom_types = load_config(config_path)
    apply_custom_types(custom_types)

    action = "copy" if args.copy else "move"
    _print_header(args, source, dest, config_path)

    files = list(_iter_files(source, args.recursive, args.include_hidden))
    # Never relocate this repo's own files if the user points at it.
    files = [p for p in files if p.resolve() not in REPO_FILES]

    total_found = len(files)
    if args.limit and args.limit > 0:
        files = files[: args.limit]

    if not files:
        print("No files to organise.")
        return 0

    print(f"Found {total_found:,} file{'s' if total_found != 1 else ''} "
          f"({len(files):,} to process)")
    if args.dry_run:
        print("Dry run: nothing will be moved or created.")
    print()

    type_counts: Counter = Counter()
    project_counts: Counter = Counter()
    total_size = 0
    processed = 0
    errors: List[str] = []
    reserved: Set[Path] = set()

    width = len(str(len(files)))

    for index, src in enumerate(files, 1):
        try:
            category = get_file_type(src.suffix)
            fdate = get_file_date(src)
            project = detect_project(src.name, projects)

            dest_dir = _destination_for(args.by, dest, category, project, fdate)
            dest_file = _unique_path(dest_dir, src.name, reserved)

            total_size += src.stat().st_size
            type_counts[category] += 1
            if project:
                project_counts[project] += 1

            if args.verbose or args.dry_run:
                suffix = f" -> {project}" if project else ""
                print(f"[{index:>{width}}/{len(files)}] {src.name} "
                      f"[{category}, {fdate.date()}]{suffix}")
                if args.verbose:
                    print(f"{' ' * (width * 2 + 4)}-> {dest_file.parent}/")
            elif index % 200 == 0 or index == len(files):
                print(f"  Processed {index:,}/{len(files):,} files "
                      f"({index / len(files) * 100:.0f}%)")

            if not args.dry_run:
                _relocate(src, dest_file, action)
            processed += 1
        except (OSError, shutil.Error) as exc:
            errors.append(f"{src.name}: {exc}")
            if args.verbose:
                print(f"  error: {src.name}: {exc}")

    _print_summary(args, processed, total_size, errors, type_counts,
                   project_counts)

    if not args.dry_run:
        log_file = _write_log(dest, source, processed, total_size,
                              type_counts, project_counts, errors)
        print(f"Log saved to: {log_file}")

    return 1 if errors else 0


def _print_summary(args: argparse.Namespace, processed: int, total_size: int,
                   errors: List[str], type_counts: Counter,
                   project_counts: Counter) -> None:
    print()
    print("Summary")
    print(f"  Processed:  {processed:,} files")
    print(f"  Total size: {format_size(total_size)}")
    print(f"  Errors:     {len(errors)}")
    if args.dry_run:
        print("  Mode:       dry-run (no changes made)")

    print()
    print("  By type:")
    for category, count in type_counts.most_common():
        print(f"    {category:<15} {count:>6,}")

    if project_counts:
        print()
        print("  By project:")
        for project, count in project_counts.most_common():
            print(f"    {project:<22} {count:>6,}")

    if errors:
        print()
        print(f"  {len(errors)} file(s) could not be processed:")
        for message in errors[:10]:
            print(f"    - {message}")
        if len(errors) > 10:
            print(f"    - ... and {len(errors) - 10} more (see the log file)")


def _write_log(dest: Path, source: Path, processed: int, total_size: int,
               type_counts: Counter, project_counts: Counter,
               errors: List[str]) -> Path:
    log_dir = dest / "_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / (
        f"organize_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    )
    lines = [
        f"source: {source}",
        f"destination: {dest}",
        f"processed: {processed}",
        f"total_size: {total_size}",
        "by_type:",
    ]
    lines += [f"  - {category}: {count}" for category, count
              in type_counts.most_common()]
    lines.append("by_project:")
    lines += [f"  - {project}: {count}" for project, count
              in project_counts.most_common()]
    if errors:
        lines.append("errors:")
        lines += [f"  - {message}" for message in errors]
    log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return log_file


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)

    source = Path(args.source).expanduser().resolve()
    dest = Path(args.dest).expanduser().resolve()

    if not source.exists():
        print(f"error: source folder does not exist: {source}")
        return 1
    if not source.is_dir():
        print(f"error: source is not a folder: {source}")
        return 1
    if source == dest:
        print("error: source and destination must be different folders")
        return 1
    if _is_within(dest, source):
        print("error: the destination folder cannot be inside the source folder")
        return 1

    config_path = _resolve_config(args.config)
    return organize(args, source, dest, config_path)


if __name__ == "__main__":
    sys.exit(main())
