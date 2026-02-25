# Slidev Syntax Reference

## Slide Structure

Each slide is separated by `---`:

```markdown
---
frontmatter options
---

# Slide Title

Content here

---
# Next Slide
```

## Frontmatter Options

```yaml
---
theme: seriph           # Theme to use
background: URL           # Background image
class: text-center      # CSS classes
layout: center          # Layout variant
transition: slide-left   # Transition animation
mdc: true              # Enable MDC syntax
highlighter: shiki     # Code highlighter
---
```

## Layout Options

- **Default**: Standard slide layout
- **layout: center**: Centered content
- **layout: image-right**: Image on right side
- **layout: two-cols**: Two column layout
- **layout: cover**: Cover slide

## Animations & Interactions

### v-click

Shows content on click. Use INDIVIDUAL `<v-click>` tags.

```markdown
<v-click>This appears on first click</v-click>

<v-click>This appears on second click</v-click>
```

**NOT SUPPORTED**: `<v-clicks>...</v-clicks>` or `v-clicks` directive

### v-mark

Highlight text with Rough Notation:

```markdown
<v-mark.red="1">highlighted text</v-mark>
<v-mark.underline.orange="2">underlined text</v-mark>
<v-mark.circle.blue="3">circled text</v-mark>
```

### v-motion

Element motion animations:

```html
<div v-motion :initial="{ opacity: 0 }" :enter="{ opacity: 1 }">
  Animated content
</div>
```

## Code Blocks

### Basic Code

```markdown
\`\`\`typescript
const x = 1;
\`\`\`
```

### Magic Move (Animated Code Transitions)

```markdown
\`\`\`md magic-move
\`\`\`typescript
const x = 1;
\`\`\`

\`\`\`typescript
const x = 2;
\`\`\`
\`\`\`
```

### TwoSlash (TypeScript Hover Info)

```markdown
\`\`\`typescript {twoslash}
const x = ref(0)
\`\`\`
```

## Components

### Built-in Components

```markdown
<Toc minDepth="1" maxDepth="2" />
<Tweet id="1390115482657726468" />
<Counter :count="10" />
```

### Custom Components

```html
<SlideCounter v-model="count" />
<CustomChart :data="chartData" />
```

## HTML & CSS

### Inline HTML

```html
<div class="grid grid-cols-2 gap-4">
  <div>Column 1</div>
  <div>Column 2</div>
</div>
```

### Scoped Styles

```markdown
<style>
h1 {
  background: linear-gradient(45deg, #4EC5D4 10%, #146b8c 20%);
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>
```

## Typography

### Emphasis

```markdown
**Bold text**
*Italic text*
~~Strikethrough~~
`Code span`
```

### Lists

```markdown
- Bullet item
  - Nested item

1. Numbered item
2. Another item

| Column 1 | Column 2 |
|-----------|-----------|
| Cell A    | Cell B     |
```

### LaTeX

```markdown
Inline: $\sqrt{3x-1}$

Block:
$$
\begin{aligned}
E &= mc^2
\end{aligned}
$$
```

## Diagrams

### Mermaid

```markdown
\`\`\`mermaid
graph TD
  A[Start] --> B{Decision}
  B -->|Yes| C[Result 1]
  B -->|No| D[Result 2]
\`\`\`
```

### PlantUML

```markdown
\`\`\`plantuml
@startuml
Alice -> Bob: Hello
Bob -> Alice: Hi
@enduml
\`\`\`
```

## Icons

### Carbon Icons

```markdown
<carbon:logo-github />
<carbon:arrow-right />
<carbon:edit />
```

### Emoji

Use emoji directly in markdown: 🎉 🔥 🚀

## Images

```markdown
![Alt text](path/to/image.png)
<img src="path/to/image.png" alt="Description" />

<img v-drag src="path/to/image.png">
```

## Common Pitfalls

### ❌ DON'T: v-clicks

```markdown
<!-- This causes errors -->
<v-clicks>
- Item 1
- Item 2
</v-clicks>
```

### ✅ DO: Individual v-click

```markdown
<!-- This works -->
<v-click>- Item 1</v-click>
<v-click>- Item 2</v-click>
```

### ❌ DON'T: Unclosed HTML

```markdown
<div>
  Content
<!-- Missing closing tag -->
```

### ✅ DO: Proper HTML

```markdown
<div>
  Content
</div>
```

## Best Practices

1. **Use v-click sparingly**: One per element, not wrapping entire lists
2. **Test builds early**: Run `npm run build` frequently to catch syntax errors
3. **Keep slides focused**: One main idea per slide
4. **Use layouts**: Leverage pre-built layouts for consistency
5. **Preview often**: Use dev server to see how slides render
