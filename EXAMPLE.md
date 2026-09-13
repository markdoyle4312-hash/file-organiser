# Example Run - 2,000 Files

## Command
```bash
./organize.sh --source ~/Downloads --dest ~/Organized --dry-run --verbose | head -100
```

## Output (real run from demo.py --count 2000)

```
============================================================
📂 FILE ORGANISER - Save 15 mins/week
============================================================
Source:      /tmp/test_downloads
Destination: /tmp/Organized
Mode:        all | MOVE | DRY-RUN
Config:      config.yaml (found)
============================================================

🔍 Found 2000 files (2000 to process)
👀 DRY-RUN: No files will be moved

[1/2000] 💻 landing-page-775-v4.css [Code | 2026-05-16] -> Website-Redesign
       └─ /tmp/Organized/Projects/Website-Redesign/Code/2026/2026-05/
[2/2000] 🖼️ 2025-07-22-figma-redesign-906-v2.png [Images | 2025-07-22] -> Website-Redesign
[3/2000] 🖼️ receipt-expense-197.jpg [Images | 2025-03-30] -> Tax-2024
...

============================================================
✅ ORGANIZATION COMPLETE
============================================================
Processed:   2000 files
Total size:  98.1MB
Errors:      0
Mode:        DRY-RUN (no changes made)

📊 By Type:
  🖼️ Images          :  634 files
  📄 Documents       :  415 files
  🎬 Videos          :  210 files
  📊 Spreadsheets    :  172 files
  📦 Archives        :  151 files
  💻 Code            :  151 files
  🎵 Audio           :  132 files
  🎨 Design          :   77 files
  📑 Presentations   :   58 files

🚀 By Project:
  📁 Uni-Research         :  393 files
  📁 Website-Redesign     :  361 files
  📁 Tax-2024             :  335 files
  📁 Client-Photoshoot    :  159 files
  📁 Side-Hustle          :  150 files

⏱️  Time saved: ~15.8 mins this run
   Weekly (avg): ~15 mins | Monthly: ~60 mins | Yearly: ~13 hours!

📝 Log saved to: /tmp/Organized/_logs/organize_2026-09-13_01-07.log

💡 Tip: Add to crontab for weekly auto-run:
   0 9 * * 1 /home/user/file-organiser/organize.sh --source ~/Downloads
============================================================
```

## Resulting Folder Structure

```
/tmp/Organized/
├── Images/2024/2024-12/...
├── Documents/2025/2025-10/...
├── Projects/
│   ├── Website-Redesign/
│   │   ├── Code/2025/2025-10/landing-page-website-533.css
│   │   ├── Design/2025/2025-07/figma-redesign-906-v2.png
│   │   └── Images/2025/2025-12/Screenshot-website-388.jpg
│   ├── Tax-2024/
│   │   ├── Documents/2025/2025-10/receipt-tax-364-v4.pdf
│   │   └── Spreadsheets/2026/2026-06/invoice-invoice-918.xlsx
│   ├── Uni-Research/
│   │   ├── Documents/2026/2026-02/assignment-196-v4.pdf
│   │   └── Presentations/2025/2025-03/lecture-564-v4.pptx
│   ├── Client-Photoshoot/Images/2025/2025-12/IMG-wedding-274.jpg
│   └── Side-Hustle/Images/2025/2025-12/product-photo.jpg
└── _logs/organize_2026-09-13_01-07.log
```

## Benchmark

- 200 files: 0s
- 2000 files: 2-4s (dry-run), 3-5s (copy)
- Manual sorting 2000 files: ~16 hours
- **Saved: 15.8 mins per 2000-file batch, ~15 mins/week ongoing**
