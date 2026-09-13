#!/usr/bin/env python3
"""Demo generator — creates realistic downloaded files for testing."""
import argparse
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

FILE_TEMPLATES = [
    # (prefix, extensions, project_keywords)
    ("IMG", [".jpg", ".png", ".heic"], ["photoshoot", "wedding", ""]),
    ("Screenshot", [".png", ".jpg"], ["", "website", ""]),
    ("invoice", [".pdf", ".xlsx"], ["tax", "invoice", ""]),
    ("receipt", [".pdf", ".jpg"], ["tax", "expense", ""]),
    ("assignment", [".docx", ".pdf"], ["uni", "research", ""]),
    ("lecture", [".pdf", ".pptx", ".mp4"], ["uni", "", ""]),
    ("figma", [".fig", ".png"], ["website", "redesign", "mockup"]),
    ("landing-page", [".html", ".css", ".js"], ["website", ""]),
    ("product-photo", [".jpg", ".psd"], ["sidehustle", "etsy", ""]),
    ("video", [".mp4", ".mov"], ["", "photoshoot", ""]),
    ("song", [".mp3", ".wav"], ["", "", ""]),
    ("backup", [".zip", ".tar.gz"], ["", "", ""]),
    ("report", [".pdf", ".xlsx", ".csv"], ["tax", "research", ""]),
]

def random_date():
    # Random date in last 2 years
    days_ago = random.randint(0, 700)
    dt = datetime.now() - timedelta(days=days_ago)
    # 30% chance include date in filename
    if random.random() < 0.3:
        return dt, dt.strftime("%Y-%m-%d")
    return dt, ""

def generate_files(count: int, source: Path):
    source.mkdir(parents=True, exist_ok=True)
    print(f"Generating {count} test files in {source}...")
    
    for i in range(count):
        prefix, exts, proj_keywords = random.choice(FILE_TEMPLATES)
        ext = random.choice(exts)
        proj_kw = random.choice(proj_keywords)
        dt, date_str = random_date()
        
        # Build filename
        parts = []
        if date_str and random.random() < 0.5:
            parts.append(date_str)
        parts.append(prefix)
        if proj_kw:
            parts.append(proj_kw)
        if random.random() < 0.7:
            parts.append(f"{random.randint(1,999)}")
        if random.random() < 0.3:
            parts.append(f"v{random.randint(1,5)}")
        
        filename = "-".join([p for p in parts if p]) + ext
        
        # Handle double extension like .tar.gz
        file_path = source / filename
        
        # Create small dummy file (0-100KB) with clean duplicate handling
        size = random.randint(0, 100*1024)
        original_stem = Path(filename).stem
        # For .tar.gz, keep both suffixes
        if filename.endswith(".tar.gz"):
            original_stem = filename[:-7]
            original_suffix = ".tar.gz"
        else:
            original_suffix = Path(filename).suffix
        
        counter = 1
        while file_path.exists():
            file_path = source / f"{original_stem}_{counter}{original_suffix}"
            counter += 1
        file_path.write_bytes(b"\0" * size)

        # Set mtime to the random date
        timestamp = dt.timestamp()
        os.utime(file_path, (timestamp, timestamp))
        
        if (i+1) % 500 == 0:
            print(f"  ... {i+1}/{count}")
    
    print(f"✅ Done! Created {count} files")
    print(f"   Total size: {sum(f.stat().st_size for f in source.iterdir())/1024/1024:.1f} MB")
    print(f"   Run: ./organize.sh --source {source} --dest ./organized --dry-run --verbose | head -100")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=2000, help="Number of files to generate")
    parser.add_argument("--source", default="./test_downloads", help="Folder to create files in")
    args = parser.parse_args()
    
    generate_files(args.count, Path(args.source).expanduser().resolve())
