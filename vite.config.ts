// vite.config.ts — Vite build config for Lumara frontend + Tauri integration
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig(async () => ({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // Tauri expects a fixed port during dev
  server: {
    port: 1420,
    strictPort: true,
    watch: {
      // Watch for Rust source changes too
      ignored: ["**/src-tauri/**"],
    },
  },
  // Ensure sourcemaps in dev for easier debugging
  build: {
    sourcemap: true,
  },
}));
