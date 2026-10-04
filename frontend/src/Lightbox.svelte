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

    // Dragging the sheet's handle down this far closes it.
    const SHEET_CLOSE_AT = 80

    let showDetails = $state(false)
    let swiperEl = $state<HTMLElement | undefined>()
    let prevEl = $state<HTMLElement | undefined>()
    let nextEl = $state<HTMLElement | undefined>()
    let backdropEl = $state<HTMLElement | undefined>()
    let sidebarEl = $state<HTMLElement | undefined>()
    let swiper: Swiper | undefined

    // Follows the active photo only once scrolling settles, so the stage never resizes mid-swipe.
    let stageId = $state(untrack(() => gallery.lightboxPhoto?.id))
    // Sizes the desktop stage so the arrows and sidebar hug the photo.
    const stageRatio = $derived((stageId !== undefined && gallery.ratios[stageId]) || 2 / 3)

    // Debounce the stage update until scrolling has been still for a moment.
    let settleTimer: ReturnType<typeof setTimeout> | undefined

    // Plain variables, not $state: these drive styles imperatively, per frame.
    const pointers = new Set<number>()
    let startX = 0
    let startY = 0
    let maxDy = 0
    let dragSpan = 0
    let tracking = false
    let dragging = false

    $effect(() => {
        if (!swiperEl || !prevEl || !nextEl) return
        swiper = new Swiper(swiperEl, {
            modules: [Zoom, Navigation],
            // Native scroll-snap instead of a transform transition on .swiper-wrapper: WebKit
            // (iOS 26, address bar collapsed) and Firefox skip that transition once the slide
            // row is mostly off-screen. Costs mouse drag-to-swipe; arrows, keys and trackpad stay.
            cssMode: true,
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
                // cssMode has no transition events; fires per scroll frame instead.
                setTranslate: () => {
                    clearTimeout(settleTimer)
                    settleTimer = setTimeout(() => (stageId = gallery.lightboxPhoto?.id), 150)
                },
                // Tapping the photo closes the mobile details sheet.
                tap: () => (showDetails = false),
            },
            // Outside .swiper, so the dismiss drag moves the photo but not the arrows.
            navigation: { prevEl, nextEl },
        })
        // Stops the grid scrolling behind the lightbox.
        document.body.style.overflow = 'hidden'
        return () => {
            clearTimeout(settleTimer)
            swiper?.destroy()
            swiper = undefined
            document.body.style.overflow = ''
        }
    })

    function onPointerDown(event: PointerEvent) {
        // The sidebar holds text and buttons; dragging there is never a dismiss.
        if ((event.target as Element).closest('.sidebar')) return
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

    // Sheet handle: a tap closes the sheet; a drag moves it and closes past SHEET_CLOSE_AT.
    let sheetStartY: number | null = null

    function onHandleDown(event: PointerEvent) {
        if (!sidebarEl) return
        const handle = event.currentTarget as Element
        // Keeps move/up coming to the handle even when the finger leaves it.
        handle.setPointerCapture(event.pointerId)
        sheetStartY = event.clientY
        sidebarEl.style.transition = 'none'
    }

    function onHandleMove(event: PointerEvent) {
        if (sheetStartY === null || !sidebarEl) return
        sidebarEl.style.transform = `translateY(${Math.max(event.clientY - sheetStartY, 0)}px)`
    }

    function onHandleUp(event: PointerEvent) {
        if (sheetStartY === null) return
        const dy = event.clientY - sheetStartY
        if (dy < 5 || dy > SHEET_CLOSE_AT) showDetails = false
        releaseSheet()
    }

    // A canceled pointer often reports clientY 0, so it never counts as a tap or drag.
    function onHandleCancel() {
        if (sheetStartY !== null) releaseSheet()
    }

    function releaseSheet() {
        sheetStartY = null
        if (!sidebarEl) return
        // Clearing both in one frame animates from the dragged spot to open or closed.
        sidebarEl.style.transition = ''
        sidebarEl.style.transform = ''
    }

    function onKeydown(event: KeyboardEvent) {
        // Arrows move the caret while typing a comment.
        if (event.target instanceof HTMLTextAreaElement || event.target instanceof HTMLInputElement) return
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
        <div class="sidebar" class:is-open={showDetails} bind:this={sidebarEl}>
            <button
                class="sidebar-handle"
                aria-label="Close details"
                onpointerdown={onHandleDown}
                onpointermove={onHandleMove}
                onpointerup={onHandleUp}
                onpointercancel={onHandleCancel}
            ></button>
            <Details />
        </div>

        <div class="stage">
            <button class="close" aria-label="Close" onclick={() => gallery.closeLightbox()}>
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M6 6l12 12M18 6L6 18" />
                </svg>
            </button>
            <div class="swiper-button-prev" bind:this={prevEl}></div>
            <div class="swiper" bind:this={swiperEl}>
                <div class="swiper-wrapper">
                    {#each gallery.lightboxPhotos as photo (photo.id)}
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
            </div>
            <div class="swiper-button-next" bind:this={nextEl}></div>
        </div>

        <div class="bottom">
            <p class="filename-mobile">{gallery.lightboxPhoto?.filename ?? ''}</p>
            <button class="details-btn" class:active={showDetails} onclick={() => (showDetails = !showDetails)}
                >&#9776;</button
            >
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

    /* --- Content --- */
    .content {
        position: relative;
        display: flex;
        flex-direction: column;
        width: 100%;
        height: 100%;
        overflow: hidden;
        user-select: none;
    }

    /* --- Sidebar (bottom sheet on mobile) --- */
    .sidebar {
        position: fixed;
        right: 0;
        bottom: 0;
        left: 0;
        z-index: 300;
        height: 72vh;
        /* 4rem clears the bottom bar sitting on top of the sheet. */
        padding: 0.5rem 1.25rem calc(4rem + 1.75rem + var(--safe-bottom));
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

    /* Full-width touch target; the visible bar is ::before. */
    .sidebar-handle {
        display: block;
        width: 100%;
        margin-bottom: 0.5rem;
        padding: 0.5rem 0;
        border: none;
        background: none;
        cursor: grab;
        touch-action: none;
    }

    .sidebar-handle::before {
        content: '';
        display: block;
        width: 36px;
        height: 4px;
        margin: 0 auto;
        border-radius: 2px;
        background: rgba(var(--dust-rgb), 0.25);
    }

    /* --- Stage: close, arrows and swiper; only .swiper moves on the dismiss drag --- */
    .stage {
        position: relative;
        flex: 1;
        min-width: 0;
        min-height: 0;
    }

    .close {
        position: absolute;
        top: calc(0.75rem + var(--safe-top));
        right: 0.75rem;
        z-index: 10;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
        border: none;
        border-radius: 50%;
        color: rgba(var(--cream-rgb), 0.75);
        background: rgba(255, 255, 255, 0.1);
        cursor: pointer;
        transition:
            background 0.2s,
            transform 0.2s;
    }

    .close:active {
        background: rgba(255, 255, 255, 0.2);
    }

    .close svg {
        width: 45%;
        height: 45%;
        fill: none;
        stroke: currentColor;
        stroke-width: 2;
        stroke-linecap: round;
    }

    .swiper-button-prev,
    .swiper-button-next {
        color: rgba(var(--cream-rgb), 0.75);
    }

    .swiper {
        width: 100%;
        height: 100%;
    }

    /* cssMode: the browser scrolls sideways; vertical drags stay ours for pull-to-close. */
    .swiper-wrapper {
        touch-action: pan-x;
    }

    /* A fast flick would otherwise scroll past several photos. */
    .swiper-slide {
        scroll-snap-stop: always;
    }

    /* --- Bottom bar (mobile) --- */
    /* Above the sheet, so the details button can close it again. */
    .bottom {
        position: relative;
        z-index: 301;
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

    /* --- Desktop: centered modal, sidebar + image --- */
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

        /* Stretches to the stage's height. */
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

        /* Matches the settled photo's shape; capped so the sidebar still fits in 95vw. */
        .stage {
            flex: none;
            width: min(calc(95vw - 280px - 1.25rem), calc(90vh * var(--stage-ratio)));
            height: 100%;
        }

        .close {
            top: 1rem;
            right: 1rem;
            width: 2.25rem;
            height: 2.25rem;
            background: rgba(var(--rose-soft-rgb), 0.3);
        }

        .close:hover {
            background: rgba(var(--rose-soft-rgb), 0.5);
            transform: rotate(90deg);
        }

        .swiper {
            border-radius: 8px;
        }

        .bottom {
            display: none;
        }
    }
</style>
