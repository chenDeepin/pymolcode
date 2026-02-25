#!/bin/bash
# export_presentation.sh - Export Slidev presentation with error handling

set -e

# Default values
FORMAT="${1:-pptx}"
OUTPUT="${2:-presentation}"
NODE_PATH="${3:-~/node-v20.19.0-linux-x64/bin}"

# Export function
export_slides() {
    local format="$1"
    local output="$2"
    
    echo "Exporting to $format format..."
    
    # Set Node path
    export PATH="$NODE_PATH:$PATH"
    
    # Ensure dependencies are installed
    if [ ! -d "node_modules" ] || [ ! -d "node_modules/playwright" ] && [ ! -d "node_modules/@playwright" ]; then
        echo "Installing Playwright dependencies..."
        npm install -D playwright-chromium 2>/dev/null || npm install -D playwright
        
        # If using full playwright, download browsers
        if command -v npx &> /dev/null && [ -d "node_modules/@playwright" ]; then
            echo "Downloading Playwright browsers..."
            npx playwright install chromium
        fi
    fi
    
    # Build first
    echo "Building presentation..."
    npm run build
    
    # Export
    echo "Exporting to ${output}.${format}..."
    npm run export -- --format "$format" --output "${output}.${format}"
    
    echo ""
    echo "✅ Export complete: ${output}.${format}"
    
    # Check if file exists and has reasonable size
    if [ -f "${output}.${format}" ]; then
        local size=$(stat -c%s "${output}.${format}" | awk '{print $1}')
        if [ "$size" -lt 10000 ]; then
            echo "⚠️  Warning: File is suspiciously small (<10KB), may be corrupted"
        else
            echo "✓ File size: $size bytes"
        fi
    else
        echo "❌ Error: Export failed, file not created"
        return 1
    fi
}

# Main execution
echo "Slidev Export Script"
echo "==================="
echo "Format: $FORMAT"
echo "Output: $OUTPUT"
echo ""

# Export to specified format
case "$FORMAT" in
    pdf|pptx|png|md)
        export_slides "$FORMAT" "$OUTPUT"
        ;;
    *)
        echo "Error: Unsupported format '$FORMAT'"
        echo "Supported formats: pdf, pptx, png, md"
        echo ""
        echo "Usage: $0 [format] [output_name] [node_path]"
        echo "  format: pdf, pptx, png, or md (default: pptx)"
        echo "  output_name: Base name without extension (default: presentation)"
        echo "  node_path: Path to Node v18+ binary (default: ~/node-v20.19.0-linux-x64/bin)"
        exit 1
        ;;
esac

echo ""
echo "Done!"
