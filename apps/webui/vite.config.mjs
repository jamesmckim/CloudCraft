import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    host: true,
    allowedHosts: [
        'app.127.0.0.1.nip.io',
        '.nip.io'
    ],
  },
});