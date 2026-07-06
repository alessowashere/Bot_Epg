import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 49267,
    allowedHosts: [
      'dataepis.uandina.pe'
    ]
  }
})
