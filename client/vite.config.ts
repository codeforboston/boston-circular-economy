import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import { TanStackRouterVite } from '@tanstack/router-plugin/vite'

// https://vite.dev/config/
export default defineConfig({
  base: '/boston-circular-economy/',
  plugins: [
    TanStackRouterVite({ routesDirectory: './src/pages' }),
    react(),
  ],
})
