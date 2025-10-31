# iA Presenter Theme Quick Reference

Essential CSS classes, structure, and patterns for theme development.

---

## Layout Classes Reference

| Layout | Container Class | Content Class | Use Case |
|--------|----------------|---------------|----------|
| Cover | `.cover-container` | `.layout-cover` | Title slides, opening slides |
| Title | `.title-container` | `.layout-title` | Section titles (H2) |
| Section | `.section-container` | `.layout-section` | Subsection titles (H3) |
| Split | `.v-split-container` | `.layout-v-split` | Two-column layouts |
| Grid | `.grid-container` | `.layout-grid` | Multi-item grids |
| Caption | `.caption-container` | `.layout-caption` | Image with caption |
| Image Title | `.title-image-container` | `.layout-title-image` | Title with background image |
| Default | `.default-container` | `.layout-default` | Body text, lists |

## Grid Modifiers

Grid layouts have additional classes indicating item count:
- `.grid-items-2` - Two items
- `.grid-items-3` - Three items
- `.grid-items-4` - Four items
- And so on...

## Appearance Classes

- `.dark` - Dark mode appearance
- `.light` - Light mode appearance

## Alignment Properties

Target the inner `div` of layouts: `.layout-* > div`

### Horizontal Alignment
```css
align-items: flex-start;  /* Left */
align-items: center;      /* Centre */
align-items: flex-end;    /* Right */
```

### Vertical Alignment
```css
justify-content: flex-start;  /* Top */
justify-content: center;      /* Centre */
justify-content: flex-end;    /* Bottom */
```

## Common Selectors

```css
/* Hide headers on cover slides */
.cover-container .header { display: none; }

/* Style all backgrounds */
.slide-background { /* styles */ }

/* Target specific layout background */
.backgrounds .cover-container { /* styles */ }

/* Target grid with 3 items */
.grid-container.grid-items-3 { /* styles */ }

/* Dark mode specific */
.dark .layout-cover { /* styles */ }

/* Light mode specific */
.light .layout-cover { /* styles */ }
```

## File Structure

```
theme-name/
├── template.json          # Theme metadata and configuration
├── presets.json          # Colour presets and gradients
├── theme-name.css        # Main CSS file
├── thumbnail.png         # Theme preview (optional)
└── fonts/                # Custom fonts (optional)
    ├── Font-Regular.woff2
    └── Font-Bold.woff2
```

## template.json Structure

```json
{
  "Name": "Theme Name",
  "Version": 1.0,
  "Author": "Your Name",
  "ShortDescription": "Brief description",
  "LongDescription": "Detailed description\n- Feature 1\n- Feature 2",
  "Css": "theme-name.css",
  "TitleFont": "Font Display Name",
  "BodyFont": "Font Display Name",
  "Layouts": [
    {
      "Name": "Cover",
      "Classes": "invert"
    }
  ]
}
```

## presets.json Structure

```json
{
  "Presets": [
    {
      "Name": "Default",
      "TitleFont": "system-ui",
      "BodyFont": "system-ui",
      "Appearance": "dark",
      "DarkBodyTextColor": "#000000",
      "LightBodyTextColor": "#ffffff",
      "DarkTitleTextColor": "#000000",
      "LightTitleTextColor": "#ffffff",
      "DarkBackgroundColor": "#1a1a1a",
      "LightBackgroundColor": "#ffffff",
      "Accent1": "#f94144",
      "Accent2": "#43aa8b",
      "Accent3": "#f9c74f",
      "Accent4": "#90be6d",
      "Accent5": "#f8961e",
      "Accent6": "#577590",
      "LightBgGradient": ["#c7e7ff", "#f0c8ff", "#ffdada", "#ffebb2"],
      "DarkBgGradient": ["#15354c", "#3e154c", "#4c2828", "#4c3900"]
    }
  ]
}
```

## Font Face Declaration

```css
@font-face {
  font-family: 'Font Name';
  font-style: normal;
  font-weight: 400;
  src: url(Font-Regular.woff2) format('woff2');
}

@font-face {
  font-family: 'Font Name';
  font-style: normal;
  font-weight: 700;
  src: url(Font-Bold.woff2) format('woff2');
}
```

## Responsive Breakpoint

```css
/* Mobile first - default styles apply to mobile */

@media (min-width: 768px) {
  /* Desktop/tablet styles */
}
```

## Background Patterns

```css
/* Image background */
.backgrounds .layout-cover {
  background-image: url("image.jpg");
  background-size: cover;
  background-position: center;
}

/* Inline SVG background (use rgb() not hex) */
.backgrounds .layout-cover {
  background-image: url('data:image/svg+xml;utf8,<svg>...</svg>');
}

/* Gradient (defined in presets.json, not CSS) */
```

## Common Customisation Patterns

### Centre all text
```css
.layout-* > div {
  align-items: center;
  justify-content: center;
  text-align: center;
}
```

### Hide footers on all slides
```css
.footer { display: none; }
```

### Custom spacing
```css
.layout-default > div {
  padding: 2rem;
  gap: 1.5rem;
}
```

### Force dark mode on cover
```json
// In template.json
"Layouts": [
  {
    "Name": "Cover",
    "Classes": "dark"
  }
]
```
