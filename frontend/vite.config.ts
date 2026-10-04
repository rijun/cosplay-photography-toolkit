import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig } from 'vite'

// Django renders the HTML; there is no index.html entry.
// See https://vite.dev/guide/backend-integration
export default defineConfig(({ mode }) => ({
    plugins: [svelte()],
    // Must match STATIC_URL + the django-vite static_url_prefix.
    base: '/static/vite/',
    build: {
        outDir: 'dist',
        // String form, not `true`: `true` writes dist/.vite/manifest.json, but django-vite
        // looks for the manifest at the prefix root.
        manifest: 'manifest.json',
        rolldownOptions: {
            input: {
                gallery: 'src/gallery.ts',
            },
            // Watch builds keep stable filenames for development to prevent asset caching.
            output:
                mode === 'development'
                    ? {
                          entryFileNames: 'assets/[name].js',
                          chunkFileNames: 'assets/[name].js',
                          assetFileNames: 'assets/[name].[ext]',
                      }
                    : {},
        },
    },
}))
