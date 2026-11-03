import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  test: {
    environment: "jsdom",
    include: ["src/tests/**/*.test.js"],
    setupFiles: "./src/tests/setup.js",
  },
})
