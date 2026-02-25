# Slidev Export Workflow

## Overview

Exporting Slidev presentations to PDF, PPTX, PNG, or Markdown requires Playwright Chromium. This workflow covers the complete export process and troubleshooting.

## Prerequisites

### Node.js Version

**Critical**: Slidev export requires Node.js v18+ or v20+. Older versions will fail.

```bash
# Check Node version
node --version

# If older than v18, upgrade or use newer binary:
export PATH=~/node-v20.19.0-linux-x64/bin:$PATH
```

### Install Export Dependencies

Export to PDF/PNG/PPTX requires Playwright browsers. Install one of:

#### Option 1: playwright-chromium (Recommended)

```bash
cd your-presentation
npm install -D playwright-chromium
```

**Pros**: Smaller, chromium-only, faster download  
**Cons**: Only supports chromium browser

#### Option 2: Playwright Full Package

```bash
cd your-presentation
npm install -D playwright

# Download browsers
npx playwright install chromium
```

**Pros**: Full Playwright, multiple browser support  
**Cons**: Larger package, longer download time (~280MB total)

**Download Details**:

| Component | Size | Location |
|-----------|------|----------|
| Chromium | 167 MB | ~/.cache/ms-playwright/chromium-1208 |
| Chrome Headless Shell | 111 MB | ~/.cache/ms-playwright/chromium_headless_shell-1208 |
| FFmpeg | 2.3 MB | ~/.cache/ms-playwright/ffmpeg-1011 |

**Total**: ~280 MB download, may take 5-10 minutes

## Export Commands

### Basic Export

```bash
# Default export (PDF)
npm run export

# Specific format
npm run export -- --format pptx
npm run export -- --format pdf
npm run export -- --format png
npm run export -- --format md
```

### Export Options

```bash
# Custom output filename
npm run export -- --format pptx --output MyPresentation.pptx

# Export specific slides
npm run export -- --range 1,3,5-10

# Export with click animations
npm run export -- --with-clicks

# Export per-slide (slower but better for global components)
npm run export -- --per-slide

# Wait for network idle before exporting
npm run export -- --wait-until networkidle

# Wait specific milliseconds
npm run export -- --wait 2000
```

## Export Formats

### PDF Export

```bash
npm run export -- --format pdf --output deck.pdf
```

**Use when**: Print-ready, email distribution, PDF viewers only  
**Output**: Single PDF file with all slides  
**Size**: ~1-5 MB depending on slides

### PPTX Export

```bash
npm run export -- --format pptx --output deck.pptx
```

**Use when**: Editing in PowerPoint/Keynote, collaboration with Microsoft Office users  
**Output**: PowerPoint file (.pptx)  
**Size**: ~3-10 MB depending on slides  
**Note**: Some Slidev features (animations, layouts) may not translate perfectly

### PNG Export

```bash
npm run export -- --format png --output slide-%d.png
```

**Use when**: Web use, social media, image-only needs  
**Output**: One PNG per slide  
**Size**: ~500KB-2MB per slide

### Markdown Export

```bash
npm run export -- --format md --output deck.md
```

**Use when**: Version control, text-only, conversion to other markdown tools  
**Output**: Single markdown file

## Troubleshooting

### Issue: "playwright not installed"

**Symptom**:
```
Error: The exporting for Slidev is powered by Playwright, please install it via `npm i -D playwright-chromium`
```

**Solution**:

```bash
# Install playwright-chromium
npm install -D playwright-chromium

# Or install full Playwright
npm install -D playwright
npx playwright install chromium
```

### Issue: Playwright download times out

**Symptom**: Download hangs or fails during `npm install playwright-chromium`

**Solutions**:

1. **Increase timeout**:
```bash
npm install -D playwright-chromium --timeout=300000  # 5 minutes
```

2. **Install separately**:
```bash
# Install package first
npm install -D playwright

# Then download browsers manually (with longer timeout)
PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/ npx playwright install chromium
```

3. **Use mirror** (for China/slow regions):
```bash
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
npx playwright install chromium
```

4. **Pre-download browsers**:
```bash
# Before running Slidev export
npx playwright install chromium

# This downloads to ~/.cache/ms-playwright/
# Then Slidev can use cached browsers
```

### Issue: Export hangs or never completes

**Symptoms**: Export command runs indefinitely without output

**Solutions**:

1. **Check build first**:
```bash
# Ensure project builds successfully
npm run build

# If build fails, fix issues before exporting
```

2. **Reduce scope**:
```bash
# Export fewer slides first
npm run export -- --range 1-5

# Then expand range
npm run export -- --range 1-10
```

3. **Increase timeout**:
```bash
# Add timeout flag to export command
npm run export -- --timeout 300000  # 5 minutes
```

4. **Check system resources**:
```bash
# Verify enough memory (2GB+ recommended)
free -h

# Check disk space (need ~1GB for temp files)
df -h
```

### Issue: "executable-path not found"

**Symptom**: Custom browser path specified but not accessible

**Solution**:

```bash
# Don't use --executable-path unless necessary
npm run export -- --format pptx  # Uses built-in Playwright

# Only specify if you know exact path:
npm run export -- --format pptx --executable-path /usr/bin/google-chrome
```

### Issue: Exported PPTX is corrupted

**Symptom**: PowerPoint cannot open exported .pptx file

**Solutions**:

1. **Verify file size**:
```bash
ls -lh deck.pptx

# Should be >100KB. If <50KB, export failed silently
```

2. **Rebuild first**:
```bash
npm run build
npm run export -- --format pptx
```

3. **Try PDF instead**:
```bash
# If PPTX consistently fails, export to PDF
npm run export -- --format pdf
```

### Issue: Images missing in export

**Symptom**: Export has broken images or missing graphics

**Solutions**:

1. **Check image paths**:
```markdown
# Use relative paths from project root
![Alt text](./images/photo.png)

# Not absolute paths that might be inaccessible during export
```

2. **Verify images exist**:
```bash
ls images/photo.png
```

3. **Use online images**:
```markdown
# Use public URLs that export process can access
![Alt text](https://example.com/image.png)
```

### Issue: Chinese characters show as squares

**Symptom**: Unicode text appears as □□□ in exported PDF

**Solutions**:

1. **Use system fonts**:
```yaml
---
theme: seriph
fonts:
  - NotoSansSC
  - NotoSerifSC
---
```

2. **Verify font installation**:
```bash
# Check if CJK fonts are installed
fc-list :lang=zh | grep Noto
```

## Performance Optimization

### Faster Exports

1. **Use --per-slide flag carefully**:
```bash
# Only use if needed
npm run export -- --format png --per-slide

# Don't use for simple exports (slower)
npm run export -- --format png  # Faster
```

2. **Reduce slide complexity**:
   - Limit animations
   - Simplify diagrams
   - Use fewer images

3. **Export to PDF first**:
   - PDF export is typically faster than PPTX
   - Use as fallback if PPTX times out

### Memory Management

```bash
# Check available memory
free -h

# Limit Chrome memory if needed
export CHROME_EXECUTABLE_PATH=$HOME/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome
export CHROME_ARGUMENTS="--max_old_space_size=512"

# Then export
npm run export -- --format pptx
```

## Automation Examples

### Batch Export to Multiple Formats

```bash
#!/bin/bash
# export_all.sh - Export to all formats

cd your-presentation
export PATH=~/node-v20.19.0-linux-x64/bin:$PATH

# Ensure built
npm run build

# Export to each format
npm run export -- --format pdf --output deck.pdf
npm run export -- --format pptx --output deck.pptx
npm run export -- --format png --output deck.png

echo "Export complete!"
ls -lh deck.*
```

### CI/CD Pipeline Example

```yaml
# .github/workflows/export.yml
name: Export Presentation

on:
  push:
    branches: [main]

jobs:
  export:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Node
        uses: actions/setup-node@v2
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright
        run: npx playwright install --with-deps chromium
      
      - name: Build
        run: npm run build
      
      - name: Export
        run: npm run export -- --format pdf --output presentation.pdf
      
      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: presentation
          path: presentation.pdf
```

## Quick Reference

| Task | Command |
|-------|----------|
| Install dependencies | `npm install -D playwright-chromium` |
| Export PDF | `npm run export -- --format pdf` |
| Export PPTX | `npm run export -- --format pptx` |
| Export PNG | `npm run export -- --format png` |
| Export MD | `npm run export -- --format md` |
| Custom filename | `npm run export -- --format pptx --output deck.pptx` |
| Specific slides | `npm run export -- --range 1,3,5-10` |
| With animations | `npm run export -- --with-clicks` |
| Per-slide export | `npm run export -- --per-slide` |
| Check Node version | `node --version` |
| Verify build | `npm run build` |
| Download Playwright | `npx playwright install chromium` |

## Getting Help

### Official Resources

- Slidev Export Docs: https://sli.dev/guide/export
- Playwright Docs: https://playwright.dev/docs/intro
- GitHub Issues: https://github.com/slidevjs/slidev/issues

### Debug Information

When reporting export issues, include:

```bash
# Node and npm versions
echo "Node: $(node --version)"
echo "npm: $(npm --version)"

# Slidev version
npm list @slidev/cli

# Playwright version
npm list playwright

# System info
uname -a

# Build output
npm run build 2>&1 | tee build.log

# Export output
npm run export -- --format pptx 2>&1 | tee export.log
```
