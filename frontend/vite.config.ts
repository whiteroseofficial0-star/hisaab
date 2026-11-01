/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // host: true listens on IPv4 and IPv6, so both http://localhost:5173 and http://127.0.0.1:5173
  // work (Windows resolves localhost to ::1 first). The API proxy targets 127.0.0.1 explicitly
  // because the backend binds IPv4 only.
  server: { host: true, port: 5173, strictPort: true, proxy: { '/api': 'http://127.0.0.1:8000' } },
  test: { environment: 'jsdom', setupFiles: ['./src/setupTests.ts'], globals: true, exclude: ['e2e/**', 'node_modules/**'] },
})
