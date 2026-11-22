import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import { tanstackRouter } from '@tanstack/router-plugin/vite'

export default defineConfig({
  base: '/boston-circular-economy/',
  plugins: [
    tanstackRouter({ routesDirectory: './src/pages' }),
    react(),
  ],
  server: {
    proxy: {
      // During `npm run dev`, forward API calls to the local FastAPI server.
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
