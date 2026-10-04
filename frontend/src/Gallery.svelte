<script lang="ts">
    import PhotoGrid from './PhotoGrid.svelte'
    import Lightbox from './Lightbox.svelte'
    import SelectionBar from './SelectionBar.svelte'
    import DownloadToast from './DownloadToast.svelte'
    import { startDownload, toggleSelectMode } from './lib/actions'
    import FlagPicker from './FlagPicker.svelte'
    import Filters from './Filters.svelte'
    import { gallery } from './lib/state.svelte'
    import { fade } from 'svelte/transition'
</script>

<div class="gallery">
    <FlagPicker />
    <div class="gallery-toolbar">
        <button class="btn-toolbar" class:active={gallery.selectMode} onclick={toggleSelectMode}>
            {gallery.selectMode ? 'Cancel' : 'Select'}
        </button>
        <button class="btn-toolbar" disabled={gallery.zip.active} onclick={() => startDownload()}>
            Download All
        </button>
    </div>
    <Filters />
    <PhotoGrid />
    {#if gallery.lightboxOpen}
        <Lightbox />
    {/if}
    <SelectionBar />
    <DownloadToast />
    <!-- Toast notification -->
    {#if gallery.toast}
        <div class="toast" transition:fade>{gallery.toast}</div>
    {/if}
</div>

<style>
    .gallery-toolbar {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 0.875rem;
    }

    .btn-toolbar {
        display: inline-flex;
        align-items: center;
        height: 44px;
        padding: 0 1.1rem;
        background: rgba(255, 252, 249, 0.85);
        border: 1.5px solid var(--border-strong);
        color: var(--text-secondary);
        font-family: inherit;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        border-radius: 24px;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
    }

    .btn-toolbar:active {
        transform: scale(0.96);
    }

    .btn-toolbar.active {
        background: rgba(212, 165, 154, 0.18);
        border-color: var(--rose);
        color: #8a5a50;
    }

    .toast {
        position: fixed;
        top: calc(1.25rem + var(--safe-top));
        left: 50%;
        transform: translateX(-50%);
        padding: 0.6rem 1.25rem;
        background: rgba(74, 50, 46, 0.93);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        color: #f5ede6;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        z-index: 400;
        white-space: nowrap;
    }
</style>
