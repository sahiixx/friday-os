import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Tauri dev server on 1420; strictPort so Tauri's webview points at the right URL.
export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: { port: 1420, strictPort: true },
  envPrefix: ["VITE_", "TAURI_"],
});
