# Slidev Troubleshooting Guide

Common issues and solutions when working with Slidev.

## Development Issues

### Slides Not Updating

**Problem**: Changes to `slides.md` not reflecting in browser

**Solutions**:
1. Hard refresh browser: `Cmd/Ctrl + Shift + R`
2. Clear Vite cache: `slidev --force`
3. Delete `.slidev` directory and restart:
   ```bash
   rm -rf .slidev
   slidev
   ```
4. Check for syntax errors in frontmatter (invalid YAML)

### Port Already in Use

**Problem**: Error: `Port 3030 is already in use`

**Solutions**:
1. Use different port: `slidev --port 8080`
2. Kill process on port 3030:
   ```bash
   lsof -ti:3030 | xargs kill -9
   ```
3. Set default port in `slidev.config.ts`:
   ```typescript
   export default defineConfig({
     port: 8080
   })
   ```

### Hot Reload Not Working

**Problem**: Changes require manual refresh

**Solutions**:
1. Check file watcher limits (Linux):
   ```bash
   echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
   sudo sysctl -p
   ```
2. Verify file is saved (check editor auto-save)
3. Try restart: `Ctrl+C` and `slidev` again

### Module Not Found Errors

**Problem**: `Cannot find module '@slidev/cli'` or similar

**Solutions**:
1. Install dependencies: `pnpm install`
2. Clear node_modules: `rm -rf node_modules && pnpm install`
3. Check Node.js version: `node --version` (need >= 18.0)
4. Verify in project directory with `package.json`

## Rendering Issues

### Layout Not Found

**Problem**: Error: `Layout "my-layout" not found`

**Solutions**:
1. Check layout exists in theme or `./layouts/`
2. Verify layout name spelling (case-sensitive)
3. For custom layouts, ensure file is `my-layout.vue` in `./layouts/`
4. Check theme documentation for available layouts

### Images Not Displaying

**Problem**: Images show broken icon or don't load

**Solutions**:
1. Verify path starts with `/` for public folder: `/image.png`
2. Check file exists in `public/` directory
3. Try absolute URL: `https://example.com/image.jpg`
4. Verify file extension is correct
5. Check browser console for 404 errors

### Fonts Not Loading

**Problem**: Custom fonts not appearing

**Solutions**:
1. Check internet connection (for Google Fonts)
2. Verify font name spelling in config:
   ```yaml
   fonts:
     sans: "Inter"  # Exact name
   ```
3. Try different provider: `provider: 'none'` for local fonts
4. Add local fonts to `public/fonts/` and use CSS:
   ```css
   @font-face {
     font-family: 'MyFont';
     src: url('/fonts/myfont.woff2');
   }
   ```

### Components Not Rendering

**Problem**: Vue components show as raw text

**Solutions**:
1. Check component file is in `./components/` directory
2. Verify file name matches component usage (case-sensitive)
3. Ensure component has proper `<template>` structure
4. Check for syntax errors in component
5. Try explicit import if auto-import fails:
   ```markdown
   <script setup>
   import MyComponent from './components/MyComponent.vue'
   </script>
   ```

### Code Blocks Not Highlighting

**Problem**: Code shows without syntax highlighting

**Solutions**:
1. Specify language: ` ```typescript ` not ` ``` `
2. Check language is supported by Shiki
3. Verify no syntax errors in code
4. Clear cache: `slidev --force`

### Mermaid Diagrams Not Rendering

**Problem**: Diagram shows as text or error

**Solutions**:
1. Validate syntax at [mermaid.live](https://mermaid.live)
2. Check for special characters that need escaping
3. Verify Mermaid block starts with ` ```mermaid `
4. Try simpler diagram first to isolate issue
5. Check browser console for errors

## Export Issues

### Export Command Not Found

**Problem**: `slidev export` fails with command not found

**Solutions**:
1. Install playwright: `pnpm add -D playwright-chromium`
2. Verify in project directory
3. Check `package.json` has correct scripts:
   ```json
   {
     "scripts": {
       "export": "slidev export"
     }
   }
   ```

### Export Hangs or Times Out

**Problem**: Export process freezes or times out

**Solutions**:
1. Increase timeout: `slidev export --timeout 60000`
2. Export specific range: `slidev export --range 1-10`
3. Disable Monaco if not needed: `monaco: false` in config
4. Check for infinite animations or loops
5. Try without clicks: `slidev export` (default no clicks)

### PDF Missing Content

**Problem**: Exported PDF missing elements or truncated

**Solutions**:
1. Add wait time: `slidev export --wait 2000`
2. Disable lazy loading: Set `preload: true` on heavy slides
3. Check CSS for `display: none` that should be removed
4. Verify all images loaded before export
5. Try browser export instead of CLI export

### Broken Emojis in PDF

**Problem**: Emojis render as boxes or missing characters

**Solutions**:
1. Install Noto Color Emoji font on system
2. Use images instead of emoji characters
3. Specify font fallback in CSS:
   ```css
   body {
     font-family: Inter, "Noto Color Emoji", sans-serif;
   }
   ```

### PPTX Export Issues

**Problem**: PowerPoint export fails or corrupted

**Solutions**:
1. Update Slidev: `pnpm update @slidev/cli`
2. Simplify slides (remove complex CSS/animations)
3. Export as PDF first to verify content
4. Check compatibility of components used
5. Try smaller slide ranges

## Monaco Editor Issues

### Monaco Not Loading

**Problem**: Code blocks with `{monaco}` don't show editor

**Solutions**:
1. Enable Monaco: `monaco: 'dev'` or `monaco: true` in headmatter
2. Clear cache: `slidev --force`
3. Check browser console for errors
4. Verify TypeScript configuration if using TS

### TypeScript Types Not Working

**Problem**: No IntelliSense or type errors in Monaco

**Solutions**:
1. Set types source: `monacoTypesSource: 'ata'` in frontmatter
2. Add types manually in `setup/monaco.ts`:
   ```typescript
   export default defineMonacoSetup(async (monaco) => {
     monaco.languages.typescript.javascriptDefaults.addExtraLib(
       'declare module "my-module" { ... }',
       'file:///my-module.d.ts'
     )
   })
   ```
3. Check internet connection (for CDN types)
4. Specify additional packages:
   ```yaml
   monacoTypesAdditionalPackages:
     - vue
     - lodash
   ```

### Monaco Running Code Fails

**Problem**: `{monaco-run}` doesn't execute or shows errors

**Solutions**:
1. Check for syntax errors in code
2. Verify browser console for runtime errors
3. Add dependencies in config:
   ```yaml
   monacoRunAdditionalDeps:
     - lodash@4.17.21
   ```
4. Test code in browser console first
5. Use try-catch for better error messages

## Animation & Transition Issues

### Click Animations Not Working

**Problem**: `v-click` elements don't appear on click

**Solutions**:
1. Verify syntax: `<div v-click>` or `<v-click>`
2. Check for conflicting CSS (opacity, display)
3. Ensure not in static export mode
4. Test in presenter mode
5. Check browser console for Vue errors

### Transitions Jerky or Slow

**Problem**: Slide transitions lag or stutter

**Solutions**:
1. Reduce `canvasWidth`: `canvasWidth: 800`
2. Use simpler transitions: `transition: fade`
3. Disable drawings if unused: `drawings.enabled: false`
4. Optimize images (compress, WebP format)
5. Limit concurrent animations
6. Test in production build: `slidev build`

### Motion Animations Not Smooth

**Problem**: `v-motion` animations choppy

**Solutions**:
1. Reduce animation complexity
2. Use hardware-accelerated properties (transform, opacity)
3. Avoid animating layout properties (width, height)
4. Test on target presentation device
5. Use spring animations with lower stiffness:
   ```javascript
   const config = {
     x: 0,
     transition: {
       type: 'spring',
       stiffness: 10,
       damping: 15
     }
   }
   ```

## Theme Issues

### Theme Not Applying

**Problem**: Theme setting in frontmatter has no effect

**Solutions**:
1. Install theme: `pnpm add slidev-theme-name`
2. Check theme name spelling (exact match)
3. Verify theme in `node_modules`
4. Try local theme path: `theme: ./my-theme`
5. Clear cache: `slidev --force`

### Theme Colors Wrong

**Problem**: Theme colours different than expected

**Solutions**:
1. Check `colorSchema` setting: `colorSchema: 'light'` or `'dark'`
2. Verify `themeConfig` matches theme's expected format
3. Override in custom CSS if needed
4. Check theme documentation for configuration options

### Theme Layout Missing

**Problem**: Theme's custom layout not available

**Solutions**:
1. Verify theme version supports layout
2. Check theme documentation for layout names
3. Inspect `node_modules/slidev-theme-*/layouts/`
4. Create custom layout if needed in `./layouts/`

## Build & Deployment Issues

### Build Fails

**Problem**: `slidev build` command fails

**Solutions**:
1. Check Node.js version: >= 18.0
2. Clear cache: `rm -rf .slidev dist`
3. Install dependencies: `pnpm install`
4. Check for syntax errors in slides
5. Review build output for specific errors
6. Try without optimisations: `slidev build --no-optimize`

### Static Site Not Working

**Problem**: Built site doesn't work when deployed

**Solutions**:
1. Set base path: `slidev build --base /slides/`
2. Check asset paths are relative
3. Verify server serves SPA correctly (fallback to index.html)
4. Test locally: `npx serve dist`
5. Check browser console for errors

### Assets Not Loading After Build

**Problem**: Images/videos 404 in production

**Solutions**:
1. Verify files in `public/` directory
2. Use absolute paths starting with `/`
3. Check base URL configuration
4. Ensure build includes public assets
5. Test with `npx serve dist` before deploying

## Performance Issues

### Slow Slide Load

**Problem**: Slides take long time to load/transition

**Solutions**:
1. Optimize images (compress, appropriate size)
2. Lazy load heavy slides: `preload: false`
3. Reduce `canvasWidth`
4. Disable unused features:
   ```yaml
   monaco: false
   drawings.enabled: false
   ```
5. Limit number of slides with heavy content

### High Memory Usage

**Problem**: Browser uses excessive memory

**Solutions**:
1. Reduce image sizes
2. Limit Monaco editors on single slide
3. Close other browser tabs
4. Use production build: `slidev build`
5. Disable dev tools when not needed

## Remote Control Issues

### Remote Not Connecting

**Problem**: Remote control URL doesn't work

**Solutions**:
1. Verify both devices on same network
2. Check firewall/network settings
3. Try different password: `slidev --remote newpass`
4. Use IP address instead of localhost
5. Check browser console for WebSocket errors

### Remote Sync Issues

**Problem**: Remote device out of sync with presenter

**Solutions**:
1. Refresh remote device browser
2. Check network stability
3. Verify `syncAll: true` in drawings config if using drawings
4. Test with simpler presentation first
5. Check for JavaScript errors on remote device

## Diagnostic Commands

### Check Slidev Version
```bash
pnpm list @slidev/cli
```

### Clear All Caches
```bash
rm -rf .slidev node_modules/.vite
pnpm install
slidev --force
```

### Verbose Logging
```bash
slidev --log debug
```

### Test Build
```bash
slidev build --no-bundle
npx serve dist
```

## Getting Help

If issues persist:

1. **Check Documentation**: https://sli.dev
2. **GitHub Issues**: Search existing issues at https://github.com/slidevjs/slidev/issues
3. **Discord Community**: https://chat.sli.dev
4. **Stack Overflow**: Tag with `slidev`

### Reporting Bugs

Include in bug report:
- Slidev version (`pnpm list @slidev/cli`)
- Node.js version (`node --version`)
- Operating system
- Minimal reproduction (simplified `slides.md`)
- Error messages (full stack trace)
- Browser console output (if relevant)
- Steps to reproduce

### Creating Minimal Reproduction

```yaml
---
theme: default
---

# Test Slide

This is a minimal test to reproduce the issue.

<!-- Describe the issue here -->
```

Save as `test-slides.md` and run: `slidev test-slides.md`
