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

### Extended Palette — Brand Ramps (50 lightest → 900 darkest)

Use these tokens for tints, shades, hover states, borders, and surfaces without introducing non-brand colours. Prefer the core step (bold) for each brand colour; reach for neighbouring steps when you need contrast adjustment.

**Ocean** — core `500`

```text
 50  #E8F2F8      500  #1E5E82   ← core
100  #C5DCEA      600  #174E6E
200  #9DC3D8      700  #103D57
300  #6AA5C3      800  #0A2D40
400  #3D89AF      900  #042031
```

**Flamingo** — core `500`

```text
 50  #FAEEF2      500  #D86E89   ← core
100  #F4D1DA      600  #C25079
200  #EDB0BE      700  #9E3456
300  #E690A2      800  #7A1E3D
400  #DE7F92      900  #550E28
```

**Sky** — core `400` (Sky's brand anchor sits at 400, not 500)

```text
 50  #F0FAFD      400  #81CCEA   ← core
100  #D9F1F9      500  #59BAE2
200  #B8E5F5      600  #329DD3
300  #95D6EF      700  #1B7EAD
                  800  #0E5F85
                  900  #064260
```

**Neutral** — greys for text, borders, dividers on light surfaces

```text
 50  #F5F7F9      500  #8A99AB
100  #DDE3EA      600  #5C6A7A
200  #C5CED9      700  #3E4F5E
300  #A8B5C4      800  #293C49
400  #B2BECC      900  #161C21
```

### Anchor Tokens (fixed, not on a ramp)

| Token | Hex | Use |
|---|---|---|
| Deep Ocean | `#002A41` | Primary dark background |
| Cloud | `#EEF9FD` | Primary light / neutral background |
| Skywalker 950 | `#001421` | Near-black dark surface |
| Skywalker 900 | `#001E2F` | Deepest dark section |
| Skywalker 800 | `#042D44` | Dark surface 2 |
| Skywalker 700 | `#073B58` | Dark surface 3 |
| Skywalker 600 | `#0C4F74` | Dark surface 4 (lightest dark) |

### Semantic Status Colours

Use these for success / warning / error / attention states. Do not substitute brand colours — overloading Flamingo for errors breaks the semantic contract users rely on.

| Token | Hex | Use |
|---|---|---|
| Yoda 600 | `#07883D` | Success / positive |
| BB8 600 | `#E87400` | Warning |
| Kylo 600 | `#D91544` | Error / danger |
| Pyre 300 | `#FFD60A` | Highlight / attention |

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

- Use Ocean for primary actions, main navigation, and brand-level emphasis
- Use Sky Blue for interactive elements, information, and secondary actions
- Use Flamingo sparingly for CTAs and brand highlights (not for errors — use Kylo)
- Use Deep Ocean for text, borders, authoritative elements
- Use Cloud for backgrounds, subtle dividers, inactive states
- Use the semantic status colours (Yoda / BB8 / Kylo / Pyre) for success / warning / error / attention — never substitute brand colours for these
- Default to light / day mode colour schemes

### Consistency Rules

- Avoid mixing colour schemes from other brands
- Maintain consistent colour meanings across all diagrams in a project
- When transparency is needed, use rgba values of the brand colours
- For hover/pressed states, step one rung on the brand ramp (e.g. `ocean-500` → `ocean-600` on hover, `flamingo-500` → `flamingo-600` on press). Only fall back to percentage darken/lighten if no ramp token fits

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
- Background: Flamingo 500 (#D86E89)
- Text: White (#FFFFFF)
- Hover: Flamingo 600 (#C25079)
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
- Error Border: Kylo 600 (#D91544)

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

Use the semantic status colours — do not overload Flamingo for errors/warnings or Ocean for success.

**Error:**
- Background: Kylo 600 (#D91544) at 10% opacity
- Border: Kylo 600 (#D91544)
- Text: Deep Ocean (#002A41)
- Icon: Kylo 600 (#D91544)

**Warning:**
- Background: BB8 600 (#E87400) at 10% opacity
- Border: BB8 600 (#E87400)
- Text: Deep Ocean (#002A41)
- Icon: BB8 600 (#E87400)

**Success:**
- Background: Yoda 600 (#07883D) at 10% opacity
- Border: Yoda 600 (#07883D)
- Text: Deep Ocean (#002A41)
- Icon: Yoda 600 (#07883D)

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
   /* Core brand (anchor steps) */
   --brand-ocean: #1E5E82;        /* ocean-500 */
   --brand-flamingo: #D86E89;     /* flamingo-500 */
   --brand-sky-blue: #81CCEA;     /* sky-400 */
   --brand-deep-ocean: #002A41;
   --brand-cloud: #EEF9FD;

   /* Ocean ramp */
   --ocean-50:  #E8F2F8; --ocean-100: #C5DCEA; --ocean-200: #9DC3D8;
   --ocean-300: #6AA5C3; --ocean-400: #3D89AF; --ocean-500: #1E5E82;
   --ocean-600: #174E6E; --ocean-700: #103D57; --ocean-800: #0A2D40;
   --ocean-900: #042031;

   /* Flamingo ramp */
   --flamingo-50:  #FAEEF2; --flamingo-100: #F4D1DA; --flamingo-200: #EDB0BE;
   --flamingo-300: #E690A2; --flamingo-400: #DE7F92; --flamingo-500: #D86E89;
   --flamingo-600: #C25079; --flamingo-700: #9E3456; --flamingo-800: #7A1E3D;
   --flamingo-900: #550E28;

   /* Sky ramp */
   --sky-50:  #F0FAFD; --sky-100: #D9F1F9; --sky-200: #B8E5F5;
   --sky-300: #95D6EF; --sky-400: #81CCEA; --sky-500: #59BAE2;
   --sky-600: #329DD3; --sky-700: #1B7EAD; --sky-800: #0E5F85;
   --sky-900: #064260;

   /* Neutral greys */
   --neutral-50:  #F5F7F9; --neutral-100: #DDE3EA; --neutral-200: #C5CED9;
   --neutral-300: #A8B5C4; --neutral-400: #B2BECC; --neutral-500: #8A99AB;
   --neutral-600: #5C6A7A; --neutral-700: #3E4F5E; --neutral-800: #293C49;
   --neutral-900: #161C21;

   /* Dark surfaces */
   --skywalker-950: #001421; --skywalker-900: #001E2F; --skywalker-800: #042D44;
   --skywalker-700: #073B58; --skywalker-600: #0C4F74;

   /* Semantic status */
   --yoda-600: #07883D;  /* success */
   --bb8-600:  #E87400;  /* warning */
   --kylo-600: #D91544;  /* error */
   --pyre-300: #FFD60A;  /* highlight */

   /* Semantic mappings */
   --colour-primary: var(--brand-ocean);
   --colour-primary-dark: var(--brand-deep-ocean);
   --colour-secondary: var(--brand-sky-blue);
   --colour-accent: var(--brand-flamingo);
   --colour-background: var(--brand-cloud);
   --colour-surface: #FFFFFF;

   /* Text */
   --text-primary: var(--brand-deep-ocean);
   --text-secondary: var(--brand-ocean);
   --text-on-primary: var(--brand-cloud);
   --text-on-accent: #FFFFFF;

   /* State (semantic status — do not substitute brand colours) */
   --colour-error: var(--kylo-600);
   --colour-warning: var(--bb8-600);
   --colour-success: var(--yoda-600);
   --colour-info: var(--brand-sky-blue);
   --colour-highlight: var(--pyre-300);

   /* Shadows and overlays */
   --shadow-colour: rgba(0, 42, 65, 0.1);
   --overlay-light: rgba(238, 249, 253, 0.9);
   --overlay-dark: rgba(0, 42, 65, 0.8);
}
```

### Tailwind Configuration

Tailwind's config key is `colors` (American spelling) — this is required by the framework regardless of project-wide spelling conventions.

```js
module.exports = {
   theme: {
      extend: {
         colors: {
            brand: {
               ocean: '#1E5E82',
               flamingo: '#D86E89',
               'sky-blue': '#81CCEA',
               'deep-ocean': '#002A41',
               cloud: '#EEF9FD',
            },
            ocean: {
               50: '#E8F2F8', 100: '#C5DCEA', 200: '#9DC3D8',
               300: '#6AA5C3', 400: '#3D89AF', 500: '#1E5E82',
               600: '#174E6E', 700: '#103D57', 800: '#0A2D40',
               900: '#042031',
            },
            flamingo: {
               50: '#FAEEF2', 100: '#F4D1DA', 200: '#EDB0BE',
               300: '#E690A2', 400: '#DE7F92', 500: '#D86E89',
               600: '#C25079', 700: '#9E3456', 800: '#7A1E3D',
               900: '#550E28',
            },
            sky: {
               50: '#F0FAFD', 100: '#D9F1F9', 200: '#B8E5F5',
               300: '#95D6EF', 400: '#81CCEA', 500: '#59BAE2',
               600: '#329DD3', 700: '#1B7EAD', 800: '#0E5F85',
               900: '#064260',
            },
            neutral: {
               50: '#F5F7F9', 100: '#DDE3EA', 200: '#C5CED9',
               300: '#A8B5C4', 400: '#B2BECC', 500: '#8A99AB',
               600: '#5C6A7A', 700: '#3E4F5E', 800: '#293C49',
               900: '#161C21',
            },
            skywalker: {
               600: '#0C4F74', 700: '#073B58', 800: '#042D44',
               900: '#001E2F', 950: '#001421',
            },
            // Semantic status (single-step anchors)
            yoda: '#07883D',   // success
            bb8:  '#E87400',   // warning
            kylo: '#D91544',   // error
            pyre: '#FFD60A',   // highlight
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
