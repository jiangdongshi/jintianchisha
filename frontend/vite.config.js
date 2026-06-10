import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import fs from 'fs';
import path from 'path';

// 启用 HTTPS：让浏览器把当前页面识别为"安全来源"，从而允许使用 Geolocation API
// 证书放在 frontend/ssl/ 目录下（由 openssl 自签生成）
const certPath = path.resolve(__dirname, 'ssl', 'server.crt');
const keyPath = path.resolve(__dirname, 'ssl', 'server.key');
const httpsEnabled = fs.existsSync(certPath) && fs.existsSync(keyPath);

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 4443,
    strictPort: false,  // 端口占用时自动找下一个
    open: false,
    https: httpsEnabled ? {
      cert: fs.readFileSync(certPath),
      key: fs.readFileSync(keyPath),
    } : false,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/docs': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/openapi.json': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 1500,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          axios: ['axios'],
          router: ['react-router-dom'],
          store: ['zustand'],
        },
      },
    },
  },
});
