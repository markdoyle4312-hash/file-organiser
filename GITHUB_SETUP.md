# GitHub Setup — Exact Steps

Your local repo is already initialized and committed on `main` branch. Now push it to GitHub.

### Current status (already done for you)
```bash
cd /home/user/file-organiser
git init
git branch -M main
git add .
git commit -m "Initial commit: Bash + Python file organiser for 2000+ files"
```

### STEP 1: Create the GitHub repo (2 mins)

**Option A — Via Website (recommended, since `gh` CLI not installed):**

1. Go to https://github.com/new
2. Fill in:
   - **Repository name:** `file-organiser`  (or `bash-python-file-organiser`)
   - **Description:** `Bash + Python file organiser that sorts 2,000+ downloaded files into project folders by type and date — saves ~15 mins/week`
   - **Visibility:** Public (or Private)
   - **IMPORTANT:** Leave all checkboxes UNCHECKED:
     - ❌ Do NOT add README
     - ❌ Do NOT add .gitignore
     - ❌ Do NOT add license
     - (You already have these)
3. Click **Create repository**
4. GitHub will show you a page with quick setup commands — copy the HTTPS URL, e.g. `https://github.com/YOUR_USERNAME/file-organiser.git`

**Option B — Via CLI (if you install gh):**
```bash
# Install gh: https://cli.github.com/
# Then:
gh auth login
gh repo create file-organiser --public --source=. --remote=origin --push --description "Bash + Python file organiser that sorts 2,000+ files by type/date/project, saves ~15 mins/week"
# Done! Skip to Step 3
```

### STEP 2: Add remote and push (run these exact commands)

Replace `YOUR_USERNAME` with your GitHub username.

```bash
cd /home/user/file-organiser

# 1. Set your Git identity (if not set globally)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 2. Add GitHub as remote (HTTPS)
git remote add origin https://github.com/YOUR_USERNAME/file-organiser.git

# 3. Verify remote
git remote -v

# 4. Push to GitHub
git push -u origin main
```

If using SSH (more secure, no password prompt):
```bash
git remote add origin git@github.com:YOUR_USERNAME/file-organiser.git
git push -u origin main
```

**First push will ask for credentials:**
- Username: your GitHub username
- Password: Use a **Personal Access Token (PAT)**, not your password
  - Create at: https://github.com/settings/tokens/new
  - Scope: `repo` 
  - Copy token and use as password

### STEP 3: Verify

```bash
# Check it worked
git log --oneline
# Should show: 8b35feb Initial commit...

# Open in browser
# https://github.com/YOUR_USERNAME/file-organiser
```

### STEP 4: Polish the GitHub repo (optional but recommended)

On GitHub repo page:

1. Click **Settings** > **About** (top right gear icon):
   - Add description
   - Add topics: `bash`, `python`, `file-organiser`, `automation`, `productivity`, `downloads-organizer`
   - Check "Include in homepage"

2. Add README badges (edit README.md):
```markdown
![Bash](https://img.shields.io/badge/Bash-4%2B-green)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
```

3. Enable Issues/Discussions if you want contributions

4. Create a release:
```bash
git tag v1.0.0
git push origin v1.0.0
# Then on GitHub: Releases > Draft new release > Choose v1.0.0 tag
```

### STEP 5: Future updates

After making changes:

```bash
cd /home/user/file-organiser
git add .
git commit -m "Add feature: ..."
git push
```

### Troubleshooting

**Error: remote origin already exists**
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/file-organiser.git
```

**Error: failed to push, updates were rejected**
```bash
git pull origin main --rebase
git push -u origin main
```

**Error: authentication failed**
- Use PAT not password: https://github.com/settings/tokens
- Or switch to SSH: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

**Want to rename master to main? Already done:**
```bash
git branch -M main
```

### Quick Copy-Paste (all in one)

```bash
cd ~/file-organiser
git remote add origin https://github.com/YOUR_USERNAME/file-organiser.git
git push -u origin main
```

Replace YOUR_USERNAME and you're live!

---

**Your repo is ready locally at:** `/home/user/file-organiser`
**Commit:** `8b35feb` on branch `main` with 8 files
