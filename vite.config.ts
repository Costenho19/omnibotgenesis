import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@assets': path.resolve(__dirname, './attached_assets'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5000,
    allowedHosts: true,
    watch: {
      ignored: [
        '**/.cache/**',
        '**/node_modules/**',
        '**/.git/**',
        '**/omnix_web/**',
        '**/omnix_dashboard/**',
        '**/omnix_services/**',
        '**/omnix_core/**',
        '**/docs/**',
        '**/evidence_packages/**',
        '**/backups/**',
        '**/avm_snapshots/**',
        '**/scripts/**',
        '**/tests/**',
        '**/sdk/**',
      ],
    },
  },
  base: '/',
});
