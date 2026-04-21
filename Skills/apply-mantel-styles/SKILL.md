---
name: apply-mantel-styles
description: Provides guidelines for applying Mantel's brand styles to diagrams and frontend components. Use when asked to create visuals that need to align with Mantel's branding.
---

# Rules For Applying Mantel Brand Styles

When creating visual diagrams or frontend components, you can apply the following style guidelines to ensure consistency with the Mantel brand identity.

## Colour Scheme

- You should aim to use the following primary colours from the Mantel brand palette.
- You _may_ also use tints and shades of these colours as needed, but avoid introducing non-brand colours.

### Palette

| Name       | Hex       | RGB                  |
|------------|-----------|----------------------|
| Ocean      | `#1E5E82` | rgb(30, 94, 130)     |
| Flamingo   | `#D86E89` | rgb(216, 110, 137)   |
| Deep Ocean | `#002A41` | rgb(0, 42, 65)       |
| Sky Blue   | `#81CCEA` | rgb(129, 204, 234)   |
| Cloud      | `#EEF9FD` | rgb(238, 249, 253)   |

### Extended Palette (derived — use sparingly)

| Name           | Hex       | Usage                                                  |
|----------------|-----------|--------------------------------------------------------|
| Card Dark      | `#0A3A55` | Slightly lighter than Deep Ocean — cards on dark bg     |
| Ocean Light    | `#2A7AA3` | Mid-tone for gradients or hover states                  |
| Flamingo Light | `#E8A0B3` | Softer pink for backgrounds or disabled states          |
| Text on Dark   | `#FFFFFF` | White text on Deep Ocean / Ocean backgrounds            |
| Text on Light  | `#002A41` | Deep Ocean text on Cloud / white backgrounds            |

---

## General Design Principles

### Colour Hierarchy

1. Primary Actions/Elements: Ocean (#1E5E82)
2. Secondary/Supporting: Sky Blue (#81CCEA)
3. Emphasis/Accent: Flamingo (#D86E89)
4. Foundation/Authority: Deep Ocean (#002A41)
5. Background/Neutral: Cloud (#EEF9FD)

- **Light backgrounds** use Cloud (`#EEF9FD`) or white (`#FFFFFF`).
- **Dark backgrounds** use Deep Ocean (`#002A41`). Never use pure black (`#000000`).
- **Primary text** on light backgrounds is Deep Ocean. On dark backgrounds, use white.
- **Accent elements** (borders, icons, highlights) use Ocean, Flamingo, or Sky Blue.

### Semantic Usage

- Use Ocean for primary actions, main navigation, success states
- Use Sky Blue for interactive elements, information, secondary actions
- Use Flamingo sparingly for CTAs, warnings, important highlights
- Use Deep Ocean for text, borders, authoritative elements
- Use Cloud for backgrounds, subtle dividers, inactive states
- Default to light / day mode colour schemes

### Consistency Rules

- Avoid mixing colour schemes from other brands
- Maintain consistent colour meanings across all diagrams in a project
- When transparency is needed, use rgba values of the brand colours
- For hover states, darken by 10-15% or lighten by 10-15% staying within brand

---

## Frontend Component Styles

### Component Guidelines

#### Buttons

**Primary:**
- Background: Ocean (#1E5E82)
- Text: Cloud (#EEF9FD)
- Hover: Deep Ocean (#002A41)
- Border: none or Ocean

**Secondary:**
- Background: Sky Blue (#81CCEA)
- Text: Deep Ocean (#002A41)
- Hover: Ocean (#1E5E82) with Cloud text
- Border: Ocean (#1E5E82)

**Accent/CTA:**
- Background: Flamingo (#D86E89)
- Text: White (#FFFFFF)
- Hover: Darker Flamingo (darken by 10%)
- Border: none

**Ghost/Outline:**
- Background: transparent
- Text: Ocean (#1E5E82)
- Hover: Cloud (#EEF9FD) background
- Border: Ocean (#1E5E82)

#### Navigation

**Header:**
- Background: Deep Ocean (#002A41)
- Text: Cloud (#EEF9FD)
- Active: Sky Blue (#81CCEA)
- Hover: Ocean (#1E5E82) background

**Sidebar:**
- Background: Cloud (#EEF9FD)
- Text: Deep Ocean (#002A41)
- Active: Ocean (#1E5E82) with Cloud text
- Hover: Sky Blue (#81CCEA) background

#### Forms

**Input Fields:**
- Background: White (#FFFFFF)
- Border: Sky Blue (#81CCEA)
- Focus Border: Ocean (#1E5E82)
- Text: Deep Ocean (#002A41)
- Placeholder: Sky Blue (#81CCEA)
- Error Border: Flamingo (#D86E89)

**Labels:**
- Colour: Ocean (#1E5E82)
- Required Indicator: Flamingo (#D86E89)

#### Cards and Surfaces

**Standard Card:**
- Background: White (#FFFFFF)
- Border: Cloud (#EEF9FD)
- Shadow: rgba(0, 42, 65, 0.1)

**Highlighted Card:**
- Background: Cloud (#EEF9FD)
- Border: Sky Blue (#81CCEA)
- Shadow: rgba(30, 94, 130, 0.15)

#### Alerts and Messages

**Error:**
- Background: Flamingo (#D86E89) at 10% opacity
- Border: Flamingo (#D86E89)
- Text: Deep Ocean (#002A41)
- Icon: Flamingo (#D86E89)

**Warning:**
- Background: Flamingo (#D86E89) at 5% opacity
- Border: Flamingo (#D86E89) at 50%
- Text: Deep Ocean (#002A41)
- Icon: Flamingo (#D86E89)

**Success:**
- Background: Ocean (#1E5E82) at 10% opacity
- Border: Ocean (#1E5E82)
- Text: Deep Ocean (#002A41)
- Icon: Ocean (#1E5E82)

**Info:**
- Background: Sky Blue (#81CCEA) at 10% opacity
- Border: Sky Blue (#81CCEA)
- Text: Deep Ocean (#002A41)
- Icon: Sky Blue (#81CCEA)

#### Data Visualisation (Charts)

- Primary Series: Ocean (#1E5E82)
- Secondary Series: Sky Blue (#81CCEA)
- Tertiary Series: Deep Ocean (#002A41)
- Highlight/Accent: Flamingo (#D86E89)
- Background: Cloud (#EEF9FD)
- Grid Lines: Sky Blue (#81CCEA) at 20% opacity
- Text: Deep Ocean (#002A41)


### CSS Variables

```css
:root {
   /* Primary Colours */
   --brand-ocean: #1E5E82;
   --brand-flamingo: #D86E89;
   --brand-deep-ocean: #002A41;
   --brand-sky-blue: #81CCEA;
   --brand-cloud: #EEF9FD;

   /* Semantic Mappings */
   --colour-primary: var(--brand-ocean);
   --colour-primary-dark: var(--brand-deep-ocean);
   --colour-secondary: var(--brand-sky-blue);
   --colour-accent: var(--brand-flamingo);
   --colour-background: var(--brand-cloud);
   --colour-surface: #FFFFFF;

   /* Text Colours */
   --text-primary: var(--brand-deep-ocean);
   --text-secondary: var(--brand-ocean);
   --text-on-primary: var(--brand-cloud);
   --text-on-accent: #FFFFFF;

   /* State Colours */
   --colour-error: var(--brand-flamingo);
   --colour-warning: var(--brand-flamingo);
   --colour-success: var(--brand-ocean);
   --colour-info: var(--brand-sky-blue);

   /* Shadows and Overlays */
   --shadow-colour: rgba(0, 42, 65, 0.1);
   --overlay-light: rgba(238, 249, 253, 0.9);
   --overlay-dark: rgba(0, 42, 65, 0.8);
}
```

### Tailwind Configuration

```js
module.exports = {
   theme: {
      extend: {
         colours: {
            'brand': {
               'ocean': '#1E5E82',
               'flamingo': '#D86E89',
               'deep-ocean': '#002A41',
               'sky-blue': '#81CCEA',
               'cloud': '#EEF9FD',
            }
         }
      }
   }
}
```

---

## Fonts & Typography

- Where applicable, the 'Inter' typeface is used for headlines, subheadings, and body copy.
- Favour bundling the font for offline use over relying on CDNs.

| Role        | Font  | Weight   | CSS                 |
|-------------|-------|----------|---------------------|
| Headlines   | Inter | SemiBold | `font-weight: 600`  |
| Subheadings | Inter | Medium   | `font-weight: 500`  |
| Body copy   | Inter | Regular  | `font-weight: 400`  |

### Inter CDN Fallback

If bundling is not possible, use this CDN:

```html
<!-- HTML in your document's head -->
<link rel="preconnect" href="https://rsms.me/">
<link rel="stylesheet" href="https://rsms.me/inter/inter.css">
```

```css
:root {
  font-family: Inter, sans-serif;
  font-feature-settings: 'liga' 1, 'calt' 1; /* fix for Chrome */
}
@supports (font-variation-settings: normal) {
  :root { font-family: InterVariable, sans-serif; }
}
```

---

## Logo System

### Logo Variants

The skill bundles all logo files in `assets/`. Selection guide:

| File                        | Use when…                                          |
|-----------------------------|----------------------------------------------------|
| `Mantel_Logo__Positive.svg` | Full-colour logo on **light** backgrounds           |
| `Mantel_Logo__Negative.svg` | Full-colour logo on **dark** backgrounds            |
| `Mantel_Logo__Navy.svg`     | Mono (Deep Ocean) logo on **light** backgrounds     |
| `Mantel_Logo__White.svg`    | Mono (white) logo on **dark** backgrounds           |
| `Mantel_Icon__Positive.svg` | Full-colour icon only, on **light** backgrounds     |
| `Mantel_Icon__Negative.svg` | Full-colour icon only, on **dark** backgrounds      |
| `Mantel_Icon__Navy.svg`     | Mono (Deep Ocean) icon, on **light** backgrounds    |
| `Mantel_Icon__White.svg`    | Mono (white) icon, on **dark** backgrounds          |

### Logo Rules (critical — violations are immediately visible)

1. **Never stretch or distort.** Logo aspect ratio is approximately 4.67:1. Icon is approximately 1.5:1. Always preserve proportions.
2. **Never change logo colours.** Use only the provided variants — never recolour the icon or wordmark.
3. **Never crop the logo.** All elements must be fully visible.
4. **Minimum clear space** around the logo equals the height and width of the icon portion.
5. **Minimum sizes:** Logo 80px / 21mm wide. Icon 44px / 12mm wide.
6. **Light logo on light background = wrong.** Dark logo on dark background = wrong. Always use the variant that contrasts with the background.
7. **Preferred for client-facing materials:** Use the full-colour Negative logo on Deep Ocean backgrounds. This is the most common and branded combination.
8. **Never add a coloured border around the logo** — the brand guide explicitly prohibits this.

---

## Resources

If you are creating diagrams you MUST also read in ./resources/diagrams.md

---

This information should help you maintain visual consistency with the Mantel brand across diagrams and frontend components.
