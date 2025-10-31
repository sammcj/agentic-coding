# iA Presenter Starter Theme

This starter theme provides a foundation for creating custom iA Presenter themes.

## Files Included

- `template.json` - Theme metadata and configuration
- `presets.json` - Colour presets and gradients for light/dark modes
- `theme.css` - Main CSS file with commented sections for common customisations

## Quick Start

1. Copy all files to a new theme directory in iA Presenter's themes folder
2. Customise `template.json` with your theme name and author
3. Modify colours in `presets.json` for light and dark modes
4. Add your custom CSS to `theme.css`
5. Close and reopen iA Presenter to see changes

## File Descriptions

### template.json

Basic metadata for your theme:
- `Name` - Theme name shown in iA Presenter
- `Author` - Your name
- `Description` - Brief theme description
- `Css` - Name of your CSS file (should match the filename)
- `TitleFont` - Display name for title font
- `BodyFont` - Display name for body font

### presets.json

Colour configuration with separate values for light and dark modes:
- Text colours for body and titles
- Background colours
- Six accent colours
- Gradient colours (arrays of colour stops)

### theme.css

Starter CSS with commented sections for:
- Custom font declarations
- Typography (heading sizes, line heights)
- Layout alignments (centring, positioning)
- Backgrounds (images, SVGs, gradients)
- Headers and footers visibility
- Grid layout customisation
- Responsive breakpoints

## Tips

- Uncomment sections in `theme.css` to enable specific features
- Test in both light and dark modes
- Use the debugging borders technique (see advanced_techniques.md) during development
- Remember to close and reopen iA Presenter after CSS changes
- Use British English spelling in comments and documentation
