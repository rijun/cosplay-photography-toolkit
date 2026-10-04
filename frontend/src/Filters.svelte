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
    <span class="label">show</span>
    <button class="chip" class:active={gallery.filterFlags.length === 0} onclick={() => (gallery.filterFlags = [])}
        >all</button
    >
    {#each FLAG_DEFS as f (f.color)}
        <button
            class="chip"
            class:active={gallery.filterFlags.includes(f.color)}
            style:--chip-color={f.hex}
            style:--chip-glow={f.glow}
            onclick={() => toggleFilter(f.color)}
        >
            <span class="dot"></span>
            <span>{f.label}</span>
        </button>
    {/each}
</div>

{#if gallery.hasEdited}
    <div class="filter-bar">
        <span class="label">type</span>
        <button
            class="chip"
            class:active={gallery.editedFilter === 'all'}
            onclick={() => (gallery.editedFilter = 'all')}>all</button
        >
        <button
            class="chip"
            class:active={gallery.editedFilter === 'originals'}
            onclick={() => (gallery.editedFilter = 'originals')}>originals</button
        >
        <button
            class="chip"
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
        padding-bottom: 2px; /* prevent clipping box-shadows */
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
    }

    .filter-bar::-webkit-scrollbar {
        display: none;
    }

    .label {
        flex-shrink: 0;
        margin-right: 0.15rem;
        font-size: 0.62rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        white-space: nowrap;
        color: var(--text-muted);
    }

    /* --- Chips --- */
    .chip {
        display: inline-flex;
        flex-shrink: 0;
        align-items: center;
        gap: 0.35rem;
        height: 32px;
        padding: 0 0.75rem;
        border: 1.5px solid var(--border);
        border-radius: 20px;
        font-family: inherit;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        white-space: nowrap;
        color: var(--text-secondary);
        background: rgba(var(--cream-rgb), 0.7);
        cursor: pointer;
        transition: all 0.2s;
    }

    .chip:active {
        transform: scale(0.95);
    }

    .chip.active {
        border-color: var(--chip-color, var(--rose));
        color: var(--chip-color, var(--rose-deep));
        background: rgba(var(--cream-rgb), 0.95);
        box-shadow: 0 0 0 2px var(--chip-glow, var(--rose-glow));
    }

    /* "all" chip has no dot color vars, use rose as default active state */
    .chip:first-of-type.active {
        border-color: var(--rose-light);
        color: var(--rose-deep);
        box-shadow: none;
    }

    .dot {
        flex-shrink: 0;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--chip-color);
        opacity: 0.5;
        transition: opacity 0.2s;
    }

    .chip.active .dot {
        opacity: 1;
    }
</style>
