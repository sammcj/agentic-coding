#!/usr/bin/env bash

# Hardlinks Cline rules from iCloud to local storage due to Cline bug https://github.com/cline/cline/issues/3092

ICLOUD_DIR="/Users/samm/Library/Mobile Documents/com~apple~CloudDocs/Documents/Cline/Rules"
LOCAL_DIR="/Users/samm/Documents/Cline/Rules"
GIT_DIR="/Users/samm/git/sammcj/agentic-coding/Cline/Rules"
IGNORE_PATTERNS=(
  ".vscode"
  ".DS_Store"
  ".git"
  ".gitignore"
)

# Generate exclusion arguments for find
EXCLUSIONS=""
for pattern in "${IGNORE_PATTERNS[@]}"; do
    EXCLUSIONS="$EXCLUSIONS -not -path \"$ICLOUD_DIR/$pattern/*\""
done

# Print out any files that exist in the local directory, but not in the iCloud directory
for file in "$LOCAL_DIR"/*; do
  filename=$(basename "$file")
  if [ ! -e "$ICLOUD_DIR/$filename" ]; then
    echo "WARNING: File '$filename' exists in local directory but not in iCloud directory."
    # ask the user if they want to copy the file to iCloud
    read -p "Do you want to copy it to iCloud? (y/n) " answer
    if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
      # turn on echoing for debugging
      set -x
        cp "$file" "$ICLOUD_DIR/"
        echo "Copied '$filename' to iCloud directory."
        # turn off echoing
        set +x
    else
        echo "Skipped copying '$filename'."
    fi
  fi
done

# Execute find with properly quoted exclusions
# shellcheck disable=SC2086
echo "Hardlinking files from iCloud directory to local directory..."
eval find \"$ICLOUD_DIR\" -type f -name \'*.md\' $EXCLUSIONS -exec ln \"{}\" \"$LOCAL_DIR\" \\\; 2>/dev/null
echo "Done"

# Offer to copy files from the ICLOUD_DIR to the GIT_DIR, listing the difference in file names present in the two directories
for file in "$ICLOUD_DIR"/*; do
  filename=$(basename "$file")
  if [ ! -e "$GIT_DIR/$filename" ]; then
    echo "WARNING: File '$filename' exists in iCloud directory but not in git directory."
    # ask the user if they want to copy the file to git
    read -p "Do you want to copy it to git? (y/n) " answer
    if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
      set -x
        cp "$file" "$GIT_DIR/"
        echo "Copied '$filename' to git directory."
        set +x
    else
        echo "Skipped copying '$filename'."
    fi
  fi
done
