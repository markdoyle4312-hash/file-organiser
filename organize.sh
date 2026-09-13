#!/bin/bash
# File Organiser - Bash Wrapper
# Sorts 2000+ files into project folders by type and date
# Saves ~15 minutes a week
# Usage: ./organize.sh [--dry-run] [--source ~/Downloads] [--dest ~/Organized]

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/organizer.py"
CONFIG_FILE="$SCRIPT_DIR/config.yaml"
LOG_DIR="$HOME/Organized/_logs"

# Defaults
SOURCE="$HOME/Downloads"
DEST="$HOME/Organized"
DRY_RUN=""
VERBOSE=""
MODE="all"
ACTION=""
RECURSIVE=""
LIMIT=""

print_banner() {
    echo -e "${BLUE}"
    cat << "EOF"
  _____ _ _        ___                        _               
 |  ___(_) | ___  / _ \ _ __ __ _  __ _ _ __ (_)___  ___ _ __ 
 | |_  | | |/ _ \| | | | '__/ _` |/ _` | '_ \| / __|/ _ \ '__|
 |  _| | | |  __/| |_| | | | (_| | (_| | | | | \__ \  __/ |   
 |_|   |_|_|\___| \___/|_|  \__, |\__,_|_| |_|_|___/\___|_|   
                            |___/                             
  Saves ~15 mins/week by auto-sorting 2000+ files
EOF
    echo -e "${NC}"
}

print_help() {
    print_banner
    echo -e "${CYAN}USAGE:${NC}"
    echo "  ./organize.sh [OPTIONS]"
    echo ""
    echo -e "${CYAN}OPTIONS:${NC}"
    echo "  -s, --source PATH     Source folder (default: ~/Downloads)"
    echo "  -d, --dest PATH       Destination folder (default: ~/Organized)"
    echo "  -m, --by MODE         Organize by: type, date, project, all (default: all)"
    echo "  -n, --dry-run         Preview without moving files"
    echo "  -c, --copy            Copy files instead of moving"
    echo "  -r, --recursive       Scan subfolders recursively"
    echo "  -v, --verbose         Verbose output"
    echo "  --limit N             Limit files processed (for testing)"
    echo "  --setup-cron          Setup weekly cron job (Mondays 9am)"
    echo "  --install             Install dependencies"
    echo "  -h, --help            Show this help"
    echo ""
    echo -e "${CYAN}EXAMPLES:${NC}"
    echo "  ./organize.sh                          # Organize ~/Downloads -> ~/Organized"
    echo "  ./organize.sh --dry-run --verbose      # Preview what will happen"
    echo "  ./organize.sh --by project             # Only sort by project"
    echo "  ./organize.sh --source ./test --dest ./out --copy"
    echo "  ./organize.sh --setup-cron             # Auto-run every Monday"
    echo ""
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ python3 not found. Please install Python 3.8+${NC}"
        exit 1
    fi
    
    PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo -e "${GREEN}✓ Python $PY_VER found${NC}"
}

install_deps() {
    echo -e "${BLUE}📦 Checking dependencies...${NC}"
    check_python
    
    # Check if yaml is available, if not offer to install
    if ! python3 -c "import yaml" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  PyYAML not found (optional, for config.yaml). Installing...${NC}"
        pip3 install --user pyyaml 2>/dev/null || pip install --user pyyaml 2>/dev/null || echo -e "${YELLOW}Could not auto-install pyyaml, using JSON config instead${NC}"
    else
        echo -e "${GREEN}✓ PyYAML available${NC}"
    fi
    
    chmod +x "$PYTHON_SCRIPT"
    chmod +x "$SCRIPT_DIR/organize.sh"
    
    echo -e "${GREEN}✅ Setup complete!${NC}"
}

setup_cron() {
    CRON_CMD="0 9 * * 1 $SCRIPT_DIR/organize.sh --source $HOME/Downloads --dest $HOME/Organized >> $LOG_DIR/cron.log 2>&1"
    
    echo -e "${BLUE}⏰ Setting up weekly cron job (Mondays 9am)...${NC}"
    echo "Command: $CRON_CMD"
    
    # Check if already exists
    if crontab -l 2>/dev/null | grep -q "organize.sh"; then
        echo -e "${YELLOW}⚠️  Cron job already exists. Current crontab:${NC}"
        crontab -l | grep organize.sh
        read -p "Replace it? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted."
            return
        fi
        # Remove old
        crontab -l | grep -v "organize.sh" | crontab -
    fi
    
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    
    echo -e "${GREEN}✅ Cron job installed!${NC}"
    echo -e "   Runs every Monday at 9am. Check with: ${CYAN}crontab -l${NC}"
    echo -e "   Logs at: ${CYAN}$LOG_DIR/cron.log${NC}"
}

count_files() {
    local dir="$1"
    if [ -d "$dir" ]; then
        find "$dir" -maxdepth 1 -type f | wc -l | tr -d ' '
    else
        echo "0"
    fi
}

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--source)
            SOURCE="$2"
            shift 2
            ;;
        -d|--dest)
            DEST="$2"
            shift 2
            ;;
        -m|--by)
            MODE="$2"
            shift 2
            ;;
        -n|--dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        -c|--copy)
            ACTION="--copy"
            shift
            ;;
        --move)
            ACTION="--move"
            shift
            ;;
        -r|--recursive)
            RECURSIVE="--recursive"
            shift
            ;;
        -v|--verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --limit)
            LIMIT="--limit $2"
            shift 2
            ;;
        --setup-cron)
            setup_cron
            exit 0
            ;;
        --install)
            install_deps
            exit 0
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_help
            exit 1
            ;;
    esac
done

# Main execution
print_banner

check_python

# Expand paths
SOURCE_EXPANDED=$(eval echo "$SOURCE")
DEST_EXPANDED=$(eval echo "$DEST")

echo -e "${CYAN}📁 Source:${NC} $SOURCE_EXPANDED ($(count_files "$SOURCE_EXPANDED") files)"
echo -e "${CYAN}📁 Dest:${NC}   $DEST_EXPANDED"
echo -e "${CYAN}🔧 Mode:${NC}   $MODE | $ACTION ${DRY_RUN:-live}"

if [ ! -d "$SOURCE_EXPANDED" ]; then
    echo -e "${RED}❌ Source folder not found: $SOURCE_EXPANDED${NC}"
    echo -e "${YELLOW}Creating test folder with sample files? Run: ./organize.sh --install && python3 demo.py${NC}"
    exit 1
fi

# Warning for large operations
FILE_COUNT=$(count_files "$SOURCE_EXPANDED")
if [ "$FILE_COUNT" -gt 1000 ] && [ -z "$DRY_RUN" ]; then
    echo -e "${YELLOW}⚠️  About to organize $FILE_COUNT files. This will MOVE files (not copy).${NC}"
    echo -e "${YELLOW}   Run with --dry-run first to preview, or --copy to keep originals.${NC}"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}💡 Tip: ./organize.sh --dry-run --verbose${NC}"
        exit 0
    fi
fi

# Ensure log dir
mkdir -p "$DEST_EXPANDED/_logs" 2>/dev/null || true

# Build python command
PY_CMD="python3 \"$PYTHON_SCRIPT\" --source \"$SOURCE_EXPANDED\" --dest \"$DEST_EXPANDED\" --by $MODE $ACTION $DRY_RUN $VERBOSE $RECURSIVE $LIMIT"

echo -e "${BLUE}🚀 Running organizer...${NC}\n"

# Time the execution
START_TIME=$(date +%s)

eval $PY_CMD
EXIT_CODE=$?

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo -e "\n${GREEN}⏱️  Finished in ${DURATION}s${NC}"

if [ $EXIT_CODE -eq 0 ] && [ -z "$DRY_RUN" ]; then
    echo -e "${GREEN}✨ Done! Your Downloads is now organized.${NC}"
    echo -e "${CYAN}📂 Check: $DEST_EXPANDED${NC}"
    
    # macOS/Linux notification if available
    if command -v osascript &> /dev/null; then
        osascript -e "display notification \"Organized $FILE_COUNT files in ${DURATION}s\" with title \"File Organiser ✅\""
    elif command -v notify-send &> /dev/null; then
        notify-send "File Organiser ✅" "Organized $FILE_COUNT files in ${DURATION}s"
    fi
elif [ $EXIT_CODE -eq 0 ] && [ -n "$DRY_RUN" ]; then
    echo -e "${YELLOW}👀 This was a DRY-RUN. No files moved. Run without --dry-run to organize.${NC}"
else
    echo -e "${RED}❌ Organizer failed with code $EXIT_CODE${NC}"
    exit $EXIT_CODE
fi
