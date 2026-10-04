<script lang="ts">
    import { fade } from 'svelte/transition'
    import { cancelDownload } from './lib/actions'
    import { gallery } from './lib/state.svelte'

    // Zipping is done; the server is still uploading, which reports no progress.
    const finalizing = $derived(gallery.zip.total > 0 && gallery.zip.done >= gallery.zip.total)
    const percent = $derived(gallery.zip.total ? (gallery.zip.done / gallery.zip.total) * 100 : 0)
</script>

{#if gallery.zip.active}
    <div class="download-toast" class:download-toast--above-selection={gallery.selected.length > 0} transition:fade>
        {#if finalizing}
            <div class="download-toast-header">
                <span class="download-toast-spinner"></span>
                <span>Finalizing download...</span>
                <button class="download-toast-cancel" onclick={cancelDownload}>&times;</button>
            </div>
        {:else}
            <div>
                <div class="download-toast-header">
                    <span>Preparing: {gallery.zip.done} / {gallery.zip.total} photos</span>
                    <button class="download-toast-cancel" onclick={cancelDownload}>&times;</button>
                </div>
                <div class="download-toast-bar">
                    <div class="download-toast-fill" style:width="{percent}%"></div>
                </div>
            </div>
        {/if}
    </div>
{/if}

<style>
    .download-toast {
        position: fixed;
        bottom: calc(1.25rem + var(--safe-bottom, 0px));
        left: 50%;
        z-index: 400;
        transform: translateX(-50%);
        min-width: 220px;
        padding: 0.75rem 1.25rem;
        border-radius: 16px;
        font-size: 0.8rem;
        font-weight: 600;
        text-align: center;
        color: var(--linen);
        background: rgba(var(--cocoa-rgb), 0.95);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }

    .download-toast--above-selection {
        bottom: calc(4.5rem + var(--safe-bottom, 0px));
    }

    .download-toast-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
    }

    .download-toast-spinner {
        display: inline-block;
        flex-shrink: 0;
        width: 14px;
        height: 14px;
        border: 2px solid rgba(255, 255, 255, 0.25);
        border-top-color: var(--linen);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }

    .download-toast-cancel {
        padding: 0;
        border: none;
        font-size: 1.1rem;
        line-height: 1;
        color: var(--linen);
        background: none;
        opacity: 0.6;
        cursor: pointer;
    }

    .download-toast-cancel:hover {
        opacity: 1;
    }

    .download-toast-bar {
        height: 4px;
        margin-top: 0.5rem;
        overflow: hidden;
        border-radius: 2px;
        background: rgba(255, 255, 255, 0.15);
    }

    .download-toast-fill {
        height: 100%;
        border-radius: 2px;
        background: var(--rose);
        transition: width 0.3s ease;
    }
</style>
