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

# Safely create hardlinks from source to destination
create_hardlinks() {
  local source_dir="$1"
  local dest_dir="$2"

  echo -e "${CYAN}Checking for files to hardlink from $source_dir to $dest_dir...${NC}"

  # Build exclusion pattern
  local exclusion_args=()
  for pattern in "${IGNORE_PATTERNS[@]}"; do
    exclusion_args+=(-not -path "${source_dir}/${pattern}*")
  done

  # Find all MD files in source_dir that should be linked
  while IFS= read -r file; do
    local filename
    filename=$(basename "$file")
    local dest_file="${dest_dir}/${filename}"

    # Check if destination already exists
    if [ -f "$dest_file" ]; then
      # Compare inodes to check if they're already hardlinked
      local src_inode dest_inode
      src_inode=$(stat -f "%i" "$file")
      dest_inode=$(stat -f "%i" "$dest_file")

      if [ "$src_inode" = "$dest_inode" ]; then
        [ "$VERBOSE" = true ] && echo -e "${GREEN}Already hardlinked: $filename${NC}"
        continue
      else
        # Files exist in both locations but are not hardlinked
        # First check if content is identical
        if cmp -s "$file" "$dest_file"; then
          echo -e "${YELLOW}Files have identical content but are not hardlinked: $filename${NC}"
          if [ "$DRY_RUN" = true ]; then
            echo -e "${YELLOW}WOULD REPLACE: $dest_file with hardlink to $file${NC}"
          else
            read -p "Replace $dest_file with hardlink to $file? (y/n) " answer
            if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
              execute_or_print rm "$dest_file"
              execute_or_print ln "$file" "$dest_file"
              echo -e "${GREEN}Replaced with hardlink: $filename${NC}"
            else
              echo -e "${YELLOW}Skipped hardlinking: $filename${NC}"
            fi
          fi
        else
          # Files have different content
          echo -e "${RED}WARNING: Files have different content: $filename${NC}"

          # Display file dates
          local src_date dest_date
          src_date=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$file")
          dest_date=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$dest_file")

          echo -e "${BLUE}Source file date: $src_date${NC}"
          echo -e "${BLUE}Destination file date: $dest_date${NC}"

          # Determine which file is newer
          local source_newer=false
          if [[ $(stat -f "%m" "$file") -gt $(stat -f "%m" "$dest_file") ]]; then
            echo -e "${GREEN}Source version is newer ($(date -r "$file" "+%H:%M:%S")).${NC}"
            source_newer=true
            recommended_direction="1->2"
          else
            echo -e "${GREEN}Destination version is newer ($(date -r "$dest_file" "+%H:%M:%S")).${NC}"
            source_newer=false
            recommended_direction="2->1"
          fi

          # Always show diff if ALWAYS_SHOW_DIFF is true
          if [ "$ALWAYS_SHOW_DIFF" = true ] || [ "$VERBOSE" = true ]; then
            show_coloured_diff "$file" "$dest_file" "Source ($source_dir)" "Destination ($dest_dir)" "$recommended_direction"
          fi

          if [ "$DRY_RUN" = true ]; then
            echo -e "${YELLOW}WOULD ASK which file to keep and create hardlink${NC}"
          else
            echo -e "${CYAN}${BOLD}OPTIONS:${NC}"
            if [ "$source_newer" = true ]; then
              echo -e "${CYAN}1) Replace destination with source (FROM $source_dir TO $dest_dir) ${GREEN}[NEWER]${NC}"
              echo -e "${CYAN}2) Keep destination and skip hardlinking this file ${RED}[OLDER]${NC}"
              echo -e "${GREEN}Recommendation: Option 1 (use newer version from source)${NC}"
              recommended_option="1"
            else
              echo -e "${CYAN}1) Replace destination with source (FROM $source_dir TO $dest_dir) ${RED}[OLDER]${NC}"
              echo -e "${CYAN}2) Keep destination and skip hardlinking this file ${GREEN}[NEWER]${NC}"
              echo -e "${GREEN}Recommendation: Option 2 (keep newer version in destination)${NC}"
              recommended_option="2"
            fi
            echo -e "${CYAN}3) Skip this file entirely${NC}"

            read -p "Choose option [1-3] (recommended: $recommended_option): " choice

            case "$choice" in
              1)
                execute_or_print rm "$dest_file"
                execute_or_print ln "$file" "$dest_file"
                echo -e "${GREEN}Copied FROM $source_dir TO $dest_dir and created hardlink.${NC}"
                ;;
              2)
                echo -e "${YELLOW}Kept destination file: $filename${NC}"
                ;;
              *)
                echo -e "${YELLOW}Skipped hardlinking: $filename${NC}"
                ;;
            esac
          fi
        fi
      fi
    else
      # Destination file doesn't exist, simply create hardlink
      echo -e "${GREEN}Creating hardlink for: $filename${NC}"
      execute_or_print ln "$file" "$dest_file"
    fi
  done < <(find "$source_dir" -type f -name "*.md" "${exclusion_args[@]}" 2>/dev/null)
}

# Sync files between two directories with confirmation
sync_directories() {
  local source_dir="$1"
  local dest_dir="$2"
  local source_name="$3"
  local dest_name="$4"

  echo -e "${CYAN}Checking for files in $source_name that are missing from $dest_name...${NC}"

  # Files that exist in source but not in destination
  for file in "$source_dir"/*.md; do
    [ -f "$file" ] || continue

    local filename
    filename=$(basename "$file")
    local dest_file="${dest_dir}/${filename}"

    # Skip ignored files
    for pattern in "${IGNORE_PATTERNS[@]}"; do
      if [[ "$filename" == *"$pattern"* ]]; then
        continue 2
      fi
    done

    if [ ! -f "$dest_file" ]; then
      echo -e "${YELLOW}File '$filename' exists in $source_name but not in $dest_name.${NC}"
      if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}WOULD COPY: '$filename' FROM $source_name TO $dest_name${NC}"
      else
        read -p "Copy FROM $source_name TO $dest_name? (y/n) " answer
        if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
          execute_or_print cp "$file" "$dest_file"
          echo -e "${GREEN}Copied '$filename' FROM $source_name TO $dest_name.${NC}"
        else
          echo -e "${YELLOW}Skipped copying '$filename'.${NC}"
        fi
      fi
    elif ! cmp -s "$file" "$dest_file"; then
      echo -e "${RED}File '$filename' differs between $source_name and $dest_name.${NC}"

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
        echo -e "${YELLOW}WOULD ASK which version to copy.${NC}"
      else
        echo -e "${CYAN}${BOLD}OPTIONS:${NC}"
        # Always be consistent with option order but label which is newer
        if [ "$source_newer" = true ]; then
          echo -e "${CYAN}1) Copy FROM $source_name TO $dest_name ${GREEN}[NEWER]${NC}"
          echo -e "${CYAN}2) Copy FROM $dest_name TO $source_name ${RED}[OLDER]${NC}"
          echo -e "${GREEN}Recommendation: Option 1 (copy the newer $source_name version to $dest_name)${NC}"
          recommended_option="1"
        else
          echo -e "${CYAN}1) Copy FROM $source_name TO $dest_name ${RED}[OLDER]${NC}"
          echo -e "${CYAN}2) Copy FROM $dest_name TO $source_name ${GREEN}[NEWER]${NC}"
          echo -e "${GREEN}Recommendation: Option 2 (copy the newer $dest_name version to $source_name)${NC}"
          recommended_option="2"
        fi
        echo -e "${CYAN}3) Skip this file${NC}"

        read -p "Choose option [1-3] (recommended: $recommended_option): " choice

        case "$choice" in
          1)
            execute_or_print cp "$file" "$dest_file"
            echo -e "${GREEN}Copied FROM $source_name TO $dest_name.${NC}"
            ;;
          2)
            execute_or_print cp "$dest_file" "$file"
            echo -e "${GREEN}Copied FROM $dest_name TO $source_name.${NC}"
            ;;
          *)
            echo -e "${YELLOW}Skipped syncing '$filename'.${NC}"
            ;;
        esac
      fi
    fi
  done
}

# Main function
main() {
  check_colour_support
  process_args "$@"
  check_directories

  # Step 1: Create hardlinks from iCloud to local (where Cline expects the rules)
  create_hardlinks "$ICLOUD_DIR" "$LOCAL_DIR"

  # Step 2: Sync from local to iCloud (if any local-only files exist)
  sync_directories "$LOCAL_DIR" "$ICLOUD_DIR" "local directory" "iCloud"

  # Step 3: Sync between iCloud and git repository
  sync_directories "$ICLOUD_DIR" "$GIT_DIR" "iCloud" "git repository"
  sync_directories "$GIT_DIR" "$ICLOUD_DIR" "git repository" "iCloud"

  echo -e "${GREEN}All operations completed.${NC}"
}

# Run the script
main "$@"
