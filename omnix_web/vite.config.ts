import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: true,
    proxy: {
      '/api/live-metrics': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/news': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/contact': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/public/sandbox': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        proxyTimeout: 120000,
        timeout: 120000,
      },
      '/api/public/verify': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/governance': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/api/credit': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  }
})
