import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Allow Vite dev server to be accessed through Cloudflare Tunnel
    // Fixes: "Blocked request. This host (...) is not allowed."
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      'server-sunglasses-flux-moved.trycloudflare.com',
      /^.+\.trycloudflare\.com$/,
    ],
    host: true,
    port: 5173,
    strictPort: false,
    // HMR over HTTPS tunnels sometimes needs clientPort 443
    hmr: {
      clientPort: 443,
    },
    // Proxy API calls from the Mini App to Django dev server
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
