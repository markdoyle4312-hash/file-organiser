#!/usr/bin/env bash
#
# File Organiser — Bash wrapper around organizer.py
#
# Sorts a downloads folder into a clean, searchable archive by type, date
# and project. Run with no arguments to organise ~/Downloads into
# ~/Organized; use --dry-run first to preview.
#
# Usage: ./organize.sh [OPTIONS]

# ---------------------------------------------------------------------------
# Colours (only when writing to a terminal)
# ---------------------------------------------------------------------------
if [[ -t 1 ]]; then
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    YELLOW='\033[1;33m'
    RED='\033[0;31m'
    CYAN='\033[0;36m'
    NC='\033[0m'
else
    GREEN='' BLUE='' YELLOW='' RED='' CYAN='' NC=''
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/organizer.py"
CONFIG_FILE="$SCRIPT_DIR/config.yaml"

# ---------------------------------------------------------------------------
# Defaults (overridable via command line)
# ---------------------------------------------------------------------------
SOURCE="$HOME/Downloads"
DEST="$HOME/Organized"
MODE="all"
ACTION=""
DRY_RUN=""
VERBOSE=""
RECURSIVE=""
LIMIT=""

print_help() {
    cat << EOF
${CYAN}USAGE:${NC}
  ./organize.sh [OPTIONS]

${CYAN}OPTIONS:${NC}
  -s, --source PATH     Source folder (default: ~/Downloads)
  -d, --dest PATH       Destination folder (default: ~/Organized)
  -m, --by MODE         Organise by: type, date, project, all (default: all)
  -n, --dry-run         Preview without moving or creating anything
  -c, --copy            Copy files instead of moving them
  -r, --recursive       Scan subfolders recursively
  -v, --verbose         Show every file and its destination
      --limit N         Process only N files (useful for testing)
      --setup-cron      Install a weekly cron job (Mondays 9am)
      --install         Check and install dependencies
  -h, --help            Show this help

${CYAN}EXAMPLES:${NC}
  ./organize.sh                              # Organise ~/Downloads -> ~/Organized
  ./organize.sh --dry-run --verbose          # Preview what will happen
  ./organize.sh --by project                 # Sort by project only
  ./organize.sh --source ./test --dest ./out --copy
  ./organize.sh --setup-cron                 # Auto-run every Monday
EOF
}

check_python() {
    if ! command -v python3 >/dev/null 2>&1; then
        printf '%b\n' "${RED}error: python3 not found (Python 3.8+ required)${NC}"
        exit 1
    fi
    local py_ver
    py_ver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    printf '%b\n' "${GREEN}python3 ${py_ver} found${NC}"
}

install_deps() {
    printf '%b\n' "${BLUE}Checking dependencies...${NC}"
    check_python

    if ! python3 -c "import yaml" >/dev/null 2>&1; then
        printf '%b\n' "${YELLOW}PyYAML is not installed; the built-in config parser will be used.${NC}"
        printf '%b\n' "${YELLOW}(Optional: pip3 install --user pyyaml)${NC}"
    else
        printf '%b\n' "${GREEN}PyYAML available${NC}"
    fi

    chmod +x "$PYTHON_SCRIPT" 2>/dev/null || true
    chmod +x "$SCRIPT_DIR/organize.sh" 2>/dev/null || true
    printf '%b\n' "${GREEN}Setup complete.${NC}"
}

setup_cron() {
    if ! command -v crontab >/dev/null 2>&1; then
        printf '%b\n' "${RED}error: 'crontab' not found — cron is not available on this system${NC}"
        return 1
    fi

    local log_dir="${HOME}/Organized/_logs"
    local cron_line="0 9 * * 1 \"$SCRIPT_DIR/organize.sh\" --source \"$HOME/Downloads\" --dest \"$HOME/Organized\" >> \"$log_dir/cron.log\" 2>&1"

    printf '%b\n' "${BLUE}Setting up weekly cron job (Mondays 9am)...${NC}"
    printf 'Command: %s\n' "$cron_line"

    if crontab -l 2>/dev/null | grep -q "organize.sh"; then
        printf '%b\n' "${YELLOW}A cron job already exists:${NC}"
        crontab -l 2>/dev/null | grep "organize.sh"
        if [[ -t 0 ]]; then
            read -r -p "Replace it? (y/N) " -n 1 REPLY
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Aborted."
                return 0
            fi
        fi
        crontab -l 2>/dev/null | grep -v "organize.sh" | crontab -
    fi

    (crontab -l 2>/dev/null; echo "$cron_line") | crontab -
    printf '%b\n' "${GREEN}Cron job installed.${NC}"
    printf '%b\n' "Runs every Monday at 9am. Check with: ${CYAN}crontab -l${NC}"
    printf '%b\n' "Logs at: ${CYAN}$log_dir/cron.log${NC}"
}

count_files() {
    local dir="$1"
    if [[ -d "$dir" ]]; then
        find "$dir" -maxdepth 1 -type f ! -name '.*' 2>/dev/null | wc -l | tr -d ' '
    else
        echo "0"
    fi
}

confirm_large_run() {
    local count="$1" verb
    if [[ -n "$ACTION" ]]; then verb="copy"; else verb="move"; fi
    if [[ "$count" -gt 1000 ]] && [[ -z "$DRY_RUN" ]]; then
        printf '%b\n' "${YELLOW}About to $verb $count files.${NC}"
        printf '%b\n' "${YELLOW}Run with --dry-run first to preview, or --copy to keep the originals.${NC}"
        if [[ -t 0 ]]; then
            read -r -p "Continue? (y/N) " -n 1 REPLY
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                printf '%b\n' "${BLUE}Tip: ./organize.sh --dry-run --verbose${NC}"
                exit 0
            fi
        else
            printf '%b\n' "${YELLOW}Non-interactive shell: continuing (use --dry-run to preview).${NC}"
        fi
    fi
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--source)    SOURCE="$2"; shift 2 ;;
        -d|--dest)      DEST="$2"; shift 2 ;;
        -m|--by)        MODE="$2"; shift 2 ;;
        -n|--dry-run)   DRY_RUN="--dry-run"; shift ;;
        -c|--copy)      ACTION="--copy"; shift ;;
        --move)         ACTION=""; shift ;;
        -r|--recursive) RECURSIVE="--recursive"; shift ;;
        -v|--verbose)   VERBOSE="--verbose"; shift ;;
        --limit)        LIMIT="--limit $2"; shift 2 ;;
        --setup-cron)   setup_cron; exit $? ;;
        --install)      install_deps; exit 0 ;;
        -h|--help)      print_help; exit 0 ;;
        *)  printf '%b\n' "${RED}Unknown option: $1${NC}"
            print_help
            exit 1 ;;
    esac
done

# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------
check_python

# Expand a leading ~.
SOURCE="$(printf '%s' "$SOURCE" | sed "s#^~/#$HOME/#")"
DEST="$(printf '%s' "$DEST" | sed "s#^~/#$HOME/#")"

if [[ ! -d "$SOURCE" ]]; then
    printf '%b\n' "${RED}error: source folder not found: $SOURCE${NC}"
    printf '%b\n' "${YELLOW}Create a test folder with: python3 demo.py${NC}"
    exit 1
fi

# Warn before large, destructive operations.
FILE_COUNT="$(count_files "$SOURCE")"
confirm_large_run "$FILE_COUNT"

MODE_VERB="move"; [[ -n "$ACTION" ]] && MODE_VERB="copy"
MODE_STATE="live"; [[ -n "$DRY_RUN" ]] && MODE_STATE="dry-run"
printf '%b\n' "${CYAN}Source:${NC}      $SOURCE ($FILE_COUNT files at top level)"
printf '%b\n' "${CYAN}Destination:${NC} $DEST"
printf '%b\n' "${CYAN}Mode:${NC}        $MODE | $MODE_VERB | $MODE_STATE"
echo

printf '%b\n' "${BLUE}Running organiser...${NC}"
echo

START_TIME="$(date +%s)"

# shellcheck disable=SC2086
python3 "$PYTHON_SCRIPT" \
    --source "$SOURCE" \
    --dest "$DEST" \
    --by "$MODE" \
    --config "$CONFIG_FILE" \
    $ACTION $DRY_RUN $VERBOSE $RECURSIVE $LIMIT
EXIT_CODE=$?

END_TIME="$(date +%s)"
DURATION=$((END_TIME - START_TIME))

if [[ $EXIT_CODE -eq 0 ]]; then
    if [[ -n "$DRY_RUN" ]]; then
        printf '%b\n' "${YELLOW}Dry run: no files were moved or created.${NC}"
    else
        printf '%b\n' "${GREEN}Done. Files organised in: $DEST${NC}"
        if command -v osascript >/dev/null 2>&1; then
            osascript -e "display notification \"Organised $FILE_COUNT files in ${DURATION}s\" with title \"File Organiser\""
        elif command -v notify-send >/dev/null 2>&1; then
            notify-send "File Organiser" "Organised $FILE_COUNT files in ${DURATION}s"
        fi
    fi
    printf '%b\n' "${GREEN}Finished in ${DURATION}s${NC}"
else
    printf '%b\n' "${RED}The organiser reported errors (exit code $EXIT_CODE).${NC}"
    exit "$EXIT_CODE"
fi
