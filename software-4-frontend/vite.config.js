import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    // Docker 컨테이너 안에서 파일 변경 감지
    watch: {
      usePolling: true,
      interval: 300,
    },
  },
})
