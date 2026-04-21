import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  build: {
    // Output directly into backend/dist so the Go server can serve it
    outDir: '../backend/dist',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    // Proxy all API calls to the Go backend during development
    proxy: {
      '/upload': 'http://localhost:8081',
      '/status': 'http://localhost:8081',
      '/progress': 'http://localhost:8081',
      '/api': 'http://localhost:8081',
      '/ai_report': 'http://localhost:8081',
      '/ai_architecture': 'http://localhost:8081',
      '/dependency_graph': 'http://localhost:8081',
      '/file-content': 'http://localhost:8081',
      '/webhook': 'http://localhost:8081',
    }
  }
})
