// Must come first, as per Vite backend integration docs (https://vite.dev/guide/backend-integration.html)
import 'vite/modulepreload-polyfill'

import { mount } from 'svelte'
import './app.css'
import App from './App.svelte'

// Entry runs on every page that loads the bundle; mount only where the host element exists.
const target = document.getElementById('svelte-root')

if (target) {
  mount(App, { target })
}
