<script lang="ts">
    import { fade } from 'svelte/transition'
    import { startDownload } from './lib/actions'
    import { gallery } from './lib/state.svelte'
</script>

{#if gallery.selected.length > 0}
    <div class="selection-bar" transition:fade>
        <span class="selection-count">{gallery.selected.length} selected</span>
        <div class="selection-actions">
            <button class="btn-selection" disabled={gallery.zip.active} onclick={() => startDownload(gallery.selected)}>
                Download
            </button>
            <button class="btn-selection" onclick={() => (gallery.selected = [])}>Clear</button>
        </div>
    </div>
{/if}

<style>
    .selection-bar {
        position: fixed;
        bottom: calc(1.25rem + var(--safe-bottom));
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.6rem 1.1rem;
        background: rgba(50, 42, 38, 0.93);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 32px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
        z-index: 100;
        color: #f5ede6;
        white-space: nowrap;
    }

    .selection-count {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }

    .selection-actions {
        display: flex;
        gap: 0.4rem;
    }

    .btn-selection {
        display: inline-flex;
        align-items: center;
        height: 32px;
        padding: 0 0.9rem;
        background: rgba(255, 252, 249, 0.12);
        border: 1px solid rgba(255, 252, 249, 0.2);
        color: #f5ede6;
        font-family: inherit;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        border-radius: 20px;
        cursor: pointer;
        transition: background 0.2s;
        text-decoration: none;
    }

    .btn-selection:active {
        background: rgba(255, 252, 249, 0.24);
    }
</style>
