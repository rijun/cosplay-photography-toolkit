// Must come first, as per Vite backend integration docs (https://vite.dev/guide/backend-integration.html)
import 'vite/modulepreload-polyfill'

import {mount} from 'svelte'
import Gallery from './Gallery.svelte'
import type {Photo} from "./lib/photo"
import {gallery} from "./lib/state.svelte";

// No mount point means this simply is not a gallery page, which is fine.
const target = document.getElementById('svelte-root')

if (target) {
    const token = target.dataset.token
    const json = document.getElementById('photos')?.textContent

    // A mount point without its data is a template bug, not an absent gallery.
    if (!token || !json) {
        throw new Error('gallery.html must provide data-token and a #photos json_script')
    }

    // Before mount: components read `gallery` during their first render.
    gallery.hydrate(token, JSON.parse(json) as Photo[])
    mount(Gallery, { target })
}
