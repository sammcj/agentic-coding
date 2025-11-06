# Slidev Layouts Reference

This reference documents all 17 built-in Slidev layouts with usage examples and when to use each.

## Layout Overview

Layouts control the structure and styling of individual slides. Specify a layout using frontmatter:

```yaml
---
layout: layout-name
---
```

## Built-in Layouts

### 1. cover
**Purpose**: Title slide for presentation opening
**Best for**: First slide, major section starts

```markdown
---
layout: cover
background: /cover-image.jpg
class: text-center
---

# Presentation Title

## Subtitle

Author Name · Date/Event
```

**Common options**:
- `background`: Image URL or gradient
- `class`: CSS classes (text-center, text-left)

---

### 2. default
**Purpose**: Standard content layout
**Best for**: General content, bullet points, paragraphs

```markdown
---
layout: default
---

# Slide Title

- Bullet point 1
- Bullet point 2
- Bullet point 3

Regular paragraph text works here too.
```

---

### 3. center
**Purpose**: Vertically and horizontally centred content
**Best for**: Short quotes, key statements, simple diagrams

```markdown
---
layout: center
---

# Centred Title

All content is centred on the slide
```

---

### 4. section
**Purpose**: Section divider
**Best for**: Marking transitions between presentation parts

```markdown
---
layout: section
background: linear-gradient(to right, #667eea, #764ba2)
class: text-white
---

# Part 2: Implementation
```

---

### 5. statement
**Purpose**: Bold statement or key message
**Best for**: Emphasis, key takeaways, memorable quotes

```markdown
---
layout: statement
---

# A Bold Statement

Supporting text if needed
```

---

### 6. fact
**Purpose**: Highlight statistics or data
**Best for**: Numbers, metrics, important facts

```markdown
---
layout: fact
---

# 95%

Success rate achieved

```

---

### 7. quote
**Purpose**: Display quotations
**Best for**: Testimonials, famous quotes, citations

```markdown
---
layout: quote
---

"Design is not just what it looks like and feels like. Design is how it works."

— Steve Jobs
```

---

### 8. end
**Purpose**: Final slide
**Best for**: Thank you slide, Q&A, contact information

```markdown
---
layout: end
---

# Thank You

Questions?

your.email@example.com
```

---

### 9. two-cols
**Purpose**: Two-column layout
**Best for**: Comparisons, before/after, contrasting concepts

```markdown
---
layout: two-cols
---

# Left Column

Content on the left side

::right::

# Right Column

Content on the right side
```

**Named slots**:
- Default: Left column
- `::right::`: Right column

---

### 10. two-cols-header
**Purpose**: Header spanning both columns, then split content
**Best for**: Shared title with different details below

```markdown
---
layout: two-cols-header
---

# Full-Width Header

Spans both columns

::left::

Left content here

::right::

Right content here
```

**Named slots**:
- Default: Header (full width)
- `::left::`: Left column
- `::right::`: Right column

---

### 11. image-left
**Purpose**: Image on left, content on right
**Best for**: Diagrams with explanations, screenshots with text

```markdown
---
layout: image-left
image: /diagram.png
backgroundSize: contain
---

# Explanation Title

- Point 1
- Point 2
- Point 3
```

**Options**:
- `image`: Path to image (required)
- `backgroundSize`: cover | contain | custom (default: cover)
- `class`: Custom classes for content area

---

### 12. image-right
**Purpose**: Image on right, content on left
**Best for**: Diagrams with explanations, screenshots with text

```markdown
---
layout: image-right
image: /architecture.png
backgroundSize: contain
class: my-content
---

# System Architecture

Content on the left explains the diagram on the right
```

**Options**: Same as image-left

---

### 13. image
**Purpose**: Full-screen image background
**Best for**: Photo slides, visual breaks, background images

```markdown
---
layout: image
image: /background.jpg
backgroundSize: cover
---

# Title Over Image

Optional content overlaid on image
```

---

### 14. iframe
**Purpose**: Embed full-screen web page
**Best for**: Live demos, web documentation, interactive content

```markdown
---
layout: iframe
url: https://github.com/slidevjs/slidev
---
```

**Note**: No additional content displays with this layout

---

### 15. iframe-left
**Purpose**: Web page on left, content on right
**Best for**: Explaining a website, showing live examples

```markdown
---
layout: iframe-left
url: https://example.com
---

# About This Site

- Feature 1
- Feature 2
- Feature 3
```

---

### 16. iframe-right
**Purpose**: Web page on right, content on left
**Best for**: Explaining a website, showing live examples

```markdown
---
layout: iframe-right
url: https://sli.dev
---

# Slidev Official Site

Content on left, live site on right
```

---

### 17. none
**Purpose**: Blank layout for full custom control
**Best for**: Completely custom slides, special designs

```markdown
---
layout: none
---

<div class="absolute inset-0 flex items-center justify-center">
  <h1>Completely Custom</h1>
</div>
```

## Custom Layouts

Create custom layouts in `./layouts/custom-name.vue`:

```vue
<template>
  <div class="slidev-layout my-custom-layout">
    <div class="header">
      <slot name="header" />
    </div>
    <div class="content">
      <slot />
    </div>
    <div class="footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<style scoped>
.my-custom-layout {
  padding: 2rem;
}
</style>
```

Usage:
```markdown
---
layout: custom-name
---

::header::
Header content

Main content

::footer::
Footer content
```

## Layout Selection Guide

| Use Case | Recommended Layout |
|----------|-------------------|
| Title slide | cover |
| Section divider | section |
| Standard content | default |
| Short quote | center |
| Big number/stat | fact |
| Long quote | quote |
| Comparison | two-cols |
| Image + text | image-left/right |
| Full image | image |
| Live website | iframe/iframe-left/right |
| Final slide | end |
| Custom design | none |

## Common Patterns

### Progressive Comparison
```markdown
---
layout: two-cols
---

# Before

```js
var x = 1
```

::right::

# After

```js
const x = 1
```
```

### Image with Explanation
```markdown
---
layout: image-right
image: /diagram.png
backgroundSize: contain
---

# Architecture

<v-clicks>

- Layer 1: Presentation
- Layer 2: Business Logic
- Layer 3: Data Access

</v-clicks>
```

### Live Demo with Notes
```markdown
---
layout: iframe-left
url: http://localhost:3000
---

# Try It Out

1. Click the button
2. Enter your name
3. See the result

<!-- Presenter note: Make sure dev server is running -->
```
