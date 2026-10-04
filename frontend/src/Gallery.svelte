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
    <div class="toolbar">
        <button class="toolbar-btn" class:active={gallery.selectMode} onclick={toggleSelectMode}>
            {gallery.selectMode ? 'Cancel' : 'Select'}
        </button>
        <button class="toolbar-btn" disabled={gallery.zip.active} onclick={() => startDownload()}>
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
    /* --- Toolbar --- */
    .toolbar {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 0.875rem;
    }

    .toolbar-btn {
        display: inline-flex;
        align-items: center;
        height: 44px;
        padding: 0 1.1rem;
        border: 1.5px solid var(--border-strong);
        border-radius: 24px;
        font-family: inherit;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        text-decoration: none;
        color: var(--text-secondary);
        background: rgba(var(--cream-rgb), 0.85);
        cursor: pointer;
        transition: all 0.2s;
    }

    .toolbar-btn:active {
        transform: scale(0.96);
    }

    .toolbar-btn.active {
        border-color: var(--rose);
        color: var(--rose-deep);
        background: rgba(var(--rose-soft-rgb), 0.18);
    }

    /* --- Toast --- */
    .toast {
        position: fixed;
        top: calc(1.25rem + var(--safe-top));
        left: 50%;
        z-index: 400;
        transform: translateX(-50%);
        padding: 0.6rem 1.25rem;
        border-radius: 24px;
        font-size: 0.8rem;
        font-weight: 600;
        white-space: nowrap;
        color: var(--linen);
        background: rgba(var(--cocoa-rgb), 0.93);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
</style>
