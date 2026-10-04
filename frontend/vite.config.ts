// vite.config.ts
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// EXPLICACIÓN: Proxy /api -> backend en 8000: un solo origen en dev (sin CORS)
export default defineConfig({
  plugins: [vue()],
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
