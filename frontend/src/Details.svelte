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

    <p class="photo-filename">{photo.filename}</p>

    <div class="lightbox-flags">
        {#each FLAG_DEFS as flag (flag.color)}
            <button
                class="lightbox-flag-btn"
                class:active={photo.flags.includes(flag.color)}
                class:lightbox-flag-btn--final={flag.color === 0}
                style:--flag-color={flag.hex}
                style:--flag-glow={flag.glow}
                onclick={() => toggleFlag(photo, flag.color)}
            >
                <span class="lightbox-flag-dot"></span>
                <span class="lightbox-flag-label">{flag.label}</span>
            </button>
        {/each}
    </div>

    <div class="comments-section">
        <h3>Comments</h3>
        {#if loading}
            <div class="comments-loading">loading...</div>
        {:else}
            <div>
                {#each comments as comment (comment.id)}
                    <div class="comment">
                        <p>{comment.body}</p>
                        {#if comment.author}
                            <span class="comment-author">: {comment.author}</span>
                        {/if}
                    </div>
                {/each}
                <form class="comment-form" onsubmit={submit}>
                    <textarea bind:value={draft} placeholder="Leave a comment..." rows="2"></textarea>
                    <button type="submit" disabled={!draft.trim()}>Send</button>
                </form>
            </div>
        {/if}
    </div>
{/if}

<style>
    .photo-filename {
        font-size: 0.74rem;
        color: rgba(186, 143, 133, 0.65);
        margin-bottom: 1rem;
        word-break: break-all;
        padding-bottom: 0.75rem;
        border-bottom: 1px dashed rgba(186, 143, 133, 0.18);
    }

    .lightbox-flags {
        display: flex;
        flex-direction: column;
        gap: 0.3rem;
        margin-bottom: 1rem;
    }

    .lightbox-flag-btn {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        width: 100%;
        min-height: 44px;
        padding: 0.5rem 0.85rem;
        background: rgba(255, 252, 249, 0.04);
        border: 1.5px solid rgba(186, 143, 133, 0.1);
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.18s ease;
        font-family: inherit;
    }

    .lightbox-flag-btn:active {
        transform: scale(0.97);
    }

    .lightbox-flag-btn.active {
        background: rgba(248, 238, 232, 0.08);
        border-color: var(--flag-color);
        box-shadow: 0 0 0 1.5px var(--flag-glow);
    }

    .lightbox-flag-dot {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: var(--flag-color);
        opacity: 0.4;
        transition:
            opacity 0.2s,
            transform 0.2s;
        flex-shrink: 0;
    }

    .lightbox-flag-btn.active .lightbox-flag-dot {
        opacity: 1;
        transform: scale(1.2);
    }

    .lightbox-flag-label {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: rgba(186, 143, 133, 0.6);
        transition: color 0.2s;
    }

    .lightbox-flag-btn.active .lightbox-flag-label {
        color: var(--flag-color);
    }

    .lightbox-flag-btn--final {
        margin-top: 0.5rem;
        position: relative;
    }

    .lightbox-flag-btn--final::before {
        content: '';
        position: absolute;
        top: -0.35rem;
        left: 0;
        right: 0;
        border-top: 1px dashed rgba(186, 143, 133, 0.18);
    }

    /* Comments */
    .comments-section {
        margin-top: 1.25rem;
    }

    .comments-loading {
        font-size: 0.75rem;
        color: rgba(186, 143, 133, 0.45);
        font-style: italic;
        padding: 0.5rem 0;
    }

    .comments-section h3 {
        font-size: 0.72rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
        color: rgba(186, 143, 133, 0.55);
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    .comment {
        background: rgba(255, 252, 249, 0.05);
        padding: 0.65rem 0.85rem;
        border-radius: 6px;
        margin-bottom: 0.4rem;
        font-size: 0.83rem;
        border-left: 2.5px solid rgba(212, 165, 154, 0.35);
        line-height: 1.55;
        color: rgba(245, 237, 230, 0.82);
    }

    .comment-author {
        display: block;
        font-size: 0.8rem;
        opacity: 0.65;
        margin-top: 0.15rem;
    }

    .comment-form textarea {
        width: 100%;
        background: rgba(255, 252, 249, 0.05);
        border: 1.5px solid rgba(186, 143, 133, 0.18);
        color: #e8ddd8;
        border-radius: 8px;
        padding: 0.65rem;
        resize: vertical;
        font-family: inherit;
        font-size: 0.85rem;
        transition:
            border-color 0.2s,
            box-shadow 0.2s;
        line-height: 1.5;
    }

    .comment-form textarea::placeholder {
        color: rgba(186, 143, 133, 0.35);
    }

    .comment-form textarea:focus {
        outline: none;
        border-color: var(--rose);
        box-shadow: 0 0 0 3px rgba(212, 165, 154, 0.1);
    }

    .comment-form button {
        margin-top: 0.6rem;
        height: 44px;
        padding: 0 1.5rem;
        background: linear-gradient(135deg, var(--rose) 0%, #c49088 100%);
        border: none;
        color: #fff;
        border-radius: 24px;
        cursor: pointer;
        font-family: 'Quicksand', sans-serif;
        font-weight: 700;
        font-size: 0.83rem;
        letter-spacing: 0.05em;
        transition:
            transform 0.2s,
            box-shadow 0.2s;
        box-shadow: 0 2px 8px rgba(196, 144, 136, 0.3);
    }

    .comment-form button:active {
        transform: scale(0.96);
    }

    .comment-form button:disabled {
        opacity: 0.35;
        cursor: default;
        transform: none;
        box-shadow: none;
    }

    @media (min-width: 768px) {
        .photo-filename {
            color: var(--text-muted);
        }

        /* Flag buttons — light theme on desktop */
        .lightbox-flag-btn {
            background: rgba(255, 252, 249, 0.6);
            border-color: rgba(186, 143, 133, 0.15);
        }

        .lightbox-flag-btn:hover {
            background: rgba(248, 238, 232, 0.8);
            border-color: var(--flag-color);
            transform: none;
        }

        .lightbox-flag-btn.active {
            background: rgba(248, 238, 232, 0.95);
            border-color: var(--flag-color);
            box-shadow: 0 0 0 2px var(--flag-glow);
        }

        .lightbox-flag-dot {
            opacity: 0.4;
        }
        .lightbox-flag-btn:hover .lightbox-flag-dot {
            opacity: 0.7;
        }
        .lightbox-flag-label {
            color: #a09890;
        }

        .lightbox-flag-btn--final::before {
            border-top-color: rgba(186, 143, 133, 0.3);
        }

        /* Comments — light theme on desktop */
        .comments-section h3 {
            color: #8a7a75;
        }
        .comments-loading {
            color: #b8a8a0;
        }

        .comment {
            background: rgba(255, 252, 249, 0.8);
            border-left-color: #d4b8b0;
            color: var(--text-primary);
        }

        .comment-form textarea {
            background: #fffcf9;
            border-color: rgba(186, 143, 133, 0.25);
            color: var(--text-primary);
        }

        .comment-form textarea::placeholder {
            color: #b8a8a0;
        }
    }
</style>
