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
        width: 100%;
        margin-bottom: 1rem;
        padding: 0.4rem 0.75rem;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        border: 1px solid var(--border);
        border-radius: 32px;
        background: rgba(var(--cream-rgb), 0.75);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        box-shadow: 0 2px 12px rgba(var(--umber-rgb), 0.06);
    }

    .flag-picker::-webkit-scrollbar {
        display: none;
    }

    .flag-picker-label {
        flex-shrink: 0;
        font-size: 0.62rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        white-space: nowrap;
        color: var(--text-muted);
    }

    /* --- Dots --- */
    .flag-picker-dots {
        display: flex;
        flex: 1;
        justify-content: space-evenly;
        gap: 0.1rem;
    }

    .flag-dot {
        display: flex;
        flex-direction: column;
        flex-shrink: 0;
        align-items: center;
        justify-content: center;
        gap: 0.15rem;
        /* 44px minimum touch target */
        min-width: 44px;
        min-height: 44px;
        padding: 0.3rem 0.4rem;
        border: none;
        border-radius: 12px;
        background: none;
        cursor: pointer;
        transition: background 0.2s;
    }

    .flag-dot:active {
        background: rgba(var(--dust-rgb), 0.12);
    }

    .flag-dot--final {
        margin-left: 0.2rem;
        padding-left: 0.5rem;
        border-left: 1.5px solid var(--border);
    }

    .flag-dot-inner {
        display: block;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: var(--dot-color);
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
        opacity: 0.4;
        transition:
            opacity 0.2s,
            transform 0.2s,
            box-shadow 0.2s;
    }

    .flag-dot.active .flag-dot-inner {
        box-shadow:
            0 0 0 3px var(--dot-glow),
            0 2px 8px rgba(0, 0, 0, 0.1);
        opacity: 1;
        transform: scale(1.2);
    }

    /* Labels and hint are desktop-only. */
    .flag-dot-label,
    .flag-picker-hint {
        display: none;
    }

    /* --- Desktop: natural width, labels, hint --- */
    @media (min-width: 768px) {
        .flag-picker {
            width: fit-content;
            padding: 0.65rem 1rem;
            overflow: visible;
        }

        .flag-dot--final {
            margin-left: 0.35rem;
            padding-left: 0.6rem;
        }

        .flag-dot:not(.active):hover .flag-dot-inner {
            opacity: 0.7;
            transform: scale(1.1);
        }

        .flag-dot-label {
            display: block;
            font-size: 0.55rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--text-muted);
            transition: color 0.2s;
        }

        .flag-dot.active .flag-dot-label {
            color: var(--dot-color);
        }

        .flag-picker-hint {
            display: block;
            padding-left: 0.5rem;
            border-left: 1px solid var(--border);
            font-size: 0.65rem;
            font-style: italic;
            white-space: nowrap;
            color: #c0b0a8;
        }
    }
</style>
