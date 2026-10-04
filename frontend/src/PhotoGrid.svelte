<script lang="ts">
    import { gallery } from './lib/state.svelte'
    import { FLAG_DEFS, flagDef } from './lib/flags'

    const activeDef = $derived(flagDef(gallery.activeFlag))
    const activeFlagStyle = $derived(
        activeDef ? `--active-flag-color: ${activeDef.hex}; --active-flag-glow: ${activeDef.glow}` : '',
    )
</script>

<div class="photo-grid">
    {#each gallery.visible as photo (photo.id)}
        <div
            class="photo-card"
            class:photo-card--selected={gallery.isSelected(photo.id)}
            class:photo-card--select-mode={gallery.selectMode}
        >
            <img src={photo.thumbnail_url} alt={photo.filename} loading="lazy">

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
                <!-- TODO slice 2: wire toggleFlag -->
                <button
                    class="btn-select"
                    class:active={photo.flags.includes(gallery.activeFlag)}
                    style={activeFlagStyle}
                >
                    <span>{photo.flags.includes(gallery.activeFlag) ? '♥' : '♡'}</span>
                </button>
            </div>
        </div>
    {/each}
</div>
