#!/usr/bin/env bash

# Script to sync Cline rules between three locations:
# 1. The directory where Cline expects the rules (local)
# 2. iCloud Drive for cross-device synchronisation
# 3. A git repository for version control and open-sourcing

# Default settings
DRY_RUN=false
VERBOSE=false
ALWAYS_SHOW_DIFF=true  # Always show diff by default

# Directories
ICLOUD_DIR="/Users/samm/Library/Mobile Documents/com~apple~CloudDocs/Documents/Cline/Rules"
LOCAL_DIR="/Users/samm/Documents/Cline/Rules"
GIT_DIR="/Users/samm/git/sammcj/agentic-coding/Cline/Rules"

# Files to ignore
IGNORE_PATTERNS=(
  ".vscode"
  ".DS_Store"
  ".git"
  ".gitignore"
)

# Colours
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Colour

# Display help message
show_help() {
  cat << EOF
Usage: $(basename "$0") [OPTIONS]

Synchronise Cline rules between local directory, iCloud, and git repository.

Options:
  -h, --help       Show this help message and exit
  -d, --dry-run    Show what would be done without making any changes
  -v, --verbose    Enable verbose output
  -n, --no-diff    Don't automatically show diffs (overrides verbose)
  -c, --no-colour  Disable coloured output

EOF
}

# Process command line arguments
process_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)
        show_help
        exit 0
        ;;
      -d|--dry-run)
        DRY_RUN=true
        echo -e "${YELLOW}Running in dry-run mode. No changes will be made.${NC}"
        shift
        ;;
      -v|--verbose)
        VERBOSE=true
        shift
        ;;
      -n|--no-diff)
        ALWAYS_SHOW_DIFF=false
        shift
        ;;
      -c|--no-colour)
        # Disable all colours
        RED=''
        GREEN=''
        BLUE=''
        CYAN=''
        YELLOW=''
        PURPLE=''
        BOLD=''
        NC=''
        shift
        ;;
      *)
        echo -e "${RED}Unknown option: $1${NC}"
        show_help
        exit 1
        ;;
    esac
  done
}

# Check if terminal supports colours
check_colour_support() {
  if ! test -t 1; then
    # Not a terminal, disable colours
    RED=''
    GREEN=''
    BLUE=''
    CYAN=''
    YELLOW=''
    PURPLE=''
    BOLD=''
    NC=''
  fi
}

# Verify directories exist
check_directories() {
  for dir in "$ICLOUD_DIR" "$LOCAL_DIR" "$GIT_DIR"; do
    if [ ! -d "$dir" ]; then
      echo -e "${RED}ERROR: Directory does not exist: $dir${NC}"
      exit 1
    fi
  done
}

# Execute a command or just print it in dry-run mode
execute_or_print() {
  if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}WOULD EXECUTE: $*${NC}"
  else
    if [ "$VERBOSE" = true ]; then
      echo -e "${BLUE}EXECUTING: $*${NC}"
    fi
    "$@"
  fi
}

# Show a coloured diff between two files
show_coloured_diff() {
  local file1="$1"
  local file2="$2"
  local file1_name="$3"
  local file2_name="$4"
  local recommended_direction="$5"  # "1->2" or "2->1"

  echo
  echo -e "${CYAN}${BOLD}DIFF SHOWING CHANGES:${NC}"

  # Determine which direction to show the diff based on recommendation
  if [[ "$recommended_direction" == "1->2" ]]; then
    # Option 1 recommended - file1 will replace file2
    echo -e "${CYAN}${BOLD}▶ WHAT WILL CHANGE WITH RECOMMENDED ACTION:${NC}"
    echo -e "${YELLOW}  - Lines marked with ${RED}-${YELLOW} will be ${RED}REMOVED${YELLOW} from $file2_name${NC}"
    echo -e "${YELLOW}  - Lines marked with ${GREEN}+${YELLOW} will be ${GREEN}ADDED${YELLOW} to $file2_name${NC}"
    echo -e "${BLUE}  - This shows what changes would happen when copying FROM $file1_name TO $file2_name${NC}"

    local tmp_script
    tmp_script=$(mktemp)

    cat > "$tmp_script" << 'EOF'
#!/usr/bin/env bash
diff -u "$2" "$1" | awk '
    /^---/ {print "\033[1;33m" $0 "\033[0m"; next}
    /^\+\+\+/ {print "\033[1;33m" $0 "\033[0m"; next}
    /^-/ {print "\033[1;31m" $0 "\033[0m"; next}
    /^\+/ {print "\033[1;32m" $0 "\033[0m"; next}
    /^@@ / {print "\033[1;36m" $0 "\033[0m"; next}
    {print}
'
EOF
  else
    # Option 2 recommended - file2 will replace file1
    echo -e "${CYAN}${BOLD}▶ WHAT WILL CHANGE WITH RECOMMENDED ACTION:${NC}"
    echo -e "${YELLOW}  - Lines marked with ${RED}-${YELLOW} will be ${RED}REMOVED${YELLOW} from $file1_name${NC}"
    echo -e "${YELLOW}  - Lines marked with ${GREEN}+${YELLOW} will be ${GREEN}ADDED${YELLOW} to $file1_name${NC}"
    echo -e "${BLUE}  - This shows what changes would happen when copying FROM $file2_name TO $file1_name${NC}"

    local tmp_script
    tmp_script=$(mktemp)

    cat > "$tmp_script" << 'EOF'
#!/usr/bin/env bash
diff -u "$1" "$2" | awk '
    /^---/ {print "\033[1;33m" $0 "\033[0m"; next}
    /^\+\+\+/ {print "\033[1;33m" $0 "\033[0m"; next}
    /^-/ {print "\033[1;31m" $0 "\033[0m"; next}
    /^\+/ {print "\033[1;32m" $0 "\033[0m"; next}
    /^@@ / {print "\033[1;36m" $0 "\033[0m"; next}
    {print}
'
EOF
  fi

  chmod +x "$tmp_script"

  "$tmp_script" "$file1" "$file2"

  rm -f "$tmp_script"

  echo -e "${CYAN}${BOLD}▶ END OF DIFF${NC}"
  echo # Add a blank line after the diff for readability
}

# Safely copy files from source to destination
copy_files() {
  local source_dir="$1"
  local dest_dir="$2"

  echo -e "${CYAN}Checking for files to copy from $source_dir to $dest_dir...${NC}"

  # Build exclusion pattern
  local exclusion_args=()
  for pattern in "${IGNORE_PATTERNS[@]}"; do
    exclusion_args+=(-not -path "${source_dir}/${pattern}*")
  done

  # Find all MD files in source_dir that should be copied
  while IFS= read -r file; do
    # file is the full path to the source file, e.g., /path/to/source_dir/subdir/name.md
    # source_dir is /path/to/source_dir
    local relative_path="${file#$source_dir/}" # e.g., subdir/name.md
    local dest_file="${dest_dir}/${relative_path}"
    local dest_file_dir
    dest_file_dir=$(dirname "$dest_file")

    # Ensure the destination directory exists
    if [ ! -d "$dest_file_dir" ]; then
      execute_or_print mkdir -p "$dest_file_dir"
    fi

    # Check if destination already exists
    if [ -f "$dest_file" ]; then
      # Check if content is identical
      if cmp -s "$file" "$dest_file"; then
        [ "$VERBOSE" = true ] && echo -e "${GREEN}Files already identical: $relative_path${NC}"
        continue
      else
        # Files exist in both locations but have different content
        echo -e "${YELLOW}Files have different content: $relative_path${NC}"
        if [ "$DRY_RUN" = true ]; then
          echo -e "${YELLOW}WOULD REPLACE: $dest_file with copy of $file${NC}"
        else
          echo -e "${BLUE}Automatically replacing $dest_file with copy of $file (source is master).${NC}"
          execute_or_print cp "$file" "$dest_file"
          echo -e "${GREEN}Replaced with copy: $relative_path${NC}"
        fi
      fi
    else
      # Destination file doesn't exist, simply copy file
      echo -e "${GREEN}Copying file: $relative_path${NC}"
      execute_or_print mkdir -p "$(dirname "$dest_file")" # Ensure directory exists
      execute_or_print cp "$file" "$dest_file"
    fi
  done < <(find "$source_dir" -type f -name "*.md" "${exclusion_args[@]}" 2>/dev/null)
}

# Sync files between two directories with confirmation
sync_directories() {
  local source_dir="$1"
  local dest_dir="$2"
  local source_name="$3"
  local dest_name="$4"

  echo -e "${CYAN}Checking for files in $source_name to sync with $dest_name...${NC}"

  # Build exclusion pattern for find, similar to copy_files
  local find_exclusion_args=()
  for pattern in "${IGNORE_PATTERNS[@]}"; do
    find_exclusion_args+=(-not -path "${source_dir}/${pattern}*")
  done

  # Find all MD files in source_dir
  while IFS= read -r file; do
    # 'file' is the full path to the source file from find
    local relative_path="${file#$source_dir/}"
    local dest_file="${dest_dir}/${relative_path}"
    local dest_file_dir
    dest_file_dir=$(dirname "$dest_file")

    # Ensure the destination directory exists before any operation
    # It's important to do this even if the source file might not be copied,
    # as a differing file might be copied *from* destination later if it's newer.
    # However, for this specific loop (source -> dest), mkdir is needed before cp.
    if [ ! -d "$dest_file_dir" ]; then
        execute_or_print mkdir -p "$dest_file_dir"
    fi

    if [ ! -f "$dest_file" ]; then
      echo -e "${YELLOW}File '$relative_path' exists in $source_name but not in $dest_name.${NC}"
      if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}WOULD COPY: '$relative_path' FROM $source_name TO $dest_name${NC}"
      else
        echo -e "${BLUE}Automatically copying '$relative_path' FROM $source_name TO $dest_name.${NC}"
        execute_or_print mkdir -p "$(dirname "$dest_file")" # Ensure directory exists
        execute_or_print cp "$file" "$dest_file"
        echo -e "${GREEN}Copied '$relative_path' FROM $source_name TO $dest_name.${NC}"
      fi
    elif ! cmp -s "$file" "$dest_file"; then
      echo -e "${RED}File '$relative_path' differs between $source_name and $dest_name.${NC}"

      # Get modification times and format them
      local src_date dest_date
      src_date=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$file")
      dest_date=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$dest_file")

      echo -e "${BLUE}$source_name file date: $src_date${NC}"
      echo -e "${BLUE}$dest_name file date: $dest_date${NC}"

      # Determine which file is newer and set recommended direction
      local source_newer=false
      if [[ $(stat -f "%m" "$file") -gt $(stat -f "%m" "$dest_file") ]]; then
        echo -e "${GREEN}$source_name version is newer ($(date -r "$file" "+%H:%M:%S")).${NC}"
        source_newer=true
        recommended_direction="1->2"
      else
        echo -e "${GREEN}$dest_name version is newer ($(date -r "$dest_file" "+%H:%M:%S")).${NC}"
        source_newer=false
        recommended_direction="2->1"
      fi

      # Show diff if requested or in verbose mode
      if [ "$ALWAYS_SHOW_DIFF" = true ] || [ "$VERBOSE" = true ]; then
        show_coloured_diff "$file" "$dest_file" "$source_name" "$dest_name" "$recommended_direction"
      else
        echo -e "${YELLOW}Use --verbose or --always-diff to see detailed differences${NC}"
      fi

      if [ "$DRY_RUN" = true ]; then
        if [ "$source_newer" = true ]; then
            echo -e "${YELLOW}WOULD COPY newer file '$relative_path' FROM $source_name TO $dest_name.${NC}"
        else
            echo -e "${YELLOW}WOULD COPY newer file '$relative_path' FROM $dest_name TO $source_name.${NC}"
        fi
      else
        if [ "$source_newer" = true ]; then
          echo -e "${BLUE}Automatically copying newer file '$relative_path' FROM $source_name TO $dest_name.${NC}"
          execute_or_print mkdir -p "$(dirname "$dest_file")" # Ensure directory exists
          execute_or_print cp "$file" "$dest_file"
          echo -e "${GREEN}Copied newer '$relative_path' FROM $source_name TO $dest_name.${NC}"
        else
          echo -e "${BLUE}Automatically copying newer file '$relative_path' FROM $dest_name TO $source_name.${NC}"
          execute_or_print mkdir -p "$(dirname "$file")" # Ensure directory exists
          execute_or_print cp "$dest_file" "$file"
          echo -e "${GREEN}Copied newer '$relative_path' FROM $dest_name TO $source_name.${NC}"
        fi
      fi
    # Optional: If files are identical and already exist, verbose log
    # elif [ "$VERBOSE" = true ]; then
    #   echo -e "${GREEN}File '$relative_path' is identical in $source_name and $dest_name.${NC}"
    fi
  done < <(find "$source_dir" -type f -name "*.md" "${find_exclusion_args[@]}" 2>/dev/null)
}

# Main function
main() {
  check_colour_support
  process_args "$@"
  check_directories

  # Step 1: Copy files from iCloud to local (where Cline expects the rules)
  copy_files "$ICLOUD_DIR" "$LOCAL_DIR"

  # Step 2: Sync from local to iCloud (if any local-only files exist)
  sync_directories "$LOCAL_DIR" "$ICLOUD_DIR" "local directory" "iCloud"

  # Step 3: Sync between iCloud and git repository
  sync_directories "$ICLOUD_DIR" "$GIT_DIR" "iCloud" "git repository"
  sync_directories "$GIT_DIR" "$ICLOUD_DIR" "git repository" "iCloud"

  echo -e "${GREEN}All operations completed.${NC}"
}

# Run the script
main "$@"
