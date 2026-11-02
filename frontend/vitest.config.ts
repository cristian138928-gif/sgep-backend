// frontend/vitest.config.ts
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

// EXPLICACIÓN: configuración aparte de vite.config.ts para no mezclar
// proxy/build de dev con el entorno de tests (happy-dom = DOM ligero).
export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'happy-dom',
    include: ['tests/**/*.spec.ts'],
  },
})
