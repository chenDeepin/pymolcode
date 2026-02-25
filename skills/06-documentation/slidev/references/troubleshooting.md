# Slidev Troubleshooting

## Build Errors

### "Invalid end tag"

**Cause**: Using `<v-clicks>...</v-clicks>` or other unsupported Vue syntax

**Solution**: Use individual `<v-click>` tags:

```markdown
<!-- Wrong -->
<v-clicks>
- Item 1
- Item 2
</v-clicks>

<!-- Correct -->
<v-click>- Item 1</v-click>
<v-click>- Item 2</v-click>
```

### "Unknown directive"

**Cause**: Using invalid Vue directives in Slidev context

**Solution**: Stick to supported directives (v-click, v-mark, v-motion). Check [syntax.md](syntax.md)

### "Module not found"

**Cause**: Missing or incorrect dependencies

**Solution**: 

```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Or ensure correct package.json structure
{
  "dependencies": {
    "@slidev/cli": "^52.11.3",
    "@slidev/theme-seriph": "latest",
    "vue": "^3.5.26"
  }
}
```

## Node.js Issues

### "Unsupported engine: required Node >=18.0.0"

**Cause**: Node version too old (common with default Linux installations)

**Solution 1**: Use newer Node binary:

```bash
# Download Node v20+
# Then set PATH:
export PATH=/path/to/node-v20/bin:$PATH

# Verify
node --version  # Should show v20.x.x or higher
```

**Solution 2**: Install Node via nvm:

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Restart terminal, then:
nvm install 20
nvm use 20
```

### npm hangs or times out

**Cause**: Network issues or registry problems

**Solution**:

```bash
# Try different registry
npm install --registry=https://registry.npmmirror.com

# Or use npm mirror
npm config set registry https://registry.npmmirror.com
```

## Export Errors

### "playwright-chromium not installed"

**Cause**: Export requires Playwright browser

**Solution**:

```bash
# Install as dev dependency
npm install -D playwright-chromium

# Or install Playwright directly
npm install -D playwright
npx playwright install chromium
```

### Playwright download timeouts

**Cause**: Slow network or large browser download (~170MB)

**Solution**:

```bash
# Install Playwright first, then browsers separately
npm install -D playwright

# This may take time, let it complete
# Downloads: chromium (167MB), FFmpeg (2MB), headless-shell (110MB)
npx playwright install chromium
```

### Export fails silently

**Cause**: Missing executable or build errors

**Solution**:

```bash
# First build successfully
npm run build

# Then export
npm run export -- --format pptx

# Check output for error messages
```

### "executable-path not found"

**Cause**: Incorrect browser path specified

**Solution**:

```bash
# Don't use --executable-path for standard export
npm run export -- --format pptx

# Only use if you have custom browser
# npm run export -- --format pptx --executable-path /path/to/chrome
```

## Dev Server Issues

### Port already in use

**Cause**: Default port 3030 occupied

**Solution**:

```bash
# Use different port
npm run dev -- --port 3031

# Or kill existing process
lsof -ti:3030 | xargs kill -9
```

### Browser won't open

**Cause**: No browser installed or permission issues

**Solution**:

```bash
# Check browser
which chromium-browser google-chrome firefox

# Or use --port to manually open
npm run dev -- --port 3031
# Then visit http://localhost:3031 manually
```

## Content Issues

### Slides don't render correctly

**Cause**: Syntax errors or improper markdown structure

**Solution**:

```bash
# Check build output
npm run build

# Look for errors in console
# Fix syntax errors in slides.md
```

### Images not displaying

**Cause**: Incorrect path or unsupported format

**Solution**:

```bash
# Use relative paths from project root
![Alt text](./images/my-image.png)

# Or use absolute paths
![Alt text](/full/path/to/image.png)

# Verify file exists
ls images/my-image.png
```

### Styles not applying

**Cause**: Scoped styles or CSS order issues

**Solution**:

```markdown
<style scoped>
/* Scoped to current slide only */
.custom-class {
  color: red;
}
</style>
```

## Theme Issues

### Theme not loading

**Cause**: Missing or incorrect theme package

**Solution**:

```bash
# Install theme
npm install @slidev/theme-default
# or
npm install @slidev/theme-seriph

# Update frontmatter
---
theme: seriph  # lowercase theme name
---
```

### Custom theme not working

**Cause**: Incorrect theme configuration

**Solution**:

```bash
# Ensure theme structure:
my-theme/
├── package.json
├── styles/
│   ├── index.css
│   └── layouts.css
└── components/

# Install locally:
npm install ./my-theme

# Use in slides.md:
---
theme: my-theme
---
```

## Performance Issues

### Slow build times

**Cause**: Large dependencies or many slides

**Solution**:

```bash
# Clear cache
rm -rf .slidev

# Use production build
npm run build

# For dev, reduce slides count while developing
```

### Export takes too long

**Cause**: Many slides or complex animations

**Solution**:

```bash
# Export specific slides only
npm run export -- --range 1-10

# Or use per-slide export
npm run export -- --format pptx --per-slide
```

## Platform-Specific Issues

### Linux: Permission denied

**Cause**: npm global installation or Node permissions

**Solution**:

```bash
# Don't use sudo with npm
# Instead, fix npm permissions:
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
export PATH=~/.npm-global/bin:$PATH

# Then install without sudo
```

### Windows: Path too long

**Cause**: Windows path length limit

**Solution**:

```bash
# Use shorter directory names
# Instead of: C:\very\long\path\to\project
# Use: C:\dev\slidev
```

### macOS: Gatekeeper issues

**Cause**: Security blocking downloaded binaries

**Solution**:

```bash
# Allow Playwright browsers
xattr -dr com.apple.quarantine ~/Library/Caches/ms-playwright/*
```

## Getting Help

### Official Documentation

- Slidev Docs: https://sli.dev
- GitHub: https://github.com/slidevjs/slidev

### Common Commands to Debug

```bash
# Check Node version
node --version
npm --version

# Check installed packages
npm list

# Clean reinstall
rm -rf node_modules package-lock.json
npm install

# Test build
npm run build

# Check for updates
npm outdated
```

### Report Issues

When reporting issues, include:

1. Node.js version (`node --version`)
2. npm version (`npm --version`)
3. OS and version
4. Full error message
5. Steps to reproduce
6. Relevant code snippets
