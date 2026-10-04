<script lang="ts">
    import { gallery } from './lib/state.svelte'
    import { toggleFlag } from './lib/actions'
    import { FLAG_DEFS, flagDef } from './lib/flags'

    const activeDef = $derived(flagDef(gallery.activeFlag))
    const activeFlagStyle = $derived(
        activeDef ? `--active-flag-color: ${activeDef.hex}; --active-flag-glow: ${activeDef.glow}` : '',
    )
</script>

<div class="photo-grid">
    {#each gallery.visible as photo, i (photo.id)}
        <div
            class="photo-card"
            class:photo-card--selected={gallery.isSelected(photo.id)}
            class:photo-card--select-mode={gallery.selectMode}
        >
            <button class="photo-open" onclick={() => gallery.openPhoto(i)}>
                <img src={photo.thumbnail_url} alt={photo.filename} loading="lazy" />
            </button>

            {#if gallery.selectMode}
                <div class="card-select-overlay" style="pointer-events: none">
                    {#if gallery.isSelected(photo.id)}
                        <span class="card-checkmark">&#10003;</span>
                    {/if}
                </div>
            {/if}

            <div class="card-flags">
                <!-- Iterate the defs, not photo.flags, so dot order is stable. -->
                {#each FLAG_DEFS.filter((f) => photo.flags.includes(f.color)) as flag (flag.color)}
                    <span class="card-flag-dot" style="--dot-color: {flag.hex}"></span>
                {/each}
            </div>

            <div class="photo-actions">
                <button
                    class="btn-select"
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
        grid-template-columns: repeat(2, 1fr);
        gap: 0.5rem;
    }

    .photo-card {
        position: relative;
        border-radius: 4px;
        overflow: hidden;
        background: #fffcf9;
        box-shadow: var(--shadow-soft);
        transition: box-shadow 0.25s ease;
        padding: 0.3rem 0.3rem 0.2rem;
    }

    .photo-card--select-mode {
        cursor: pointer;
    }

    .photo-card--selected {
        box-shadow:
            0 0 0 2.5px var(--rose),
            0 4px 16px rgba(212, 165, 154, 0.3);
    }

    .photo-card--selected img {
        opacity: 0.82;
    }

    /* A button so the photo is reachable by keyboard; styled away to nothing. */
    .photo-open {
        display: block;
        width: 100%;
        padding: 0;
        border: none;
        background: none;
    }

    .photo-card img {
        width: 100%;
        aspect-ratio: 1 / 1;
        object-fit: cover;
        cursor: pointer;
        display: block;
        border-radius: 2px;
        filter: saturate(0.95) contrast(0.98);
        transition: filter 0.25s;
    }

    .card-flags {
        position: absolute;
        top: 0.5rem;
        left: 0.5rem;
        display: flex;
        gap: 3px;
        z-index: 5;
    }

    .card-flag-dot {
        display: block;
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: var(--dot-color);
        box-shadow:
            0 1px 3px rgba(0, 0, 0, 0.15),
            0 0 0 1.5px rgba(255, 255, 255, 0.6);
    }

    /* Select mode checkmark */
    .card-select-overlay {
        position: absolute;
        inset: 0.3rem;
        border-radius: 2px;
        display: flex;
        align-items: flex-start;
        justify-content: flex-end;
        padding: 0.3rem;
        z-index: 6;
    }

    .card-checkmark {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: var(--rose);
        color: #fff;
        font-size: 0.85rem;
        font-weight: 700;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.18);
    }

    /* Card flag-toggle button */
    .photo-actions {
        position: absolute;
        bottom: 0.3rem;
        right: 0.3rem;
        left: 0.3rem;
        padding: 1.25rem 0.3rem 0.2rem;
        display: flex;
        justify-content: flex-end;
        background: linear-gradient(to top, rgba(255, 252, 249, 0.9), transparent);
        border-radius: 0 0 2px 2px;
    }

    .btn-select {
        background: rgba(255, 252, 249, 0.88);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        border: 1.5px solid rgba(186, 143, 133, 0.3);
        color: #9a8580;
        font-size: 1rem;
        min-width: 44px;
        min-height: 36px;
        padding: 0.3rem 0.65rem;
        border-radius: 20px;
        cursor: pointer;
        transition:
            color 0.2s,
            border-color 0.2s,
            background 0.2s;
        font-family: inherit;
    }

    .btn-select:active {
        transform: scale(0.93);
    }

    .btn-select.active {
        color: var(--active-flag-color, #c47a70);
        border-color: var(--active-flag-color, var(--rose-light));
        background: rgba(248, 232, 228, 0.95);
    }

    /* TABLET — wider grid */
    @media (min-width: 540px) {
        .photo-grid {
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 0.75rem;
        }
    }

    /* DESKTOP — full experience */
    @media (min-width: 768px) {
        /* Cards — polaroid hover */
        .photo-card {
            padding: 0.5rem 0.5rem 0.4rem;
            transition:
                transform 0.3s ease,
                box-shadow 0.3s ease;
        }

        .photo-card:hover {
            transform: translateY(-4px) rotate(0.4deg);
            box-shadow: var(--shadow-lift);
        }

        .photo-card:hover img {
            filter: saturate(1) contrast(1);
        }
    }
</style>
