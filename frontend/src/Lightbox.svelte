<script lang="ts">
    import { untrack } from 'svelte'
    import Swiper from 'swiper'
    import { Zoom, Navigation } from 'swiper/modules'
    import 'swiper/css'
    import 'swiper/css/zoom'
    import 'swiper/css/navigation'
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

    // Follows the active photo only once a slide settles, so the stage never resizes mid-swipe.
    let stageId = $state(untrack(() => gallery.lightboxPhoto?.id))
    // Sizes the desktop stage so the arrows and sidebar hug the photo.
    const stageRatio = $derived((stageId !== undefined && gallery.ratios[stageId]) || 2 / 3)

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
            modules: [Zoom, Navigation],
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
                slideChangeTransitionEnd: () => (stageId = gallery.lightboxPhoto?.id),
            },
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev',
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
    <div class="fade" bind:this={backdropEl}></div>

    <div class="content" style:--stage-ratio={stageRatio}>
        <button class="close" onclick={() => gallery.closeLightbox()}>&times;</button>

        <div class="swiper" bind:this={swiperEl}>
            <div class="swiper-button-prev"></div>
            <div class="swiper-wrapper">
                {#each gallery.visible as photo (photo.id)}
                    <div class="swiper-slide">
                        <div class="swiper-zoom-container">
                            <img
                                src={photo.preview_url}
                                alt={photo.filename}
                                loading="lazy"
                                onload={(e) => gallery.learnRatio(photo.id, e)}
                            />
                        </div>
                    </div>
                {/each}
            </div>
            <div class="swiper-button-next"></div>
        </div>

        <div class="bottom">
            <p class="filename-mobile">{gallery.lightboxPhoto?.filename ?? ''}</p>
            <button class="details-btn" class:active={showDetails} onclick={() => (showDetails = !showDetails)}
                >&#9776;</button
            >
        </div>

        <div class="sidebar" class:is-open={showDetails}>
            <div class="sidebar-handle"></div>
            <Details />
        </div>
    </div>
</div>

<style>
    /* --- Shell --- */
    .lightbox {
        position: fixed;
        inset: 0;
        z-index: 200;
        display: flex;
        flex-direction: column;
    }

    /* Holds the background so the dismiss gesture fades opacity instead of repainting. */
    .fade {
        position: absolute;
        inset: 0;
        background: #120e0c;
    }

    .content {
        position: relative;
        display: flex;
        flex-direction: column;
        width: 100%;
        height: 100%;
        overflow: hidden;
        user-select: none;
    }

    /* --- Close --- */
    .close {
        position: absolute;
        top: calc(0.75rem + var(--safe-top));
        right: 0.75rem;
        z-index: 10;
        width: 44px;
        height: 44px;
        border: none;
        border-radius: 50%;
        font-family: inherit;
        font-size: 1.4rem;
        line-height: 44px;
        text-align: center;
        color: #fff;
        background: rgba(255, 255, 255, 0.1);
        cursor: pointer;
        transition:
            background 0.2s,
            transform 0.2s;
    }

    .close:active {
        background: rgba(255, 255, 255, 0.2);
    }

    /* --- Swiper --- */
    .swiper {
        flex: 1;
        /* Swiper's auto side margins block the column stretch on mobile. */
        width: 100%;
        min-width: 0;
        height: 100%;
    }

    .swiper-button-prev,
    .swiper-button-next {
        color: rgba(var(--cream-rgb), 0.75);
    }

    /* --- Bottom bar (mobile) --- */
    .bottom {
        display: flex;
        flex-shrink: 0;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        min-height: 64px;
        padding: 0.5rem 1rem calc(0.65rem + var(--safe-bottom));
        background: rgba(22, 17, 15, 0.96);
    }

    .filename-mobile {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        font-size: 0.7rem;
        white-space: nowrap;
        text-overflow: ellipsis;
        color: rgba(var(--linen-rgb), 0.5);
    }

    .details-btn {
        display: flex;
        flex-shrink: 0;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
        border: none;
        border-radius: 50%;
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.75);
        background: rgba(255, 255, 255, 0.07);
        cursor: pointer;
        transition:
            background 0.15s,
            color 0.15s;
    }

    .details-btn.active {
        color: var(--rose-light);
        background: rgba(var(--rose-rgb), 0.25);
    }

    .details-btn:active {
        background: rgba(255, 255, 255, 0.17);
    }

    /* --- Sidebar (bottom sheet on mobile) --- */
    .sidebar {
        position: fixed;
        right: 0;
        bottom: 0;
        left: 0;
        z-index: 300;
        height: 72vh;
        padding: 0.5rem 1.25rem calc(1.75rem + var(--safe-bottom));
        overflow-y: auto;
        overscroll-behavior: contain;
        -webkit-overflow-scrolling: touch;
        border-top: 1px solid rgba(var(--dust-rgb), 0.12);
        border-radius: 16px 16px 0 0;
        color: var(--text-on-dark);
        background: linear-gradient(180deg, #242018 0%, #1e1a14 100%);
        box-shadow: 0 -12px 48px rgba(0, 0, 0, 0.5);
        transform: translateY(100%);
        transition: transform 0.32s cubic-bezier(0.32, 0.72, 0, 1);
    }

    .sidebar.is-open {
        transform: translateY(0);
    }

    .sidebar-handle {
        width: 36px;
        height: 4px;
        margin: 0 auto 1rem;
        border-radius: 2px;
        background: rgba(var(--dust-rgb), 0.25);
    }

    /* --- Desktop: centered modal, image + sidebar --- */
    @media (min-width: 768px) {
        .lightbox {
            flex-direction: row;
            align-items: center;
            justify-content: center;
        }

        .fade {
            background: rgba(30, 24, 22, 0.93);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }

        .content {
            flex-direction: row;
            align-items: center;
            gap: 1.25rem;
            width: auto;
            height: 90vh;
            overflow: visible;
        }

        .close {
            top: -1.25rem;
            right: -0.75rem;
            width: 2.25rem;
            height: 2.25rem;
            line-height: 2.25rem;
            background: rgba(var(--rose-soft-rgb), 0.3);
        }

        .close:hover {
            background: rgba(var(--rose-soft-rgb), 0.5);
            transform: rotate(90deg);
        }

        /* Matches the settled photo's shape; capped so the sidebar still fits in 95vw. */
        .swiper {
            flex: none;
            width: min(calc(95vw - 280px - 1.25rem), calc(90vh * var(--stage-ratio)));
            border-radius: 8px;
        }

        .bottom {
            display: none;
        }

        /* Stretches to the swiper's height. */
        .sidebar {
            position: static;
            display: flex;
            flex-direction: column;
            align-self: stretch;
            width: 280px;
            height: auto;
            padding: 1.25rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            background: linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 100%);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            transform: none;
            transition: none;
        }

        .sidebar-handle {
            display: none;
        }
    }
</style>
