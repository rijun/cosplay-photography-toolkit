<script lang="ts">
    import * as api from './lib/api'
    import { toggleFlag } from './lib/actions'
    import { FLAG_DEFS } from './lib/flags'
    import { gallery } from './lib/state.svelte'

    let comments = $state<api.Comment[]>([])
    let loading = $state(false)
    let draft = $state('')

    // Refetch whenever the open photo changes. The cleanup discards a response
    // that arrives after the reader has already swiped on — Swiper makes that
    // easy to trigger, and a late reply would otherwise overwrite the new list.
    $effect(() => {
        const photo = gallery.lightboxPhoto
        if (!photo) return

        let stale = false
        loading = true
        api.comments(gallery.token, photo.id)
            .then((fetched) => {
                if (!stale) comments = fetched
            })
            .catch(() => {
                if (!stale) comments = []
            })
            .finally(() => {
                if (!stale) loading = false
            })

        return () => {
            stale = true
        }
    })

    async function submit(event: SubmitEvent) {
        event.preventDefault()
        const photo = gallery.lightboxPhoto
        const body = draft.trim()
        if (!photo || !body) return

        try {
            comments.push(await api.addComment(gallery.token, photo.id, body))
            draft = ''
        } catch {
            gallery.showToast('Could not save comment, please try again')
        }
    }
</script>

{#if gallery.lightboxPhoto}
    {@const photo = gallery.lightboxPhoto}

    <p class="filename">{photo.filename}</p>

    <div class="flags">
        {#each FLAG_DEFS as flag (flag.color)}
            <button
                class="flag-btn"
                class:active={photo.flags.includes(flag.color)}
                class:final={flag.color === 0}
                style:--flag-color={flag.hex}
                style:--flag-glow={flag.glow}
                onclick={() => toggleFlag(photo, flag.color)}
            >
                <span class="flag-dot"></span>
                <span class="flag-label">{flag.label}</span>
            </button>
        {/each}
    </div>

    <div class="comments-section">
        <h3>Comments</h3>
        <div class="comment-list">
            {#if loading}
                <div class="comment-loading">loading...</div>
            {:else}
                {#each comments as comment (comment.id)}
                    <div class="comment">
                        <p>{comment.body}</p>
                        {#if comment.author}
                            <span class="comment-author">: {comment.author}</span>
                        {/if}
                    </div>
                {/each}
            {/if}
        </div>
        <form class="comment-form" onsubmit={submit}>
            <textarea bind:value={draft} placeholder="Leave a comment..." rows="2"></textarea>
            <button type="submit" disabled={!draft.trim()}>Send</button>
        </form>
    </div>
{/if}

<style>
    /* --- Filename --- */
    .filename {
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px dashed rgba(var(--dust-rgb), 0.18);
        font-size: 0.74rem;
        word-break: break-all;
        color: rgba(var(--dust-rgb), 0.65);
    }

    /* --- Flags --- */
    .flags {
        display: flex;
        flex-direction: column;
        gap: 0.3rem;
        margin-bottom: 1rem;
    }

    .flag-btn {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        width: 100%;
        min-height: 44px;
        padding: 0.5rem 0.85rem;
        border: 1.5px solid rgba(var(--dust-rgb), 0.1);
        border-radius: 10px;
        font-family: inherit;
        background: rgba(var(--cream-rgb), 0.04);
        cursor: pointer;
        transition: all 0.18s ease;
    }

    .flag-btn:active {
        transform: scale(0.97);
    }

    .flag-btn.active {
        border-color: var(--flag-color);
        background: rgba(var(--blush-rgb), 0.08);
        box-shadow: 0 0 0 1.5px var(--flag-glow);
    }

    .flag-btn.final {
        position: relative;
        margin-top: 0.5rem;
    }

    .flag-btn.final::before {
        content: '';
        position: absolute;
        top: -0.35rem;
        right: 0;
        left: 0;
        border-top: 1px dashed rgba(var(--dust-rgb), 0.18);
    }

    .flag-dot {
        flex-shrink: 0;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: var(--flag-color);
        opacity: 0.4;
        transition:
            opacity 0.2s,
            transform 0.2s;
    }

    .flag-btn.active .flag-dot {
        opacity: 1;
        transform: scale(1.2);
    }

    .flag-label {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: rgba(var(--dust-rgb), 0.6);
        transition: color 0.2s;
    }

    .flag-btn.active .flag-label {
        color: var(--flag-color);
    }

    /* --- Comments --- */
    .comments-section {
        margin-top: 1.25rem;
    }

    .comments-section h3 {
        margin-bottom: 0.75rem;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: rgba(var(--dust-rgb), 0.55);
    }

    .comment-loading {
        padding: 0.5rem 0;
        font-size: 0.75rem;
        font-style: italic;
        color: rgba(var(--dust-rgb), 0.45);
    }

    .comment {
        margin-bottom: 0.4rem;
        padding: 0.65rem 0.85rem;
        border-left: 2.5px solid rgba(var(--rose-soft-rgb), 0.35);
        border-radius: 6px;
        font-size: 0.83rem;
        line-height: 1.55;
        color: rgba(var(--linen-rgb), 0.82);
        background: rgba(var(--cream-rgb), 0.05);
    }

    .comment-author {
        display: block;
        margin-top: 0.15rem;
        font-size: 0.8rem;
        opacity: 0.65;
    }

    .comment-form textarea {
        width: 100%;
        padding: 0.65rem;
        border: 1.5px solid rgba(var(--dust-rgb), 0.18);
        border-radius: 8px;
        font-family: inherit;
        font-size: 0.85rem;
        line-height: 1.5;
        color: var(--text-on-dark);
        background: rgba(var(--cream-rgb), 0.05);
        resize: vertical;
        transition:
            border-color 0.2s,
            box-shadow 0.2s;
    }

    .comment-form textarea::placeholder {
        color: rgba(var(--dust-rgb), 0.35);
    }

    .comment-form textarea:focus {
        border-color: var(--rose);
        box-shadow: 0 0 0 3px rgba(var(--rose-soft-rgb), 0.1);
        outline: none;
    }

    .comment-form button {
        height: 44px;
        margin-top: 0.6rem;
        padding: 0 1.5rem;
        border: none;
        border-radius: 24px;
        font-family: inherit;
        font-size: 0.83rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        color: #fff;
        background: linear-gradient(135deg, var(--rose) 0%, #c49088 100%);
        box-shadow: 0 2px 8px rgba(196, 144, 136, 0.3);
        cursor: pointer;
        transition:
            transform 0.2s,
            box-shadow 0.2s;
    }

    .comment-form button:active {
        transform: scale(0.96);
    }

    .comment-form button:disabled {
        box-shadow: none;
        opacity: 0.35;
        cursor: default;
        transform: none;
    }

    /* --- Desktop: light theme --- */
    @media (min-width: 768px) {
        .filename {
            color: var(--text-muted);
        }

        .flag-btn {
            border-color: rgba(var(--dust-rgb), 0.15);
            background: rgba(var(--cream-rgb), 0.6);
        }

        .flag-btn:hover {
            border-color: var(--flag-color);
            background: rgba(var(--blush-rgb), 0.8);
            transform: none;
        }

        .flag-btn.active {
            background: rgba(var(--blush-rgb), 0.95);
            box-shadow: 0 0 0 2px var(--flag-glow);
        }

        .flag-btn.final::before {
            border-top-color: rgba(var(--dust-rgb), 0.3);
        }

        .flag-btn:not(.active):hover .flag-dot {
            opacity: 0.7;
        }

        .flag-label {
            color: #a09890;
        }

        /* Fills the sidebar; the list scrolls so the panel never resizes. */
        .comments-section {
            display: flex;
            flex: 1;
            flex-direction: column;
            min-height: 0;
        }

        .comment-list {
            flex: 1;
            min-height: 0;
            overflow-y: auto;
        }

        .comments-section h3 {
            color: var(--text-secondary);
        }

        .comment-loading {
            color: #b8a8a0;
        }

        .comment {
            border-left-color: #d4b8b0;
            color: var(--text-primary);
            background: rgba(var(--cream-rgb), 0.8);
        }

        .comment-form textarea {
            border-color: rgba(var(--dust-rgb), 0.25);
            color: var(--text-primary);
            background: var(--cream);
        }

        .comment-form textarea::placeholder {
            color: #b8a8a0;
        }
    }
</style>
