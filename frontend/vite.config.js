import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Forward /api requests to the FastAPI backend (avoids CORS in development).
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:5000" } },
});
