#!/usr/bin/env bash
set -euo pipefail

# Render Wisdom PDF
# Converts an extract-wisdom markdown analysis into a styled PDF
# using pandoc + weasyprint with a custom CSS stylesheet.
#
# Usage: bash scripts/render_pdf.sh <markdown-file> [output.pdf]
#
# Dependencies: pandoc, weasyprint
# Both installable via: brew install pandoc weasyprint

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd -P)"
CSS_FILE="${SKILL_DIR}/styles/wisdom-pdf.css"

usage() {
    echo "Usage: $0 <markdown-file> [output.pdf]"
    echo ""
    echo "Converts an extract-wisdom markdown analysis into a styled PDF."
    echo ""
    echo "Arguments:"
    echo "  markdown-file   Path to the .md file to render"
    echo "  output.pdf      Optional output path (defaults to same name with .pdf extension)"
    echo ""
    echo "Options:"
    echo "  --css <file>    Use a custom CSS stylesheet instead of the default"
    echo "  --open          Open the PDF after rendering (macOS only)"
    echo "  --help          Show this help message"
    echo ""
    echo "Dependencies: pandoc, weasyprint"
    echo "Install with: brew install pandoc weasyprint"
}

check_dependencies() {
    local missing=()

    if ! command -v pandoc &>/dev/null; then
        missing+=("pandoc")
    fi

    if ! command -v weasyprint &>/dev/null; then
        missing+=("weasyprint")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "Error: Missing required dependencies: ${missing[*]}" >&2
        echo "Install with: brew install ${missing[*]}" >&2
        exit 1
    fi
}

main() {
    local input_file=""
    local output_file=""
    local css_file="$CSS_FILE"
    local open_after=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                usage
                exit 0
                ;;
            --css)
                if [[ -z "${2:-}" ]]; then
                    echo "Error: --css requires a file path argument" >&2
                    exit 1
                fi
                css_file="$2"
                shift 2
                ;;
            --open)
                open_after=true
                shift
                ;;
            -*)
                echo "Error: Unknown option: $1" >&2
                usage >&2
                exit 1
                ;;
            *)
                if [[ -z "$input_file" ]]; then
                    input_file="$1"
                elif [[ -z "$output_file" ]]; then
                    output_file="$1"
                else
                    echo "Error: Too many arguments" >&2
                    usage >&2
                    exit 1
                fi
                shift
                ;;
        esac
    done

    # Validate input
    if [[ -z "$input_file" ]]; then
        echo "Error: No input file specified" >&2
        usage >&2
        exit 1
    fi

    if [[ ! -f "$input_file" ]]; then
        echo "Error: File not found: $input_file" >&2
        exit 1
    fi

    # Default output: same name, .pdf extension, same directory
    if [[ -z "$output_file" ]]; then
        output_file="${input_file%.md}.pdf"
    fi

    # Validate CSS exists
    if [[ ! -f "$css_file" ]]; then
        echo "Error: CSS stylesheet not found: $css_file" >&2
        echo "Expected at: $CSS_FILE" >&2
        exit 1
    fi

    check_dependencies

    echo "Rendering PDF..."
    echo "  Input:  $input_file"
    echo "  Output: $output_file"
    echo "  CSS:    $css_file"

    pandoc "$input_file" \
        --pdf-engine=weasyprint \
        --css="$css_file" \
        --standalone \
        --from=markdown+smart \
        -o "$output_file"

    echo "PDF created: $output_file"

    if [[ "$open_after" == "true" && "$OSTYPE" == "darwin"* ]]; then
        open "$output_file"
    fi

    echo "PDF_PATH: $output_file"
}

main "$@"
