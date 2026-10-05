<script lang="ts">
    import { gallery } from './lib/state.svelte'
    import { toggleFlag, toggleSelect } from './lib/actions'
    import { FLAG_DEFS, flagDef } from './lib/flags'

    const activeDef = $derived(flagDef(gallery.activeFlag))
    const activeFlagStyle = $derived(
        activeDef ? `--active-flag-color: ${activeDef.hex}; --active-flag-glow: ${activeDef.glow}` : '',
    )
</script>

<div class="photo-grid">
    {#each gallery.visible as photo, i (photo.id)}
        <div class="card" class:selected={gallery.isSelected(photo.id)} class:select-mode={gallery.selectMode}>
            <button class="open" onclick={() => (gallery.selectMode ? toggleSelect(photo.id) : gallery.openPhoto(i))}>
                <img
                    src={photo.thumbnail_url}
                    alt={photo.filename}
                    loading="lazy"
                    onload={(e) => gallery.learnRatio(photo.id, e)}
                />
                <!-- Iterate the defs, not photo.flags, so dot order is stable. -->
                {@const marks = FLAG_DEFS.filter((f) => photo.flags.includes(f.color))}
                {#if marks.length > 0}
                    <span class="flags">
                        {#each marks as flag (flag.color)}
                            <span class="flag-dot" style="--dot-color: {flag.hex}"></span>
                        {/each}
                    </span>
                {/if}
            </button>

            {#if gallery.selectMode}
                <div class="select-overlay" style="pointer-events: none">
                    {#if gallery.isSelected(photo.id)}
                        <span class="checkmark">&#10003;</span>
                    {/if}
                </div>
            {/if}

            <div class="actions">
                <button
                    class="heart-btn"
                    class:active={photo.flags.includes(gallery.activeFlag)}
                    style={activeFlagStyle}
                    onclick={() => toggleFlag(photo)}
                >
                    <span>{photo.flags.includes(gallery.activeFlag) ? '♥' : '♡'}</span>
                </button>
            </div>
        </div>
    {/each}
</div>

<style>
    .photo-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.2rem;
    }

    /* --- Card --- */
    .card {
        position: relative;
        padding: 0.2rem 0.2rem;
        overflow: hidden;
        border-radius: 4px;
        background: var(--cream);
        box-shadow: var(--shadow-soft);
        transition: box-shadow 0.25s ease;
    }

    .card.select-mode {
        cursor: pointer;
    }

    .card.selected {
        box-shadow:
            0 0 0 2.5px var(--rose),
            0 4px 16px rgba(var(--rose-soft-rgb), 0.3);
    }

    /* A button so the photo is reachable by keyboard; styled away to nothing. */
    .open {
        position: relative;
        display: block;
        width: 100%;
        padding: 0;
        border: none;
        background: none;
    }

    .card img {
        display: block;
        width: 100%;
        aspect-ratio: 1 / 1;
        border-radius: 2px;
        object-fit: cover;
        filter: saturate(0.95) contrast(0.98);
        cursor: pointer;
        transition: filter 0.25s;
    }

    .card.selected img {
        opacity: 0.82;
    }

    /* --- Marks: dots on a dark plate, so they read over any photo --- */
    .flags {
        position: absolute;
        top: 6px;
        left: 6px;
        z-index: 5;
        display: flex;
        gap: 5px;
        padding: 4px 6px;
        border-radius: 10px;
        background: rgba(25, 19, 16, 0.6);
    }

    .flag-dot {
        width: 11px;
        height: 11px;
        border-radius: 50%;
        background: var(--dot-color);
    }

    /* --- Select mode checkmark --- */
    .select-overlay {
        position: absolute;
        inset: 0.3rem;
        z-index: 6;
        display: flex;
        align-items: flex-start;
        justify-content: flex-end;
        padding: 0.3rem;
        border-radius: 2px;
    }

    .checkmark {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        font-size: 0.85rem;
        font-weight: 700;
        color: #fff;
        background: var(--rose);
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.18);
    }

    /* --- Flag toggle --- */
    .actions {
        position: absolute;
        right: 0.3rem;
        bottom: 0.3rem;
        left: 0.3rem;
        display: flex;
        justify-content: flex-end;
        padding: 1.25rem 0.3rem 0.2rem;
        border-radius: 0 0 2px 2px;
    }

    .heart-btn {
        min-width: 44px;
        min-height: 36px;
        padding: 0.3rem 0.65rem;
        border: 1.5px solid rgba(var(--dust-rgb), 0.3);
        border-radius: 20px;
        font-family: inherit;
        font-size: 1rem;
        color: #9a8580;
        background: rgba(var(--cream-rgb), 0.88);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        cursor: pointer;
        transition:
            color 0.2s,
            border-color 0.2s,
            background 0.2s;
    }

    .heart-btn:active {
        transform: scale(0.93);
    }

    .heart-btn.active {
        border-color: var(--active-flag-color, var(--rose-light));
        color: var(--active-flag-color, #c47a70);
        background: rgba(248, 232, 228, 0.95);
    }

    /* --- Tablet: wider grid --- */
    @media (min-width: 540px) {
        .photo-grid {
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 0.75rem;
        }
    }

    /* --- Desktop: polaroid hover --- */
    @media (min-width: 768px) {
        .card {
            padding: 0.5rem 0.5rem 0.4rem;
            transition:
                transform 0.3s ease,
                box-shadow 0.3s ease;
        }

        .card:hover {
            box-shadow: var(--shadow-lift);
            transform: translateY(-4px) rotate(0.4deg);
        }

        .card:hover img {
            filter: saturate(1) contrast(1);
        }
    }
</style>
