<script lang="ts">
    import { gallery } from './lib/state.svelte'
    import { FLAG_DEFS } from './lib/flags'
</script>

<div class="flag-picker">
    <span class="flag-picker-label">your color</span>
    <div class="flag-picker-dots">
        {#each FLAG_DEFS as f (f.color)}
            <button
                class="flag-dot"
                class:active={gallery.activeFlag === f.color}
                class:flag-dot--final={f.color === 0}
                style:--dot-color={f.hex}
                style:--dot-glow={f.glow}
                title={f.color === 0 ? 'final pick' : `${f.label} - pick your color, each person uses a different one`}
                onclick={() => (gallery.activeFlag = f.color)}
            >
                <span class="flag-dot-inner"></span>
                <span class="flag-dot-label">{f.label}</span>
            </button>
        {/each}
    </div>
    <span class="flag-picker-hint">select a color to mark your favorites</span>
</div>

<style>
    .flag-picker {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        margin-bottom: 1rem;
        padding: 0.4rem 0.75rem;
        background: rgba(255, 252, 249, 0.75);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid var(--border);
        border-radius: 32px;
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        box-shadow: 0 2px 12px rgba(107, 87, 80, 0.06);
    }

    .flag-picker::-webkit-scrollbar {
        display: none;
    }

    .flag-picker-label {
        font-size: 0.62rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: var(--text-muted);
        white-space: nowrap;
        flex-shrink: 0;
    }

    .flag-picker-hint {
        display: none;
    }

    .flag-picker-dots {
        display: flex;
        gap: 0.1rem;
        flex: 1;
        justify-content: space-evenly;
    }

    .flag-dot {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.15rem;
        background: none;
        border: none;
        cursor: pointer;
        /* 44px minimum touch target */
        min-width: 44px;
        min-height: 44px;
        padding: 0.3rem 0.4rem;
        border-radius: 12px;
        justify-content: center;
        transition: background 0.2s;
        flex-shrink: 0;
    }

    .flag-dot:active {
        background: rgba(186, 143, 133, 0.12);
    }

    .flag-dot-inner {
        display: block;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: var(--dot-color);
        opacity: 0.4;
        transition:
            opacity 0.2s,
            transform 0.2s,
            box-shadow 0.2s;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
    }

    .flag-dot.active .flag-dot-inner {
        opacity: 1;
        transform: scale(1.2);
        box-shadow:
            0 0 0 3px var(--dot-glow),
            0 2px 8px rgba(0, 0, 0, 0.1);
    }

    /* Labels hidden on mobile, shown on desktop */
    .flag-dot-label {
        display: none;
    }

    .flag-dot--final {
        margin-left: 0.2rem;
        padding-left: 0.5rem;
        border-left: 1.5px solid var(--border);
    }

    @media (min-width: 768px) {
        /*natural width, labels, hint */
        .flag-picker {
            width: fit-content;
            overflow: visible;
            padding: 0.65rem 1rem;
        }

        .flag-picker-hint {
            display: block;
            font-size: 0.65rem;
            color: #c0b0a8;
            white-space: nowrap;
            padding-left: 0.5rem;
            border-left: 1px solid var(--border);
            font-style: italic;
        }

        .flag-dot-label {
            display: block;
            font-size: 0.55rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-muted);
            transition: color 0.2s;
        }

        .flag-dot.active .flag-dot-label {
            color: var(--dot-color);
        }

        .flag-dot:hover .flag-dot-inner {
            opacity: 0.7;
            transform: scale(1.1);
        }

        .flag-dot--final {
            margin-left: 0.35rem;
            padding-left: 0.6rem;
        }
    }
</style>
