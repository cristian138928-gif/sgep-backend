// vite.config.ts
import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// EXPLICACIÓN: Proxy /api -> backend en 8000: un solo origen en dev (sin CORS)
export default defineConfig({
  // EXPLICACIÓN: @tailwindcss/vite compila on-demand las utilities (v4, sin postcss.config)
  plugins: [vue(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
