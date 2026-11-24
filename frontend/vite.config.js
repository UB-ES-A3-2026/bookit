import vue from '@vitejs/plugin-vue'
import { loadEnv } from 'vite'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd())

  // Render defineix RENDER=true quan fa el build. Allà VITE_API_URL és
  // obligatòria: sense, el frontend publicat buscaria l'API a localhost.
  if (command === 'build' && process.env.RENDER && !env.VITE_API_URL) {
    throw new Error(
      "Falta VITE_API_URL: definiu-la al servei del frontend a Render amb l'adreça del backend (sense /api).",
    )
  }

  return {
    plugins: [vue()],
    test: {
      environment: 'jsdom',
      include: ['src/tests/**/*.test.js'],
      setupFiles: './src/tests/setup.js',
    },
  }
})
