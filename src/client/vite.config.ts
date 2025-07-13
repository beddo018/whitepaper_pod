import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    proxy: {
      '/api': {
        target: `http://localhost:${process.env.FLASK_PORT || 5000}`,
        changeOrigin: true,
      },
      '/static': {
        target: `http://localhost:${process.env.FLASK_PORT || 5000}`,
        changeOrigin: true,
      },
      '/download-audio': {
        target: `http://localhost:${process.env.FLASK_PORT || 5000}`,
        changeOrigin: true,
      },
    }
  },
  plugins: [
    react(),
    mode === 'development' &&
    componentTagger(),
  ].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
