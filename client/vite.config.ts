import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import { tanstackRouter } from '@tanstack/router-plugin/vite'

export default defineConfig({
  base: '/boston-circular-economy/',
  plugins: [
    tanstackRouter({ routesDirectory: './src/pages' }),
    react(),
  ],
})
