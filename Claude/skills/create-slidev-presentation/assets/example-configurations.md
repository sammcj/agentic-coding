# Example Slidev Configurations

Complete example configuration files for common use cases.

## Basic Presentation

### Minimal `slides.md`
```markdown
---
theme: default
title: My Presentation
---

# Welcome

This is a minimal Slidev presentation

---

# Slide 2

Content here

---
layout: end
---

# Thank You
```

## Professional Business Presentation

### `slides.md` Headmatter
```yaml
---
theme: seriph
title: Q4 Business Review
author: Jane Smith
info: |
  ## Q4 2024 Business Review
  Quarterly performance and strategic initiatives

colorSchema: light
class: text-center
mdc: true
transition: slide-left
download: true
exportFilename: q4-business-review

aspectRatio: 16/9
canvasWidth: 980

fonts:
  sans: Inter
  serif: Lora
  weights: '300,400,600,700'
  provider: google

drawings:
  enabled: true
  persist: false
  presenterOnly: true

themeConfig:
  primary: '#1E40AF'
  secondary: '#059669'
---
```

## Technical/Code-Heavy Presentation

### `slides.md` Headmatter
```yaml
---
theme: default
title: Modern JavaScript Patterns
author: Alex Developer
keywords: javascript,typescript,patterns,best-practices

colorSchema: dark
mdc: true
monaco: dev
lineNumbers: true
twoslash: true
highlighter: shiki
transition: slide-left

aspectRatio: 16/9
canvasWidth: 1200

fonts:
  sans: Inter
  mono: JetBrains Mono
  weights: '300,400,600,700'
  provider: google

drawings:
  enabled: false

export:
  format: pdf
  dark: true
  withClicks: true
---
```

### `setup/shiki.ts`
```typescript
import { defineShikiSetup } from '@slidev/types'

export default defineShikiSetup(() => {
  return {
    themes: {
      dark: 'nord',
      light: 'github-light',
    },
    transformers: [],
  }
})
```

### `setup/monaco.ts`
```typescript
import { defineMonacoSetup } from '@slidev/types'

export default defineMonacoSetup(() => {
  return {
    editorOptions: {
      wordWrap: 'on',
      fontSize: 16,
      lineNumbers: 'on',
      minimap: { enabled: false },
      theme: 'vs-dark',
      tabSize: 2,
      fontFamily: 'JetBrains Mono, monospace',
    }
  }
})
```

### `uno.config.ts`
```typescript
import { defineConfig } from 'unocss'
import { presetAttributify, presetUno, presetWebFonts } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetAttributify(),
    presetWebFonts({
      fonts: {
        mono: 'JetBrains Mono',
      },
    }),
  ],
  shortcuts: {
    'code-block': 'bg-gray-900 text-gray-100 p-4 rounded',
  },
  safelist: [
    'i-carbon:logo-github',
    'i-carbon:logo-typescript',
  ],
})
```

## Conference/Workshop Presentation

### `slides.md` Headmatter
```yaml
---
theme: seriph
title: Building Scalable Web Apps
info: |
  ## Workshop: Building Scalable Web Apps
  TechConf 2025 - Full-Day Workshop
author: Jamie Technical
keywords: workshop,web,scalability,architecture

colorSchema: auto
background: /conference-bg.jpg
class: text-center

mdc: true
monaco: dev
lineNumbers: true
transition: view-transition
download: true
record: dev
presenter: true

aspectRatio: 16/9
canvasWidth: 980

fonts:
  sans: Roboto
  mono: Fira Code
  weights: '300,400,600,700,900'
  provider: google

drawings:
  enabled: true
  persist: true
  presenterOnly: false
  syncAll: true

export:
  format: pdf
  timeout: 60000
  dark: false
  withClicks: false
  withToc: true

exportFilename: scalable-web-apps-workshop

themeConfig:
  primary: '#6366F1'
  secondary: '#EC4899'

defaults:
  layout: default
  transition: view-transition

htmlAttrs:
  lang: en
  dir: ltr

seoMeta:
  ogTitle: Building Scalable Web Apps Workshop
  ogDescription: Learn modern patterns for building scalable web applications
  ogImage: https://example.com/workshop-cover.jpg
  twitterCard: summary_large_image
---
```

### `setup/shortcuts.ts`
```typescript
import { defineShortcutsSetup, NavOperations } from '@slidev/types'

export default defineShortcutsSetup((nav: NavOperations) => {
  return [
    {
      key: 'ctrl+shift+enter',
      fn: () => nav.next(),
      autoRepeat: true,
    },
    {
      key: 'ctrl+shift+backspace',
      fn: () => nav.prev(),
      autoRepeat: true,
    },
  ]
})
```

## Educational/Tutorial Presentation

### `slides.md` Headmatter
```yaml
---
theme: default
title: Introduction to Vue.js
info: |
  ## Introduction to Vue.js
  A beginner-friendly guide to modern web development
author: Chris Educator

colorSchema: light
class: text-left
mdc: true
monaco: dev
lineNumbers: true
transition: slide-left

aspectRatio: 16/9
canvasWidth: 980

fonts:
  sans: Open Sans
  mono: Source Code Pro
  weights: '400,600,700'
  provider: google

drawings:
  enabled: true
  persist: true

export:
  format: pdf
  withClicks: false

themeConfig:
  primary: '#42B883'
  secondary: '#35495E'
---
```

### `setup/mermaid.ts`
```typescript
import { defineMermaidSetup } from '@slidev/types'

export default defineMermaidSetup(() => {
  return {
    theme: 'base',
    themeVariables: {
      primaryColor: '#42B883',
      primaryTextColor: '#fff',
      primaryBorderColor: '#35495E',
      lineColor: '#35495E',
      secondaryColor: '#35495E',
      tertiaryColor: '#fff',
    }
  }
})
```

## Minimalist/Design-Focused Presentation

### `slides.md` Headmatter
```yaml
---
theme: apple-basic
title: Product Design Principles
author: Designer Name

colorSchema: light
class: text-center
transition: fade
download: false

aspectRatio: 16/9
canvasWidth: 980

fonts:
  sans: SF Pro Display
  serif: New York
  weights: '300,400,500,600'
  provider: none
  local: SF Pro Display,New York

drawings:
  enabled: false

themeConfig:
  primary: '#000000'
  secondary: '#666666'

defaults:
  layout: center
  transition: fade
---
```

### `styles/index.css`
```css
/* Custom global styles */
:root {
  --color-primary: #000000;
  --color-secondary: #666666;
  --spacing-unit: 1rem;
}

.slidev-layout {
  font-size: 1.5rem;
  line-height: 1.6;
}

h1 {
  font-weight: 600;
  font-size: 4rem;
  letter-spacing: -0.02em;
  margin-bottom: 2rem;
}

h2 {
  font-weight: 500;
  font-size: 2.5rem;
  letter-spacing: -0.01em;
}

p {
  font-weight: 400;
  max-width: 40rem;
  margin-inline: auto;
}
```

## Multi-File Presentation

### `slides.md` (Main file)
```markdown
---
theme: seriph
title: Complete Product Overview
---

# Welcome

Product Overview Presentation

---
src: ./pages/introduction.md
---

---
src: ./pages/features.md
---

---
src: ./pages/demo.md
---

---
src: ./pages/pricing.md
---

---
layout: end
---

# Thank You
```

### `pages/introduction.md`
```markdown
---
layout: section
---

# Introduction

---

# About Our Company

Founded in 2020...

---

# Mission Statement

To revolutionize...
```

### `pages/features.md`
```markdown
---
layout: section
---

# Features

---
layout: two-cols
---

# Core Features

- Feature 1
- Feature 2

::right::

# Advanced Features

- Advanced 1
- Advanced 2
```

## Complete Project Example

### Directory Structure
```
my-presentation/
├── slides.md
├── package.json
├── slidev.config.ts
├── uno.config.ts
├── vite.config.ts
├── components/
│   ├── Logo.vue
│   └── StatsCard.vue
├── layouts/
│   └── custom.vue
├── pages/
│   ├── intro.md
│   └── demo.md
├── public/
│   ├── images/
│   ├── videos/
│   └── fonts/
├── setup/
│   ├── main.ts
│   ├── shiki.ts
│   ├── monaco.ts
│   └── shortcuts.ts
└── styles/
    └── index.css
```

### `package.json`
```json
{
  "name": "my-presentation",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "slidev --open",
    "build": "slidev build",
    "export": "slidev export",
    "export:pptx": "slidev export --format pptx",
    "format": "slidev format"
  },
  "dependencies": {
    "@slidev/cli": "^0.52.6",
    "@slidev/theme-seriph": "^0.27.1"
  },
  "devDependencies": {
    "playwright-chromium": "^1.40.0",
    "unocss": "^0.58.0",
    "vite": "^5.0.0"
  }
}
```

### `slidev.config.ts`
```typescript
import { defineConfig } from '@slidev/cli'

export default defineConfig({
  theme: 'seriph',
  highlighter: 'shiki',
  lineNumbers: true,
  monaco: 'dev',
  routerMode: 'history',
  aspectRatio: 16 / 9,
  canvasWidth: 980,

  fonts: {
    sans: 'Inter',
    mono: 'JetBrains Mono',
    weights: '300,400,600,700',
    provider: 'google',
  },

  drawings: {
    enabled: true,
    persist: true,
    syncAll: true,
  },

  exportFilename: 'presentation',
  download: true,
  mdc: true,
})
```

### `vite.config.ts`
```typescript
import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 3030,
    open: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
```

### `setup/main.ts`
```typescript
import { defineAppSetup } from '@slidev/types'
import Logo from '../components/Logo.vue'
import StatsCard from '../components/StatsCard.vue'

export default defineAppSetup(({ app }) => {
  // Register global components
  app.component('Logo', Logo)
  app.component('StatsCard', StatsCard)

  // Global properties
  app.config.globalProperties.$formatNumber = (n: number) => {
    return new Intl.NumberFormat('en-US').format(n)
  }
})
```

## Quick Start Templates

### 3-Slide Minimum
```markdown
---
theme: default
title: Quick Demo
---

# Title

Introduction

---

# Content

Main points

---
layout: end
---

# End
```

### 10-Slide Standard
```markdown
---
theme: seriph
title: Standard Presentation
---

# Cover

---
layout: section
---

# Section 1

---

# Slide 3

---

# Slide 4

---
layout: section
---

# Section 2

---

# Slide 6

---

# Slide 7

---
layout: two-cols
---

# Comparison

::right::

# Results

---
layout: section
---

# Conclusion

---
layout: end
---

# Thank You
```

## Configuration Best Practices

### 1. Start Simple
```yaml
---
theme: default
title: My Talk
---
```

### 2. Add Features as Needed
```yaml
---
theme: default
title: My Talk
mdc: true
lineNumbers: true
---
```

### 3. Optimize for Use Case
```yaml
---
# Code presentations
monaco: dev
lineNumbers: true
twoslash: true

# OR design presentations
transition: fade
drawings: false
```

### 4. Test Before Presenting
```bash
# Test locally
slidev

# Test build
slidev build
npx serve dist

# Test export
slidev export --range 1-5
```
