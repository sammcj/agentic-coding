---
name: liteparse
description: Provides fast document to markdown extraction. Use this skill when the user asks to parse, perform multi-format document conversion or spatially extract text from an unstructured file (PDF, DOCX, PPTX, XLSX, images, etc.) locally.
---

# LiteParse Skill

Parse unstructured documents (PDF, DOCX, PPTX, XLSX, images, and more) locally with LiteParse: fast, lightweight, no cloud dependencies or LLM required.

## Step 0 - Use via npx, or install LiteParse

NOTE: Rather than installing `liteparse` globally, you can instead run it directly with `npx`, substituting `lit <args>` with `npx -y @llamaindex/liteparse <args>` in the commands below.

```bash
npx -y @llamaindex/liteparse
```

Otherwise if installing globally, use `pnpm install -g @llamaindex/liteparse` and then run `lit <args>`.

---

## Step 1 - Produce the CLI Command or Script

### Parse a Single File

```bash
# Basic text extraction
lit parse document.pdf

# JSON output saved to a file
lit parse document.pdf --format json -o output.json

# Specific page range
lit parse document.pdf --target-pages "1-5,10,15-20"

# Disable OCR (faster, text-only PDFs)
lit parse document.pdf --no-ocr

# Use an external HTTP OCR server for higher accuracy
lit parse document.pdf --ocr-server-url http://localhost:8828/ocr

# Higher DPI for better quality
lit parse document.pdf --dpi 300
```

### Batch Parse a Directory

```bash
lit batch-parse ./input-directory ./output-directory

# Only process PDFs, recursively
lit batch-parse ./input ./output --extension .pdf --recursive
```

### Generate Page Screenshots

Screenshots are useful for LLM agents that need to see visual layout.

```bash
# All pages
lit screenshot document.pdf -o ./screenshots

# Specific pages
lit screenshot document.pdf --pages "1,3,5" -o ./screenshots

# High-DPI PNG
lit screenshot document.pdf --dpi 300 --format png -o ./screenshots

# Page range
lit screenshot document.pdf --pages "1-10" -o ./screenshots
```

---

## Step 3 - Key Options Reference

### OCR Options

| Option | Description |
|--------|-------------|
| (default) | Tesseract.js - zero setup, built-in |
| `--ocr-language fra` | Set OCR language (ISO code) |
| `--ocr-server-url <url>` | Use external HTTP OCR server (EasyOCR, PaddleOCR, custom) |
| `--no-ocr` | Disable OCR entirely |

### Output Options

| Option | Description |
|--------|-------------|
| `--format json` | Structured JSON with bounding boxes |
| `--format text` | Plain text (default) |
| `-o <file>` | Save output to file |

### Performance / Quality Options

| Option | Description |
|--------|-------------|
| `--dpi <n>` | Rendering DPI (default: 150; use 300 for high quality) |
| `--max-pages <n>` | Limit pages parsed |
| `--target-pages <pages>` | Parse specific pages (e.g. `"1-5,10"`) |
| `--no-precise-bbox` | Disable precise bounding boxes (faster) |
| `--skip-diagonal-text` | Ignore rotated/diagonal text |
| `--preserve-small-text` | Keep very small text that would otherwise be dropped |

---

## Step 4 - Using a Config File

For repeated use with consistent options, generate a `liteparse.config.json`:

```json
{
  "ocrLanguage": "en",
  "ocrEnabled": true,
  "maxPages": 1000,
  "dpi": 150,
  "outputFormat": "json",
  "preciseBoundingBox": true,
  "skipDiagonalText": false,
  "preserveVerySmallText": false
}
```

For an HTTP OCR server:

```json
{
  "ocrServerUrl": "http://localhost:8828/ocr",
  "ocrLanguage": "en",
  "outputFormat": "json"
}
```

Use with:

```bash
lit parse document.pdf --config liteparse.config.json
```

---

## Step 5 - HTTP OCR Server API (Advanced)

If the user wants to plug in a custom OCR backend, the server must implement:

- **Endpoint**: `POST /ocr`
- **Accepts**: `file` (multipart) and `language` (string) parameters
- **Returns**:
```json
{
  "results": [
    { "text": "Hello", "bbox": [x1, y1, x2, y2], "confidence": 0.98 }
  ]
}
```

Ready-to-use wrappers exist for EasyOCR and PaddleOCR in the LiteParse repo.

---

## Supported Input Formats

| Category | Formats |
|----------|---------|
| PDF | `.pdf` |
| Word | `.doc`, `.docx`, `.docm`, `.odt`, `.rtf` |
| PowerPoint | `.ppt`, `.pptx`, `.pptm`, `.odp` |
| Spreadsheets | `.xls`, `.xlsx`, `.xlsm`, `.ods`, `.csv`, `.tsv` |
| Images | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.webp`, `.svg` |

Office documents require LibreOffice; images require ImageMagick. LiteParse auto-converts these formats to PDF before parsing.
