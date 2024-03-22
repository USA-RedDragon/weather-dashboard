import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import VueDevTools from 'vite-plugin-vue-devtools';
import mkcert from 'vite-plugin-mkcert';
import { viteStaticCopy } from 'vite-plugin-static-copy';

// https://vitejs.dev/config/
export default defineConfig({
  // eslint-disable-next-line new-cap
  plugins: [
    vue(),
    VueDevTools(),
    mkcert(),
    viteStaticCopy({
      targets: [
        {
          src: 'node_modules/pyodide/*.whl*',
          dest: 'assets/',
        },
        {
          src: 'node_modules/pyodide/pyodide.asm.js',
          dest: 'assets/',
        },
        {
          src: 'node_modules/pyodide/pyodide.asm.wasm',
          dest: 'assets/',
        },
        {
          src: 'node_modules/pyodide/python_stdlib.zip',
          dest: 'assets/',
        },
        {
          src: 'node_modules/pyodide/sqlite3-1.0.0.zip',
          dest: 'assets/',
        },
        {
          src: 'node_modules/pyodide/pyodide-lock.json',
          dest: 'assets/',
        },
      ],
    }),
  ],
  optimizeDeps: { exclude: ['pyodide'] },
  server: {
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
    },
  },
});
