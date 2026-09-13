# Example run — 2,000 files

A real run against 2,000 generated test files (see `demo.py`).

## Command

```bash
python3 demo.py --count 2000 --source /tmp/test_downloads
python3 organizer.py --source /tmp/test_downloads --dest /tmp/test_organized --dry-run --verbose | head -40
```

## Output

```
File Organiser
  Source:       /tmp/test_downloads
  Destination:  /tmp/test_organized
  Mode:         all | move | dry-run
  Config:       /home/user/file-organiser/config.yaml (found)

Found 2,000 files (2,000 to process)
Dry run: nothing will be moved or created.

[   1/2000] 2024-10-14-product-photo-etsy.psd [Images, 2024-10-14] -> Side-Hustle
           -> /tmp/test_organized/Projects/Side-Hustle/Images/2024/2024-10/
[   2/2000] 2024-10-14-song-346.wav [Audio, 2024-10-14]
           -> /tmp/test_organized/Audio/2024/2024-10/
[   3/2000] 2024-10-17-receipt.pdf [Documents, 2024-10-17] -> Tax-2024
           -> /tmp/test_organized/Projects/Tax-2024/Documents/2024/2024-10/
[   4/2000] 2024-10-19-IMG-photoshoot-956.jpg [Images, 2024-10-19] -> Client-Photoshoot
           -> /tmp/test_organized/Projects/Client-Photoshoot/Images/2024/2024-10/
...
[1999/2000] video_8.mov [Videos, 2026-02-14]
           -> /tmp/test_organized/Videos/2026/2026-02/
[2000/2000] video_9.mov [Videos, 2025-12-15]
           -> /tmp/test_organized/Videos/2025/2025-12/

Summary
  Processed:  2,000 files
  Total size: 95.5 MB
  Errors:     0
  Mode:       dry-run (no changes made)

  By type:
    Images              594
    Documents           429
    Videos              185
    Code                171
    Spreadsheets        168
    Audio               163
    Archives            161
    Design               84
    Presentations        45

  By project:
    Uni-Research             373
    Website-Redesign         370
    Tax-2024                 348
    Client-Photoshoot        151
    Side-Hustle              147
```

## Resulting folder structure

```
/tmp/test_organized/
├── Audio/2024/2024-10/...
├── Documents/2025/2025-03/...
├── Images/2024/2024-12/...
├── Videos/2025/2025-04/...
├── Projects/
│   ├── Website-Redesign/
│   │   ├── Code/2024/2024-10/landing-page-website-457-v4.js
│   │   ├── Design/2025/2025-07/figma-redesign-906-v2.fig
│   │   └── Images/2025/2025-12/Screenshot-website-388.jpg
│   ├── Tax-2024/
│   │   ├── Documents/2024/2024-10/receipt-tax-348.pdf
│   │   └── Spreadsheets/2026/2026-06/invoice-invoice-918.xlsx
│   ├── Uni-Research/
│   │   ├── Documents/2026/2026-02/assignment-196-v4.docx
│   │   └── Presentations/2025/2025-03/lecture-564-v4.pptx
│   ├── Client-Photoshoot/Images/2025/2025-12/IMG-wedding-274.jpg
│   └── Side-Hustle/Images/2024/2024-12/product-photo.jpg
└── _logs/organize_2026-09-13_01-27-40.log
```

Duplicate names are auto-renamed, e.g. `product-photo.jpg` + `product-photo.jpg`
→ `product-photo.jpg` + `product-photo_1.jpg`.

## Benchmark

| Operation | Time |
|-----------|------|
| Generate 2,000 test files | ~0.2 s |
| Dry-run (2,000 files) | ~0.1 s |
| Live move (2,000 files) | ~0.3 s |
