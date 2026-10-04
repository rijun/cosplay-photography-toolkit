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
        z-index: 100;
        transform: translateX(-50%);
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.6rem 1.1rem;
        border-radius: 32px;
        white-space: nowrap;
        color: var(--linen);
        background: rgba(50, 42, 38, 0.93);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
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
        border: 1px solid rgba(var(--cream-rgb), 0.2);
        border-radius: 20px;
        font-family: inherit;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        text-decoration: none;
        color: var(--linen);
        background: rgba(var(--cream-rgb), 0.12);
        cursor: pointer;
        transition: background 0.2s;
    }

    .btn-selection:active {
        background: rgba(var(--cream-rgb), 0.24);
    }
</style>
