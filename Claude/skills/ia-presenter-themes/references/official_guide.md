# iA Presenter Custom Themes - Official Guide

This is the official iA Presenter documentation for creating custom themes.

Source: https://ia.net/presenter/support/visuals/themes

---

## Custom Themes

Aside from choosing from iA Presenter's default Themes, you can create your own custom themes too.

You can change your presentation's style by:
- Using a specific *theme* and its *CSS*
- Using *presets*
- Selecting different layouts, depending on your slide content (auto-layout)
- Defining *CSS variables* in the Style Inspector

💡 Creating custom themes requires some knowledge of HTML and CSS.

## Theme Structure

Every theme consists of:
1. Themes assets
2. Presets (predefined sets of CSS variables)
3. Custom fonts
4. Theme CSS definitions
5. Theme thumbnail
6. Theme definition

## Slides HTML Structures

- A presentation has a collection of *slide containers* and a collection of *slide backgrounds*
- Each slide generates a *slide container* and a *slide background* DIVs
- The *slide background* has the same layout CSS class as the *slide container*
- If there are no footnotes, the footnotes DIV has 0 height
- If there are no headers and footers, the slide content occupies all the available space
- You can choose to hide headers/footers on a per-layout basis: `.cover-container .header{ display:none;}`

## Layouts

### Cover
- Container CSS Class: `.cover-container`
- Slide Content CSS Class: `.layout-cover`

### Title
- Container CSS Class: `.title-container`
- Slide Content CSS Class: `.layout-title`

### Section
- Container CSS Class: `.section-container`
- Slide Content CSS Class: `.layout-section`

### Split
- Container CSS Class: `.v-split-container`
- Slide Content CSS Class: `.layout-v-split`

### Grid
- Container CSS Class: `.grid-container`
- Slide Content CSS Class: `.layout-grid`

The **Grid** layout also has a CSS class indicating the number of grid cells at the slide content DIV level: `grid-items-2`, `grid-items-3`, `grid-items-4`, and so forth.

### Caption
- Container CSS Class: `.caption-container`
- Slide Content CSS Class: `.layout-caption`

### Image Title
- Container CSS Class: `.title-image-container`
- Slide Content CSS Class: `.layout-title-image`

### Default (Text)
- Container CSS Class: `.default-container`
- Slide Content CSS Class: `.layout-default`

## Custom Fonts

Follow these steps to add a custom font to your theme:

### 1. Add the Font Files to Your Theme Folder

Example:
```
Roboto-Slab-Regular.woff2
Roboto-Slab-Bold.woff2
```

### 2. Reference these Fonts at the Beginning of Your CSS

```css
@font-face {
  font-family: 'Roboto Slab';
  font-style: normal;
  font-weight: 400;
  src: url(Roboto-Slab-Regular.woff2) format('woff2');
}
@font-face {
  font-family: 'Roboto Slab';
  font-style: normal;
  font-weight: 700;
  src: url(roboto-slab-Bold.woff2) format('woff2');
}
```

### 3. Inform Metadata

#### In `template.json`

```json
"TitleFont": "New York",
"BodyFont": "New York",
```

Here you need to inform the **display name** of your custom fonts. That's the name that will appear in the Style Inspector.

#### In `presets.json`

```json
"TitleFont": "-apple-system-ui-serif, ui-serif",
"BodyFont": "-apple-system-ui-serif, ui-serif",
```

Here you need to inform the **CSS name** of your custom font. The name may differ from the display name.

💡 You could directly set your custom font in CSS, but would lose the ability to override it using the Style Inspector.

## Using Images From Your Theme in CSS

When your custom theme is installed, iA Presenter preserves the directory structure.

You can then reference an image using the `url(...)` function:

```css
.backgrounds .default-container{
  background-image: url("image1.jpg");
  background-size: cover;
  background-position: center;
}
```

## Alignments

You need to target the inner div of each layout.

Example:
```css
.layout-cover > div {
    justify-content: flex-end; /* vertical alignment */
    align-items: flex-start; /* horizontal alignment */
}
```

### Horizontal Alignment

Property: `align-items`

| Alignment | Value |
|-----------|-------|
| Left | `flex-start` |
| Centre | `center` |
| Right | `flex-end` |

### Vertical Alignment

Property: `justify-content`

| Alignment | Value |
|-----------|-------|
| Top | `flex-start` |
| Centre | `center` |
| Bottom | `flex-end` |

## Backgrounds

- You can use regular bitmap images (`.jpg`, `.png`) as well as SVG backgrounds
- Background images can also be inlined directly in the CSS
- You can target a specific layout:

```css
.backgrounds .v-split-container{
  background-image: url('data:image/svg+xml;utf8,<svg viewBox="0 0 1024 600" xmlns="http://www.w3.org/2000/svg" xml:space="preserve" fill-rule="evenodd" clip-rule="evenodd" stroke-linejoin="round" stroke-miterlimit="2"><path fill="red" d="m541.526-57.455 584.065 49.14-56.35 669.755-584.065-49.14z"/></svg>');
  background-size: cover;
  background-position: center;
}
```

⚠️ If you use inline SVG as the URL directly in your CSS files, you need to take care of how you declare colours. Colours in hexadecimal format (like `#FFFFFF`) will break your CSS. Use the `rgb(0,0,0)` format instead.

If you want to target all backgrounds regardless of the layout, target the `.slide-background` class.

## Gradient Background

- You need to define two different gradients: one per appearance (Light/Dark)
- These gradients are defined in the `presets.json` file

Example:
```json
{
  "Presets": [
    {
      "Name": "Default",
      "TitleFont": "system-ui",
      "BodyFont": "system-ui",
      "Appearance" : "dark",
      "DarkBodyTextColor": "#000000",
      "LightBodyTextColor": "#ffffff",
      "DarkTitleTextColor": "#000000",
      "LightTitleTextColor": "#ffffff",
      "DarkBackgroundColor": "transparent",
      "LightBackgroundColor": "transparent",
      "Accent1": "#f94144",
      "Accent2": "#43aa8b",
      "Accent3": "#f9c74f",
      "Accent4": "#90be6d",
      "Accent5": "#f8961e",
      "Accent6": "#577590",
      "LightBgGradient":[
          "#c7e7ff",
          "#f0c8ff",
          "#ffdada",
          "#ffebb2"
      ],
      "DarkBgGradient":[
          "#15354c",
          "#3e154c",
          "#4c2828",
          "#4c3900"
      ]
    }
  ]
}
```

## Appearances

iA Presenter uses the `.dark` and `.light` CSS classes. These classes are set per layout. You can force the appearance for a specific layout in a custom Theme, in the `template.json` file:

```json
{
  "Name": "New York",
  "Version": 0.1,
  "Author": "iA",
  "ShortDescription": "Stylish, bold, classy.",
  "LongDescription": "Stylish, bold, classy\n- Different sizes for headlines\n- Simple color background\n- Default white on black\n- Default font: New York",
  "Css": "newyork.css",
  "TitleFont": "New York",
  "BodyFont": "New York",
  "Layouts":[
     {
          "Name": "Cover",
          "Classes": "invert",
     },
     {
          "Name": "Title",
          "Classes": "invert",
     }
  ]
}
```

## Responsiveness

iA Presenter themes are responsive. By default, CSS applies to mobile devices. If you want to target non-mobile devices:

```css
@media (min-width: 768px) {
  ...
}
```

You can add additional breakpoints if you want to provide different font-size/margins depending on the viewport size. However, iA Presenter already has its logic, and defaults should be sufficient.

## Developing Custom Themes

### 1. Create a New Theme

Go to **Settings** → **Themes**. Click on **+**, **Create Theme** and enter a name.

### 2. Navigate to the New Theme Files

Click on the **Reveal Themes folder in Finder** button. Navigate to the folder of the newly created Theme.

### 3. Use Your New Theme

Open a presentation, go to the **Theme and Style** tab in the Inspector, and set the newly created theme.

### 4. Bring Your Modification

Open your `Theme.css` in your preferred editor and add your custom CSS.
