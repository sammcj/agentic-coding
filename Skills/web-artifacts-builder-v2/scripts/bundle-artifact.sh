#!/bin/bash
set -e

echo "Bundling React app to a single self-contained HTML file..."

if [ ! -f "package.json" ]; then
  echo "Error: no package.json found. Run this from your project root."
  exit 1
fi

if [ ! -f "index.html" ]; then
  echo "Error: no index.html in project root."
  exit 1
fi

echo "Installing bundling dependency (vite-plugin-singlefile)..."
pnpm add -D vite-plugin-singlefile

echo "Writing vite.config.bundle.ts (single-file build config)..."
cat > vite.config.bundle.ts << 'EOF'
import path from "path";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { viteSingleFile } from "vite-plugin-singlefile";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss(), viteSingleFile()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    target: "esnext",
    assetsInlineLimit: 100000000,
    chunkSizeWarningLimit: 100000000,
    cssCodeSplit: false,
    reportCompressedSize: false,
    rollupOptions: {
      output: {
        inlineDynamicImports: true,
      },
    },
  },
});
EOF

echo "Cleaning previous bundle..."
rm -rf dist bundle.html

echo "Building..."
pnpm exec vite build --config vite.config.bundle.ts

if [ ! -f "dist/index.html" ]; then
  echo "Error: build did not produce dist/index.html"
  exit 1
fi

mv dist/index.html bundle.html

FILE_SIZE=$(du -h bundle.html | cut -f1)

echo ""
echo "Bundle complete."
echo "Output: bundle.html ($FILE_SIZE)"
echo ""
echo "Share this single file as a Claude artefact, or open it in a browser to preview locally."
