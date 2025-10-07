import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // If you prefer a dev proxy instead of CORS on the agent service:
    // set VITE_USE_PROXY=1 and VITE_AGENT_BASE_URL to your agent origin
    proxy: process.env.VITE_USE_PROXY === '1'
      ? {
          '/report': {
            target: process.env.VITE_AGENT_BASE_URL || 'http://localhost:5050',
            changeOrigin: true,
            secure: false
          }
        }
      : undefined
  }
})
