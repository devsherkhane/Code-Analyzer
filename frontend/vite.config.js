import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import fs from 'fs'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'history-proxy-middleware',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          if ((req.url.startsWith('/dependency_graph') || req.url.startsWith('/ai_architecture')) && req.url.includes('id=')) {
            const urlObj = new URL(req.url, 'http://localhost');
            const id = urlObj.searchParams.get('id');
            if (id) {
              const isGraph = req.url.startsWith('/dependency_graph');
              const filename = isGraph ? `dependency_graph_${id}.json` : `ai_architecture_${id}.json`;
              const filePath = path.resolve(__dirname, '../backend/json_reports', filename);
              
              if (fs.existsSync(filePath)) {
                res.setHeader('Content-Type', 'application/json');
                res.end(fs.readFileSync(filePath));
                return;
              } else {
                res.statusCode = 404;
                res.end(JSON.stringify({ error: "Historical data not found for this report." }));
                return;
              }
            }
          }
          next();
        });
      }
    }
  ],
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
