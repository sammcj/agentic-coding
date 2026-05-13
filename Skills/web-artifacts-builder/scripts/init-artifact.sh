#!/bin/bash

set -e

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
NODE_MINOR=$(node -v | cut -d'v' -f2 | cut -d'.' -f2)

echo "Detected Node.js $(node -v)"

if [ "$NODE_VERSION" -lt 20 ] || { [ "$NODE_VERSION" -eq 20 ] && [ "$NODE_MINOR" -lt 19 ]; }; then
  echo "Error: Node.js 20.19+ or 22.12+ is required for Vite 8 + Tailwind v4."
  exit 1
fi

if [[ "$OSTYPE" == "darwin"* ]]; then
  SED_INPLACE="sed -i ''"
else
  SED_INPLACE="sed -i"
fi

if ! command -v pnpm &> /dev/null; then
  echo "pnpm not found. Installing..."
  npm install -g pnpm
fi

if [ -z "$1" ]; then
  echo "Usage: bash init-artifact.sh <project-name>"
  exit 1
fi

PROJECT_NAME="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPONENTS_TARBALL="$SCRIPT_DIR/shadcn-components.tar.gz"

if [ ! -f "$COMPONENTS_TARBALL" ]; then
  echo "Error: shadcn-components.tar.gz not found at $COMPONENTS_TARBALL"
  exit 1
fi

echo "Creating Vite React + TypeScript project: $PROJECT_NAME"
pnpm create vite@latest "$PROJECT_NAME" --template react-ts

cd "$PROJECT_NAME"

echo "Cleaning Vite template..."
$SED_INPLACE '/<link rel="icon".*vite\.svg/d' index.html
$SED_INPLACE 's/<title>.*<\/title>/<title>'"$PROJECT_NAME"'<\/title>/' index.html
rm -f src/App.css src/App.tsx
rm -rf src/assets

echo "Installing base dependencies..."
pnpm install

echo "Installing Tailwind v4, shadcn runtime, Radix UI and icons..."
pnpm add tailwindcss @tailwindcss/vite tw-animate-css \
  class-variance-authority clsx tailwind-merge lucide-react \
  radix-ui \
  next-themes sonner cmdk vaul \
  embla-carousel-react react-day-picker react-resizable-panels \
  date-fns react-hook-form @hookform/resolvers zod \
  input-otp
pnpm add -D @types/node

echo "Writing vite.config.ts with Tailwind v4 plugin and @ alias..."
cat > vite.config.ts << 'EOF'
import path from "path";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
EOF

echo "Adding path aliases to tsconfig.json..."
node -e "
const fs = require('fs');
const config = JSON.parse(fs.readFileSync('tsconfig.json', 'utf8'));
config.compilerOptions = config.compilerOptions || {};
config.compilerOptions.baseUrl = '.';
config.compilerOptions.paths = { '@/*': ['./src/*'] };
fs.writeFileSync('tsconfig.json', JSON.stringify(config, null, 2));
"

echo "Adding path aliases to tsconfig.app.json..."
node -e "
const fs = require('fs');
const path = 'tsconfig.app.json';
const content = fs.readFileSync(path, 'utf8');
const stripped = content.split('\n').filter(line => !line.trim().startsWith('//')).join('\n');
const config = JSON.parse(stripped.replace(/\/\*[\s\S]*?\*\//g, '').replace(/,(\s*[}\]])/g, '\$1'));
config.compilerOptions = config.compilerOptions || {};
config.compilerOptions.baseUrl = '.';
config.compilerOptions.paths = { '@/*': ['./src/*'] };
fs.writeFileSync(path, JSON.stringify(config, null, 2));
"

echo "Writing components.json..."
cat > components.json << 'EOF'
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/index.css",
    "baseColor": "neutral",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "iconLibrary": "lucide"
}
EOF

echo "Extracting pre-built shadcn components, hooks, lib, and index.css..."
tar -xzf "$COMPONENTS_TARBALL" -C src/

echo "Writing src/main.tsx..."
cat > src/main.tsx << 'EOF'
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
EOF

echo "Writing minimal src/App.tsx placeholder..."
cat > src/App.tsx << 'EOF'
export default function App() {
  return (
    <main className="min-h-svh">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <h1 className="text-2xl font-semibold tracking-tight">
          Replace this page with your artefact.
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Edit <code>src/App.tsx</code> to begin.
        </p>
      </div>
    </main>
  );
}
EOF

echo ""
echo "Setup complete. Stack:"
echo "  - React 19 + TypeScript"
echo "  - Vite 8"
echo "  - Tailwind CSS v4 (CSS-first config in src/index.css)"
echo "  - shadcn/ui (new-york style, 40+ components in src/components/ui)"
echo "  - lucide-react icons"
echo ""
echo "Pre-installed components:"
echo "  accordion, alert, alert-dialog, aspect-ratio, avatar, badge,"
echo "  breadcrumb, button, calendar, card, carousel, checkbox, collapsible,"
echo "  command, context-menu, dialog, drawer, dropdown-menu, form,"
echo "  hover-card, input, input-otp, label, menubar, navigation-menu,"
echo "  pagination, popover, progress, radio-group, resizable, scroll-area,"
echo "  select, separator, sheet, sidebar, skeleton, slider, sonner,"
echo "  switch, table, tabs, textarea, toggle, toggle-group, tooltip"
echo ""
echo "To develop:"
echo "  cd $PROJECT_NAME"
echo "  pnpm dev"
echo ""
echo "Imports use the @/ alias, for example:"
echo "  import { Button } from '@/components/ui/button'"
echo "  import { Card, CardHeader } from '@/components/ui/card'"
echo "  import { cn } from '@/lib/utils'"
