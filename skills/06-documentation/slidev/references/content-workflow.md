# Creating Slides from External Content

## Overview

This workflow describes creating Slidev presentations from existing documents (PDFs, reports, Word docs, etc.). Useful for converting presentations, summarizing research, or creating decks from specifications.

## Prerequisites

```bash
# Ensure Node v18+ is available
export PATH=~/node-v20.19.0-linux-x64/bin:$PATH
node --version  # Should show v18+ or v20+

# Install required skills
# (already available in this environment)
# - pdf skill (for PDF extraction)
# - docx skill (for Word docs)
# - slidev skill (for presentation creation)
```

## Workflow Steps

### Step 1: Extract Content from Source

#### From PDF Documents

```bash
# Extract text from PDF using pdfplumber (Python)
python3 << 'EOF'
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        print(f"--- Page {i+1} ---")
        print(text)
        print("\n")
EOF
```

#### From Multiple PDFs

```bash
# Process multiple PDFs and combine
for pdf in doc1.pdf doc2.pdf doc3.pdf; do
    python3 << PYEOF
import pdfplumber
with pdfplumber.open("$pdf") as pdf:
    for page in pdf.pages:
        print(page.extract_text())
PYEOF
    echo ""
done > extracted_content.txt
```

#### From Word Documents

Use docx skill for Word documents:

```bash
# See docx skill for full extraction capabilities
python3 -c "from docx import Document; doc = Document('file.docx'); print('\n\n'.join([p.text for p in doc.paragraphs]))"
```

### Step 2: Analyze and Structure Content

Read extracted content and identify:

1. **Slide boundaries**: Look for sections, chapters, or natural breaks
2. **Key sections**: Introduction, problem, solution, methodology, results, conclusion
3. **Visual elements**: Tables, charts, diagrams mentioned in text
4. **Hierarchical structure**: H1 = main sections, H2 = subsections, H3 = details

Example structure:

```text
Extracted from PDFs:

=== Part 1: Business Pitch ===
- Title
- Problem statement
- Market opportunity
- Solution overview
- Business model

=== Part 2: Technical Details ===
- Architecture
- Algorithm
- Benchmarking
- Case study
```

### Step 3: Plan Slide Structure

Map content to slides:

```markdown
# Slide Planning Template

1. Title Slide
   - Name, subtitle, date, author

2. Introduction
   - Context, problem statement

3. Main Content Slides (1 topic per slide)
   - Use v-click for progressive reveal
   - 1-3 key points per slide

4. Technical Details
   - Architecture diagrams
   - Code blocks or algorithms
   - Performance tables

5. Results/Case Studies
   - Data tables
   - Charts/graphs
   - Key findings

6. Conclusion
   - Summary
   - Next steps
   - Contact info

7. Q&A
   - Simple closing slide
```

**Best Practices**:
- 1 main idea per slide
- 5-7 words per bullet
- Use diagrams for complex concepts
- Progressive disclosure (v-click) for lists

### Step 4: Create Slidev Project

See SKILL.md main section for project setup. Quick version:

```bash
# Create project
mkdir my-presentation
cd my-presentation

# Initialize
npm init -y
npm install @slidev/cli @slidev/theme-seriph vue

# Create package.json
cat > package.json << 'EOF'
{
  "name": "my-presentation",
  "type": "module",
  "private": true,
  "scripts": {
    "build": "slidev build",
    "dev": "slidev --open",
    "export": "slidev export"
  },
  "dependencies": {
    "@slidev/cli": "^52.11.3",
    "@slidev/theme-seriph": "latest",
    "vue": "^3.5.26"
  }
}
EOF

# Install dependencies
npm install
```

### Step 5: Create slides.md

#### Basic Template

```markdown
---
theme: seriph
background: https://source.unsplash.com/collection/94734566/1920x1080
class: text-center
highlighter: shiki
lineNumbers: false
title: Presentation Title
mdc: true
---

# Presentation Title
## Subtitle or tagline

<div class="pt-12">
  <span @click="$slidev.nav.next" class="px-2 py-1 rounded">
    Click or press space to continue
  </span>
</div>

<div class="abs-bl m-6 text-xl text-gray-500">
  Date information
</div>

---
layout: center
class: text-center
---

# Section Title

<v-click>

## Main point to reveal on click

</v-click>

---

# Content Slide

<div class="grid grid-cols-2 gap-8 pt-4">

<div>

## Left Column

- <v-click>Point 1</v-click>
- <v-click>Point 2</v-click>

</div>

<div>

## Right Column

- <v-click>Point A</v-click>
- <v-click>Point B</v-click>

</div>

</div>
```

#### Converting Extracted Content

From extracted text:

```
Source: "The system uses three main components:
1. Input processing
2. Core algorithm
3. Output generation
```

To Slidev slide:

```markdown
# System Components

<div class="grid grid-cols-3 gap-8 pt-4">

<div>

## 1. Input Processing

<v-click>Data ingestion</v-click>
<v-click>Validation</v-click>

</div>

<div>

## 2. Core Algorithm

<v-click>Processing engine</v-click>
<v-click>Optimization</v-click>

</div>

<div>

## 3. Output Generation

<v-click>Formatting</v-click>
<v-click>Export</v-click>

</div>

</div>
```

### Step 6: Add Visual Elements

#### Tables

```markdown
# Performance Comparison

| Metric | System A | System B | Improvement |
|---------|-----------|-----------|-------------|
| Speed   | 100 ms    | 50 ms     | 2x faster |
| Accuracy | 95%       | 98%       | +3%        |
| Cost    | $100       | $80        | 20% savings |
```

#### Code Blocks

```markdown
# Core Algorithm

\`\`\`typescript {all|4|5}
function processData(input: Input): Output {
  // Step 1: Validate
  if (!input.isValid) {
    throw new Error("Invalid input");
  }
  
  // Step 2: Process
  const result = engine.process(input);
  
  // Step 3: Return
  return result;
}
\`\`\`
```

#### Diagrams (Mermaid)

```markdown
# System Architecture

\`\`\`mermaid
graph TD
    A[Input] --> B[Processor]
    B --> C{Decision}
    C -->|Valid| D[Output]
    C -->|Invalid| E[Error]
\`\`\`
```

### Step 7: Build and Test

```bash
# Build presentation
export PATH=~/node-v20.19.0-linux-x64/bin:$PATH
npm run build

# Check for syntax errors
# Build output shows any issues

# Start dev server to preview
npm run dev

# Visit http://localhost:3030
# Navigate through slides, check rendering
```

### Step 8: Export to Desired Format

```bash
# Install export dependencies
npm install -D playwright-chromium

# Export to PPTX
npm run export -- --format pptx --output presentation.pptx

# Or PDF
npm run export -- --format pdf --output presentation.pdf
```

## Common Patterns

### Pattern 1: Document Summary

Convert a report or paper into presentation:

1. **Abstract/Introduction** → Title + Context slides
2. **Methodology** → Technical approach slides
3. **Results** → Data visualization slides
4. **Discussion** → Analysis and implications
5. **Conclusion** → Summary and next steps

### Pattern 2: Pitch Deck from Multiple Sources

Combine business and technical PDFs:

1. **Business pitch PDF** → First half (problem, market, solution, team, roadmap)
2. **Technical paper PDF** → Second half (architecture, methodology, benchmarks)
3. **Transition slide** → Bridge between business and technical sections

### Pattern 3: Progress Report

From multiple documents into one deck:

1. **Background** → Project context
2. **Progress** → Achievements per document
3. **Challenges** → Issues encountered
4. **Next Steps** → Action items
5. **Resources** → Budget/timeline

## Automation Script Example

```bash
#!/bin/bash
# auto_slides.sh - Generate slides from extracted content

CONTENT_FILE="extracted_content.txt"
OUTPUT_FILE="slides.md"

cat > "$OUTPUT_FILE" << 'HEADER'
---
theme: seriph
background: https://source.unsplash.com/collection/94734566/1920x1080
class: text-center
highlighter: shiki
title: Auto-generated Presentation
---

HEADER

# Read content line by line
in_section=false
while IFS= read -r line; do
  if [[ "$line" == "==="* ]]; then
    # Section header
    echo "" >> "$OUTPUT_FILE"
    echo "---" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "# ${line//= / }" >> "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    in_section=true
  elif [[ "$in_section" == true ]]; then
    # Section content
    echo "$line" >> "$OUTPUT_FILE"
  fi
done < "$CONTENT_FILE"

echo "Generated: $OUTPUT_FILE"
```

## Tips for Better Conversions

### Content Organization

1. **Start with outline**: Map major sections to slides
2. **Limit content per slide**: Aim for 5-7 bullets max
3. **Use hierarchy**: H1 = slide title, bullets = content
4. **Combine related points**: Don't spread across multiple slides

### Visual Enhancement

1. **Replace text lists with grids**: Use `grid grid-cols-2` for side-by-side
2. **Use icons**: Carbon icons for visual interest
3. **Add emphasis**: Use `**bold**`, `<v-click>`, and colors
4. **Include tables** for data: Better than text lists

### Narrative Flow

1. **Opening hook**: Start with compelling statement or question
2. **Logical progression**: Problem → Solution → Evidence → Conclusion
3. **Call to action**: End with clear next steps
4. **Q&A slide**: Always include for presentations

## Example: Full Conversion Workflow

```bash
# 1. Extract content
python3 extract_from_pdf.py document.pdf > content.txt

# 2. Create project
mkdir presentation && cd presentation
npm init -y && npm install @slidev/cli @slidev/theme-seriph vue

# 3. Generate slides.md
python3 generate_slides.py content.txt > slides.md

# 4. Build and test
npm run build
npm run dev  # Preview in browser

# 5. Export
npm install -D playwright-chromium
npm run export -- --format pptx --output final.pptx
```

## Quick Reference

| Task | Command |
|-------|----------|
| Extract PDF text | `python3 -c "import pdfplumber; print('\n'.join([p.extract_text() for p in pdfplumber.open('doc.pdf').pages]))"` |
| Create project | `mkdir deck && cd deck && npm init -y && npm install @slidev/cli @slidev/theme-seriph vue` |
| Build slides | `npm run build` |
| Preview | `npm run dev` |
| Export PPTX | `npm run export -- --format pptx` |
| Export PDF | `npm run export -- --format pdf` |
