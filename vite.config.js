import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
    plugins: [svelte()],
    // CRITICAL: This must match your GitHub repository name exactly for GH Pages deployment.
    base: '/swinburne-easy-calendar/',
});
