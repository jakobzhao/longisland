import { defineConfig } from 'vite';
import { resolve } from 'node:path';

// Serve pipeline outputs (../data/processed) directly from the site root.
// No copy step needed in dev; `vite build` bundles them into dist/.
export default defineConfig({
  // GitHub Pages sub-path; set to '/<repo>/' before deploying.
  base: './',
  publicDir: resolve(__dirname, '../data/processed'),
  server: { port: 5173, open: false },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
});
