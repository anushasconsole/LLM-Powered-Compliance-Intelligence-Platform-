import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: false,   // if 3000 is taken, use next available (3001, 3002, ...)
    open: true,          // auto-open browser
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
  build: {
    outDir: 'build',
    sourcemap: false,
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          charts:  ['recharts'],
          motion:  ['framer-motion'],
        },
      },
    },
  },
  css: {
    postcss: './postcss.config.cjs',
  },
});
