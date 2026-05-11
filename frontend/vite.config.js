import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/',
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/users': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/debts': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/expenses': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/incomes': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/credit-cards': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/repayments': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/analytics': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/audit-logs': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/creditors': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/credit-card-issuers': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/debt-history': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/imports': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/records': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
})
