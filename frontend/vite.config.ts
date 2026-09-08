import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  test: {
    // Component tests mount into a DOM, so they need jsdom rather than node.
    environment: 'jsdom',
  },
})
