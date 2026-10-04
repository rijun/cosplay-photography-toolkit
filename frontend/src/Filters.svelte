<script lang="ts">
    import { gallery } from './lib/state.svelte'
    import { FLAG_DEFS } from './lib/flags'

    function toggleFilter(color: number) {
        const index = gallery.filterFlags.indexOf(color)
        if (index === -1) gallery.filterFlags.push(color)
        else gallery.filterFlags.splice(index, 1)
    }
</script>

<div class="filter-bar">
    <span class="filter-bar-label">show</span>
    <button
        class="filter-chip"
        class:active={gallery.filterFlags.length === 0}
        onclick={() => (gallery.filterFlags = [])}>all</button
    >
    {#each FLAG_DEFS as f (f.color)}
        <button
            class="filter-chip"
            class:active={gallery.filterFlags.includes(f.color)}
            style:--chip-color={f.hex}
            style:--chip-glow={f.glow}
            onclick={() => toggleFilter(f.color)}
        >
            <span class="filter-chip-dot"></span>
            <span>{f.label}</span>
        </button>
    {/each}
</div>

{#if gallery.hasEdited}
    <div class="filter-bar">
        <span class="filter-bar-label">type</span>
        <button
            class="filter-chip"
            class:active={gallery.editedFilter === 'all'}
            onclick={() => (gallery.editedFilter = 'all')}>all</button
        >
        <button
            class="filter-chip"
            class:active={gallery.editedFilter === 'originals'}
            onclick={() => (gallery.editedFilter = 'originals')}>originals</button
        >
        <button
            class="filter-chip"
            class:active={gallery.editedFilter === 'edited'}
            onclick={() => (gallery.editedFilter = 'edited')}>edited</button
        >
    </div>
{/if}

<style>
    .filter-bar {
        display: flex;
        align-items: center;
        gap: 0.35rem;
        margin-bottom: 0.875rem;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        padding-bottom: 2px; /* prevent clipping box-shadows */
    }

    .filter-bar::-webkit-scrollbar {
        display: none;
    }

    .filter-bar-label {
        font-size: 0.62rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: var(--text-muted);
        white-space: nowrap;
        flex-shrink: 0;
        margin-right: 0.15rem;
    }

    .filter-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        height: 32px;
        padding: 0 0.75rem;
        background: rgba(255, 252, 249, 0.7);
        border: 1.5px solid var(--border);
        color: var(--text-secondary);
        font-family: inherit;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        border-radius: 20px;
        cursor: pointer;
        transition: all 0.2s;
        white-space: nowrap;
        flex-shrink: 0;
    }

    .filter-chip:active {
        transform: scale(0.95);
    }

    .filter-chip.active {
        background: rgba(255, 252, 249, 0.95);
        border-color: var(--chip-color, var(--rose));
        color: var(--chip-color, #8a5a50);
        box-shadow: 0 0 0 2px var(--chip-glow, var(--rose-glow));
    }

    /* "all" chip has no dot color vars, use rose as default active state */
    .filter-chip:first-of-type.active {
        border-color: var(--rose-light);
        color: #8a5a50;
        box-shadow: none;
    }

    .filter-chip-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--chip-color);
        opacity: 0.5;
        flex-shrink: 0;
        transition: opacity 0.2s;
    }

    .filter-chip.active .filter-chip-dot {
        opacity: 1;
    }
</style>
