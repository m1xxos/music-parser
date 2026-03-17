import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    outDir: '../app/static',
    emptyOutDir: true
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
