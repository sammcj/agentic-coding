# Slidev Configuration Reference

Complete reference for all Slidev configuration options.

## Configuration Methods

Slidev can be configured through:
1. **Headmatter**: First slide's YAML frontmatter (most common)
2. **slidev.config.ts**: TypeScript configuration file
3. **Per-slide frontmatter**: Individual slide configuration

## Headmatter (Global Configuration)

The first slide's frontmatter configures the entire presentation.

### Complete Headmatter Example

```yaml
---
# Theme
theme: seriph
colorSchema: auto

# Metadata
title: My Presentation
info: |
  ## Detailed Description
  Multi-line markdown supported
author: Jane Developer
keywords: vue,typescript,presentations

# Appearance
background: /cover.jpg
class: text-center

# Features
mdc: true
monaco: dev
lineNumbers: true
twoslash: true
download: true
presenter: true
record: dev

# Transitions
transition: slide-left
drawings:
  enabled: true
  persist: true
  presenterOnly: false
  syncAll: true

# Layout
aspectRatio: 16/9
canvasWidth: 980
routerMode: history

# Fonts
fonts:
  sans: Inter
  serif: Lora
  mono: JetBrains Mono
  weights: '300,400,600,700'
  italic: true
  provider: google

# Export
exportFilename: my-presentation
export:
  format: pdf
  timeout: 30000
  dark: false
  withClicks: false
  withToc: true

# Highlighting
highlighter: shiki
contextMenu: true
selectable: true
wakeLock: true

# Theme Configuration
themeConfig:
  primary: '#5b21b6'
  secondary: '#0891b2'

# Defaults
defaults:
  layout: default
  transition: fade

# SEO
htmlAttrs:
  lang: en
  dir: ltr
seoMeta:
  ogTitle: My Presentation
  ogDescription: Description for social sharing
  ogImage: https://example.com/cover.jpg
  twitterCard: summary_large_image
---
```

### Headmatter Options Reference

#### Theme & Appearance

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `theme` | string | `'default'` | Theme name or path |
| `colorSchema` | `'auto'` \| `'light'` \| `'dark'` | `'auto'` | Colour scheme |
| `background` | string | - | Global background (URL or gradient) |
| `class` | string | - | Global CSS classes |

#### Metadata

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `title` | string | `'Slidev'` | Presentation title |
| `titleTemplate` | string | `'%s - Slidev'` | Browser title template |
| `info` | string | - | Presentation description (markdown) |
| `author` | string | - | Author name (for exports) |
| `keywords` | string | - | Comma-separated keywords |

#### Features

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `mdc` | boolean | `false` | Enable MDC syntax |
| `monaco` | `boolean` \| `'dev'` \| `'build'` | `false` | Monaco editor |
| `lineNumbers` | boolean | `false` | Show line numbers in code blocks |
| `twoslash` | boolean | `false` | Enable TwoSlash for TypeScript |
| `download` | boolean | `false` | Show download button |
| `presenter` | boolean | `true` | Enable presenter mode |
| `record` | `boolean` \| `'dev'` \| `'build'` | `false` | Enable recording |
| `contextMenu` | boolean | `true` | Enable right-click menu |
| `selectable` | boolean | `true` | Allow text selection |
| `wakeLock` | boolean | `true` | Prevent screen sleep |

#### Transitions & Animations

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `transition` | string \| object | `'fade'` | Global slide transition |
| `drawings.enabled` | boolean | `true` | Enable drawing |
| `drawings.persist` | boolean | `false` | Save drawings |
| `drawings.presenterOnly` | boolean | `false` | Drawing in presenter only |
| `drawings.syncAll` | boolean | `true` | Sync drawings across devices |

#### Layout

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `aspectRatio` | number | `16/9` | Slide aspect ratio |
| `canvasWidth` | number | `980` | Canvas width (px) |
| `routerMode` | `'history'` \| `'hash'` | `'history'` | Router mode |

#### Fonts

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `fonts.sans` | string | - | Sans-serif font |
| `fonts.serif` | string | - | Serif font |
| `fonts.mono` | string | - | Monospace font |
| `fonts.weights` | string | `'200,400,600'` | Font weights |
| `fonts.italic` | boolean | `true` | Include italic variants |
| `fonts.provider` | `'google'` \| `'none'` | `'google'` | Font provider |
| `fonts.local` | string | - | Local font names |

#### Export

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `exportFilename` | string | `'slides-export'` | Export filename |
| `export.format` | `'pdf'` \| `'pptx'` \| `'png'` \| `'md'` | `'pdf'` | Export format |
| `export.timeout` | number | `30000` | Export timeout (ms) |
| `export.dark` | boolean | `false` | Export in dark mode |
| `export.withClicks` | boolean | `false` | Include click animations |
| `export.withToc` | boolean | `false` | Include PDF outline |

#### Code Highlighting

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `highlighter` | `'shiki'` | `'shiki'` | Code highlighter |
| `monacoTypesSource` | `'cdn'` \| `'local'` \| `'ata'` | `'cdn'` | Monaco types source |

#### Theme Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `themeConfig` | object | `{}` | Theme-specific configuration |

**Example**:
```yaml
---
themeConfig:
  primary: '#5b21b6'
  secondary: '#0891b2'
  logoUrl: /logo.png
---
```

#### Defaults

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `defaults.layout` | string | `'default'` | Default layout |
| `defaults.transition` | string | `'fade'` | Default transition |

## Per-Slide Frontmatter

Configure individual slides with frontmatter after slide separators.

### Per-Slide Options

```yaml
---
# Layout
layout: center

# Appearance
background: /image.jpg
class: text-white

# Behaviour
clicks: 5
clicksStart: 0
preload: true
disabled: false
hide: false
hideInToc: false

# Transition
transition: slide-left
zoom: 0.8

# Navigation
level: 1
title: Custom Title
routeAlias: solutions

# Import
src: ./pages/external.md

# Draggable positions
dragPos:
  element1: 100,200,300,50,0
---
```

### Per-Slide Options Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `layout` | string | `'default'` or `'cover'` | Slide layout |
| `background` | string | - | Background image or gradient |
| `class` | string | - | CSS classes for slide |
| `clicks` | number | `0` | Number of clicks |
| `clicksStart` | number | `0` | Starting click index |
| `transition` | string | - | Slide transition override |
| `zoom` | number | `1` | Content zoom level |
| `level` | number | `1` | Heading level for TOC |
| `title` | string | - | Slide title override |
| `hideInToc` | boolean | `false` | Hide from table of contents |
| `routeAlias` | string | - | Navigation alias |
| `src` | string | - | Import external slide |
| `preload` | boolean | `true` | Preload slide |
| `disabled` | boolean | `false` | Disable slide |
| `hide` | boolean | `false` | Hide slide completely |
| `dragPos` | object | `{}` | Draggable element positions |

## slidev.config.ts

TypeScript configuration file (optional, alternative to headmatter).

### Complete Example

```typescript
import { defineConfig } from '@slidev/cli'

export default defineConfig({
  // Theme
  theme: 'seriph',

  // Features
  highlighter: 'shiki',
  lineNumbers: true,
  monaco: 'dev',
  mdc: true,

  // Layout
  routerMode: 'history',
  aspectRatio: 16 / 9,
  canvasWidth: 980,

  // Fonts
  fonts: {
    sans: 'Inter',
    serif: 'Lora',
    mono: 'JetBrains Mono',
    weights: '300,400,600',
    provider: 'google',
  },

  // Drawing
  drawings: {
    enabled: true,
    persist: true,
    syncAll: true,
  },

  // Export
  exportFilename: 'presentation',
  download: true,

  // Transitions
  transition: 'slide-left',
})
```

## Setup Files

Advanced configuration through setup files in `./setup/` directory.

### Shiki Configuration

**File**: `setup/shiki.ts`

```typescript
import { defineShikiSetup } from '@slidev/types'

export default defineShikiSetup(() => {
  return {
    themes: {
      dark: 'nord',
      light: 'min-light',
    },
    transformers: [
      // Custom transformers
    ],
  }
})
```

### Monaco Configuration

**File**: `setup/monaco.ts`

```typescript
import { defineMonacoSetup } from '@slidev/types'

export default defineMonacoSetup(() => {
  return {
    editorOptions: {
      wordWrap: 'on',
      fontSize: 14,
      lineNumbers: 'on',
      minimap: { enabled: false },
      theme: 'vs-dark',
    }
  }
})
```

### Mermaid Configuration

**File**: `setup/mermaid.ts`

```typescript
import { defineMermaidSetup } from '@slidev/types'

export default defineMermaidSetup(() => {
  return {
    theme: 'forest',
    themeVariables: {
      primaryColor: '#ff0000',
      primaryTextColor: '#fff',
      primaryBorderColor: '#000',
    }
  }
})
```

### UnoCSS Configuration

**File**: `uno.config.ts`

```typescript
import { defineConfig } from 'unocss'
import { presetAttributify, presetUno } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetAttributify(),
  ],
  shortcuts: {
    'btn': 'px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600',
    'card': 'p-6 rounded-lg shadow-lg bg-white dark:bg-gray-800',
  },
  theme: {
    colors: {
      primary: '#5b21b6',
    },
  },
  safelist: [
    'i-carbon:checkmark',
    'i-mdi:github',
  ],
})
```

### App Setup

**File**: `setup/main.ts`

```typescript
import { defineAppSetup } from '@slidev/types'

export default defineAppSetup(({ app, router }) => {
  // Register global components
  app.component('MyComponent', MyComponent)

  // Router guards
  router.beforeEach((to, from) => {
    console.log('Navigating to:', to.path)
  })

  // Global properties
  app.config.globalProperties.$myUtil = () => {
    return 'Utility function'
  }
})
```

### Custom Shortcuts

**File**: `setup/shortcuts.ts`

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
      key: 'ctrl+shift+p',
      fn: () => nav.togglePresenter(),
    },
  ]
})
```

### Preparser/Transformers

**File**: `setup/preparser.ts`

```typescript
import { definePreparserSetup } from '@slidev/types'

export default definePreparserSetup(() => {
  return [
    {
      transformRawLines(lines) {
        for (let i = 0; i < lines.length; i++) {
          // Custom transformations
          if (lines[i] === '@@@')
            lines[i] = '---'
        }
      },
    }
  ]
})
```

## Vite Configuration

**File**: `vite.config.ts`

```typescript
import { defineConfig } from 'vite'

export default defineConfig({
  slidev: {
    vue: {
      /* Vue options */
    },
    markdown: {
      /* markdown-it options */
      markdownItSetup(md) {
        md.use(MyMarkdownPlugin)
      },
    },
  },
  server: {
    port: 3030,
  },
  build: {
    outDir: 'dist',
  },
})
```

## Configuration Priority

When the same option is set in multiple places:

1. Per-slide frontmatter (highest priority)
2. Headmatter
3. slidev.config.ts
4. Setup files
5. Default values (lowest priority)

## Common Configuration Patterns

### Minimal Setup
```yaml
---
theme: default
title: My Presentation
---
```

### Standard Professional
```yaml
---
theme: seriph
title: Technical Workshop
author: Jane Developer
mdc: true
lineNumbers: true
transition: slide-left
fonts:
  sans: Inter
  mono: JetBrains Mono
---
```

### Code-Heavy Presentation
```yaml
---
theme: default
title: Code Deep Dive
monaco: dev
lineNumbers: true
twoslash: true
highlighter: shiki
fonts:
  mono: JetBrains Mono
aspectRatio: 16/9
canvasWidth: 1200
---
```

### Conference Talk
```yaml
---
theme: seriph
title: Modern Web Development
info: |
  ## Conference Talk
  TechConf 2025
author: Jane Developer
download: true
exportFilename: techconf-2025-talk
drawings:
  enabled: true
  persist: false
record: dev
---
```

## Environment Variables

Set via `.env` file or environment:

```bash
# Development
SLIDEV_PORT=3030
SLIDEV_OPEN=true

# Export
SLIDEV_EXPORT_DARK=true
SLIDEV_EXPORT_WITH_CLICKS=false
```

## Configuration Troubleshooting

### Theme not loading
- Check theme name spelling
- Verify theme is installed: `npm list | grep slidev-theme`
- Try absolute path for local themes

### Fonts not appearing
- Verify `provider` is set correctly
- Check internet connection for CDN fonts
- Use local fonts if CDN is blocked

### Monaco not working
- Check `monaco: 'dev'` or `monaco: true` in config
- Verify TypeScript files have proper types
- Set `monacoTypesSource: 'ata'` for auto type acquisition

### Export failing
- Install playwright: `pnpm add -D playwright-chromium`
- Increase timeout: `export.timeout: 60000`
- Check for console errors during export

### Transitions not smooth
- Reduce `canvasWidth` for better performance
- Use simpler transitions
- Disable `drawings` if not needed
