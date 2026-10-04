// Must come first, as per Vite backend integration docs (https://vite.dev/guide/backend-integration.html)
import 'vite/modulepreload-polyfill'

import {mount} from 'svelte'
import Poc from './Poc.svelte'
import type {Photo} from "./lib/photo"
import '../../backend/gallery/static/gallery/css/style.css'

// Entry runs on every page that loads the bundle; mount only where the host element exists.
const target = document.getElementById('svelte-root')
const photos_json = document.getElementById('poc-photos')

if (target && photos_json) {
    const photos = JSON.parse(photos_json.textContent!) as Photo[]
    mount(Poc, { target, props: { photos } })
}
