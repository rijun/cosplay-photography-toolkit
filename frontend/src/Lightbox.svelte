<script lang="ts">
    import { untrack } from 'svelte'
    import Swiper from 'swiper'
    import { Zoom } from 'swiper/modules'
    import 'swiper/css'
    import 'swiper/css/zoom'
    import Details from './Details.svelte'
    import { gallery } from './lib/state.svelte'

    // Downward distance that commits to closing.
    const DISMISS_AT = 40

    // Pulling back this far from the furthest point reads as "no", like iOS Photos.
    const PULL_BACK = 20

    let showDetails = $state(false)
    let swiperEl = $state<HTMLElement | undefined>()
    let backdropEl = $state<HTMLElement | undefined>()
    let swiper: Swiper | undefined

    // Plain variables, not $state: these drive styles imperatively, per frame.
    const pointers = new Set<number>()
    let startX = 0
    let startY = 0
    let maxDy = 0
    let dragSpan = 0
    let tracking = false
    let dragging = false

    $effect(() => {
        if (!swiperEl) return
        swiper = new Swiper(swiperEl, {
            modules: [Zoom],
            // untrack: reading lightboxIndex here would rebuild Swiper on every swipe.
            initialSlide: untrack(() => gallery.lightboxIndex) ?? 0,
            // Loads the active slide plus 2 either side, not all of them.
            lazyPreloadPrevNext: 2,
            zoom: {
                limitToOriginalSize: true, // never zoom past the preview's real resolution
                toggle: true, // double-tap to zoom
            },
            on: {
                // Keeps the filename, flags and comments on the photo being viewed.
                slideChange: (instance) => (gallery.lightboxIndex = instance.activeIndex),
            },
        })
        // Stops the grid scrolling behind the lightbox.
        document.body.style.overflow = 'hidden'
        return () => {
            swiper?.destroy()
            swiper = undefined
            document.body.style.overflow = ''
        }
    })

    function onPointerDown(event: PointerEvent) {
        pointers.add(event.pointerId)
        // A second finger means a pinch. Abandon any drag already in progress.
        if (pointers.size > 1) return reset()
        // While zoomed, vertical belongs to panning.
        if (swiper && swiper.zoom.scale !== 1) return
        startX = event.clientX
        startY = event.clientY
        maxDy = 0
        // Scaling runs from here to the bottom of the screen, so it never clamps early.
        dragSpan = Math.max(window.innerHeight - event.clientY, 1)
        tracking = true
        dragging = false
    }

    function onPointerMove(event: PointerEvent) {
        if (!tracking || !swiperEl || !backdropEl) return
        const dy = event.clientY - startY
        const dx = event.clientX - startX

        // Decide the axis once, then stay with it so Swiper keeps horizontal.
        if (!dragging) {
            if (Math.abs(dx) + Math.abs(dy) < 10) return
            if (Math.abs(dy) <= Math.abs(dx)) return reset()
            dragging = true
            swiperEl.style.transition = 'none'
        }
        if (dy < 0) return
        if (dy > maxDy) maxDy = dy

        const progress = Math.min(dy / dragSpan, 1)
        swiperEl.style.transform = `translateY(${dy}px) scale(${1 - progress * 0.2})`
        backdropEl.style.opacity = `${1 - progress * 0.8}`
    }

    function onPointerUp(event: PointerEvent) {
        pointers.delete(event.pointerId)
        // Still pinching: wait for the last finger before deciding anything.
        if (pointers.size > 0) return
        const dy = event.clientY - startY
        // Dragging back up from the furthest point cancels, however far down you are.
        const pulledBack = dy < maxDy - PULL_BACK
        if (dragging && !pulledBack && dy > DISMISS_AT) {
            tracking = false
            dragging = false
            gallery.closeLightbox(true)
            return
        }
        reset()
    }

    function onPointerCancel(event: PointerEvent) {
        pointers.delete(event.pointerId)
        reset()
    }

    function reset() {
        tracking = false
        dragging = false
        if (!swiperEl || !backdropEl) return
        swiperEl.style.transition = 'transform 0.25s ease-out'
        swiperEl.style.transform = ''
        backdropEl.style.opacity = ''
    }

    function onKeydown(event: KeyboardEvent) {
        if (event.key === 'Escape') gallery.closeLightbox()
        if (event.key === 'ArrowLeft') swiper?.slidePrev()
        if (event.key === 'ArrowRight') swiper?.slideNext()
    }
</script>

<svelte:window onkeydown={onKeydown} />

<div
    class="lightbox"
    role="dialog"
    aria-modal="true"
    aria-label="Photo viewer"
    tabindex="-1"
    onpointerdown={onPointerDown}
    onpointermove={onPointerMove}
    onpointerup={onPointerUp}
    onpointercancel={onPointerCancel}
>
    <!-- Carries the background so the dismiss gesture can fade opacity, which is
         compositor-only, rather than repainting .lightbox's background-color. -->
    <div class="lightbox-fade" bind:this={backdropEl}></div>

    <div class="lightbox-content">
        <button class="lightbox-close" onclick={() => gallery.closeLightbox()}>&times;</button>
        <button class="lightbox-prev" onclick={() => swiper?.slidePrev()}>&lsaquo;</button>

        <div class="swiper" bind:this={swiperEl}>
            <div class="swiper-wrapper">
                {#each gallery.visible as photo (photo.id)}
                    <div class="swiper-slide">
                        <div class="swiper-zoom-container">
                            <img src={photo.preview_url} alt={photo.filename} loading="lazy" />
                        </div>
                    </div>
                {/each}
            </div>
        </div>

        <button class="lightbox-next" onclick={() => swiper?.slideNext()}>&rsaquo;</button>

        <div class="lightbox-bottom">
            <p class="lightbox-filename-mobile">{gallery.lightboxPhoto?.filename ?? ''}</p>
            <div class="lightbox-bottom-actions">
                <button class="lightbox-nav-btn" onclick={() => swiper?.slidePrev()}>&lsaquo;</button>
                <button
                    class="lightbox-details-btn"
                    class:active={showDetails}
                    onclick={() => (showDetails = !showDetails)}>&#9776;</button
                >
                <button class="lightbox-nav-btn" onclick={() => swiper?.slideNext()}>&rsaquo;</button>
            </div>
        </div>

        <div class="lightbox-sidebar" class:is-open={showDetails}>
            <div class="lightbox-sidebar-handle"></div>
            <Details />
        </div>
    </div>
</div>

<style>
    .lightbox {
        position: fixed;
        inset: 0;
        z-index: 200;
        display: flex;
        flex-direction: column;
        background: #120e0c;
    } /* only used on desktop */

    .lightbox-content {
        position: relative;
        display: flex;
        flex-direction: column;
        width: 100%;
        height: 100%;
        overflow: hidden;
        user-select: none;
    }

    /* Close */
    .lightbox-close {
        position: absolute;
        top: calc(0.75rem + var(--safe-top));
        right: 0.75rem;
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.1);
        border: none;
        color: #fff;
        font-size: 1.4rem;
        line-height: 44px;
        text-align: center;
        cursor: pointer;
        z-index: 10;
        transition: background 0.2s;
        font-family: inherit;
    }

    .lightbox-close:active {
        background: rgba(255, 255, 255, 0.2);
    }

    /* Desktop nav — hidden on mobile */
    .lightbox-prev,
    .lightbox-next {
        display: none;
    }

    /* --- Mobile bottom bar --- */
    .lightbox-bottom {
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        padding: 0.5rem 1rem calc(0.65rem + var(--safe-bottom));
        background: rgba(22, 17, 15, 0.96);
        min-height: 64px;
    }

    .lightbox-filename-mobile {
        font-size: 0.7rem;
        color: rgba(245, 237, 230, 0.5);
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .lightbox-bottom-actions {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        flex-shrink: 0;
    }

    .lightbox-nav-btn {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.07);
        border: none;
        color: rgba(255, 255, 255, 0.75);
        font-size: 1.4rem;
        line-height: 44px;
        text-align: center;
        cursor: pointer;
        transition: background 0.15s;
        font-family: inherit;
    }

    .lightbox-nav-btn:active {
        background: rgba(255, 255, 255, 0.17);
    }

    .lightbox-details-btn {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.07);
        border: none;
        color: rgba(255, 255, 255, 0.75);
        font-size: 1rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition:
            background 0.15s,
            color 0.15s;
    }

    .lightbox-details-btn.active {
        background: rgba(212, 133, 122, 0.25);
        color: var(--rose-light);
    }

    .lightbox-details-btn:active {
        background: rgba(255, 255, 255, 0.17);
    }

    /* --- Sidebar — bottom sheet on mobile --- */
    .lightbox-sidebar {
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0;
        height: 72vh;
        background: linear-gradient(180deg, #242018 0%, #1e1a14 100%);
        border-top: 1px solid rgba(186, 143, 133, 0.12);
        border-radius: 16px 16px 0 0;
        padding: 0.5rem 1.25rem calc(1.75rem + var(--safe-bottom));
        overflow-y: auto;
        overscroll-behavior: contain;
        -webkit-overflow-scrolling: touch;
        color: #e8ddd8;
        z-index: 300;
        transform: translateY(100%);
        transition: transform 0.32s cubic-bezier(0.32, 0.72, 0, 1);
        box-shadow: 0 -12px 48px rgba(0, 0, 0, 0.5);
    }

    .lightbox-sidebar.is-open {
        transform: translateY(0);
    }

    .lightbox-sidebar-handle {
        width: 36px;
        height: 4px;
        border-radius: 2px;
        background: rgba(186, 143, 133, 0.25);
        margin: 0 auto 1rem;
    }

    @media (min-width: 768px) {
        /* Lightbox — centered modal, image + sidebar */
        .lightbox {
            flex-direction: row;
            align-items: center;
            justify-content: center;
            background: rgba(30, 24, 22, 0.93);
        }

        .lightbox-content {
            flex-direction: row;
            width: auto;
            height: auto;
            max-width: 95vw;
            max-height: 95vh;
            gap: 1.25rem;
            align-items: center;
            overflow: visible;
        }

        .lightbox-close {
            top: -1.25rem;
            right: -0.75rem;
            width: 2.25rem;
            height: 2.25rem;
            line-height: 2.25rem;
            font-size: 1.4rem;
            background: rgba(212, 165, 154, 0.3);
        }

        .lightbox-close:hover {
            background: rgba(212, 165, 154, 0.5);
            transform: rotate(90deg);
        }

        .lightbox-prev,
        .lightbox-next {
            display: block;
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            width: 2.75rem;
            height: 2.75rem;
            border-radius: 50%;
            background: rgba(212, 165, 154, 0.25);
            border: none;
            color: #fff;
            font-size: 1.75rem;
            line-height: 2.75rem;
            text-align: center;
            cursor: pointer;
            z-index: 10;
            transition:
                background 0.2s,
                transform 0.2s;
            font-family: inherit;
        }

        .lightbox-prev {
            left: -3.5rem;
        }
        .lightbox-next {
            right: -3.5rem;
        }

        .lightbox-prev:hover {
            background: rgba(212, 165, 154, 0.45);
            transform: translateY(-50%) scale(1.05);
        }
        .lightbox-next:hover {
            background: rgba(212, 165, 154, 0.45);
            transform: translateY(-50%) scale(1.05);
        }

        /* Mobile bottom bar hidden on desktop */
        .lightbox-bottom {
            display: none;
        }

        /* Sidebar — warm paper panel */
        .lightbox-sidebar {
            position: static;
            width: 280px;
            height: auto;
            max-height: 90vh;
            transform: none !important;
            transition: none;
            background: linear-gradient(180deg, #faf6f2 0%, #f5ede6 100%);
            border: 1px solid var(--border);
            border-top: 1px solid var(--border);
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            color: var(--text-primary);
            padding: 1.25rem;
            overflow-y: auto;
        }

        .lightbox-sidebar-handle {
            display: none;
        }
    }

    /* Carries the background so the dismiss gesture animates opacity, which is
       compositor-only, instead of repainting .lightbox. Also takes over the blur
       the old .lightbox-backdrop provided on desktop. */
    .lightbox-fade {
        position: absolute;
        inset: 0;
        background: #120e0c;
    }

    @media (min-width: 768px) {
        .lightbox-fade {
            background: rgba(30, 24, 22, 0.93);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }
    }

    .swiper {
        width: 100%;
        height: 100%;
    }
</style>
