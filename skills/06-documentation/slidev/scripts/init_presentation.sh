#!/bin/bash
# init_presentation.sh - Create a new Slidev presentation with proper setup

set -e

# Default values
PROJECT_NAME="${1:-my-presentation}"
NODE_PATH="${2:-~/node-v20.19.0-linux-x64/bin}"
THEME="${3:-seriph}"

# Create project directory
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

echo "Creating Slidev project: $PROJECT_NAME"

# Initialize npm package
cat > package.json << EOF
{
  "name": "$PROJECT_NAME",
  "type": "module",
  "private": true,
  "scripts": {
    "build": "slidev build",
    "dev": "slidev --open",
    "export": "slidev export"
  },
  "dependencies": {
    "@slidev/cli": "^52.11.3",
    "@slidev/theme-$THEME": "latest",
    "vue": "^3.5.26"
  }
}
EOF

# Install dependencies
echo "Installing dependencies..."
export PATH="$NODE_PATH:$PATH"
npm install

echo ""
echo "✅ Project created successfully!"
echo ""
echo "Next steps:"
echo "  cd $PROJECT_NAME"
echo "  # Create your slides.md"
echo "  npm run dev    # Start dev server"
echo "  npm run build  # Build for production"
echo "  npm install -D playwright-chromium  # For export"
echo "  npm run export -- --format pptx  # Export to PowerPoint"
