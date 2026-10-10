import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({ plugins: [react()], build: { rollupOptions: { output: { manualChunks(id) { if(id.includes('recharts')||id.includes('d3-'))return 'charts';if(id.includes('@supabase'))return 'auth'; } } } }, server: { proxy: { '/api': 'http://127.0.0.1:8000' } } });


