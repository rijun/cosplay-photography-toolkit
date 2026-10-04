<script lang="ts">
    import type { Photo } from './lib/photo'
    import { untrack } from 'svelte'
    import Swiper from 'swiper'
    import { Zoom } from 'swiper/modules'
    import 'swiper/css'
    import 'swiper/css/zoom'

    const FLAG_HEX: Record<number, string> = {
        0: '#22a355', // final
        1: '#d4857a', // rose
        2: '#a888b8', // lavender
        3: '#88a888', // sage
        4: '#7a9ab8', // sky
        5: '#c4a050', // amber
    }

    let { photos }: { photos: Photo[] } = $props()
    let openIndex = $state<number | null>(null)
    let swiperEl = $state<HTMLElement | undefined>()
    let lightboxEl = $state<HTMLElement | undefined>()
    let backdropEl = $state<HTMLElement | undefined>()
    let swiper: Swiper | undefined

    // Downward distance that commits to closing.
    const DISMISS_AT = 40

    // Pulling back this far from the furthest point reads as "no", like iOS Photos.
    const PULL_BACK = 20

    // Plain variables, not $state: these drive styles imperatively, per frame.
    let startX = 0
    let startY = 0
    let maxDy = 0
    let dragSpan = 0
    let tracking = false
    let dragging = false
    let dismissedAt = 0

    function openPhoto(i: number) {
        if (Date.now() - dismissedAt < 300) return
        openIndex = i
    }

    function onPointerDown(e: PointerEvent) {
        // While zoomed, vertical belongs to panning.
        if (swiper && swiper.zoom.scale !== 1) return
        lightboxEl?.setPointerCapture(e.pointerId)
        startX = e.clientX
        startY = e.clientY
        maxDy = 0
        // Scaling runs from here to the bottom of the screen, so it never clamps early.
        dragSpan = Math.max(window.innerHeight - e.clientY, 1)
        tracking = true
        dragging = false
    }

    function onPointerMove(e: PointerEvent) {
        if (!tracking || !swiperEl || !backdropEl) return
        const dy = e.clientY - startY
        const dx = e.clientX - startX

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

    function onPointerUp(e: PointerEvent) {
        const dy = e.clientY - startY
        // Dragging back up from the furthest point cancels, however far down you are.
        const pulledBack = dy < maxDy - PULL_BACK
        if (dragging && !pulledBack && dy > DISMISS_AT) {
            // A short, fast flick stays within the browser's tap slop, so a click is
            // still synthesized after pointerup — and by then the lightbox is gone and
            // it lands on the grid card underneath, reopening it.
            dismissedAt = Date.now()
            tracking = false
            dragging = false
            openIndex = null
            return
        }
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

    // Runs after the element is mounted; cleanup tears Swiper down on close
    $effect(() => {
        if (!swiperEl) return
        swiper = new Swiper(swiperEl, {
            modules: [Zoom],
            // untrack: reading openIndex here would rebuild Swiper on every change.
            initialSlide: untrack(() => openIndex) ?? 0,
            // Loads the active slide plus 2 either side
            lazyPreloadPrevNext: 2,
            zoom: {
                limitToOriginalSize: true, // never zoom past the preview's real resolution
                toggle: true, // double-tap to zoom
            },
        })
        // Stops the grid scrolling behind the lightbox
        document.body.style.overflow = 'hidden'
        return () => {
            swiper?.destroy()
            swiper = undefined
            document.body.style.overflow = ''
        }
    })
</script>

<div class="photo-grid">
    {#each photos as photo, i (photo.id)}
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div class="photo-card" onclick={() => openPhoto(i)}>
            <img src={photo.thumbnail_url} alt={photo.filename} loading="lazy" />
            {#if photo.flags.length}
                <span class="mark">
                    {#each photo.flags as flag (flag)}
                        <span class="dot" style="background: {FLAG_HEX[flag]}"></span>
                    {/each}
                </span>
            {/if}
        </div>
    {/each}
</div>
{#if openIndex !== null}
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
        class="lightbox"
        bind:this={lightboxEl}
        onpointerdown={onPointerDown}
        onpointermove={onPointerMove}
        onpointerup={onPointerUp}
        onpointercancel={reset}
    >
        <div class="backdrop" bind:this={backdropEl}></div>
        <div class="swiper" bind:this={swiperEl}>
            <div class="swiper-wrapper">
                {#each photos as photo (photo.id)}
                    <div class="swiper-slide">
                        <div class="swiper-zoom-container">
                            <img src={photo.preview_url} alt={photo.filename} loading="lazy" />
                        </div>
                    </div>
                {/each}
            </div>
        </div>
    </div>
{/if}

<style>
    .lightbox {
        background: none;
    }

    .backdrop {
        position: absolute;
        inset: 0;
        background: #120e0c;
    }

    .swiper {
        width: 100%;
        height: 100%;
    }

    .photo-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.5rem;
    }

    /* Design: image flush to the card edge, no frame. */
    .photo-card {
        padding: 0;
        border-radius: 8px;
        box-shadow: none;
    }

    .photo-card img {
        border-radius: 0;
    }

    /* Scrim pill: dots on a plate, so they read over any photo. */
    .mark {
        position: absolute;
        left: 6px;
        bottom: 6px;
        display: flex;
        gap: 5px;
        padding: 4px 6px;
        border-radius: 10px;
        background: rgba(25, 19, 16, 0.35);
        backdrop-filter: blur(12px) saturate(1.6);
        -webkit-backdrop-filter: blur(12px) saturate(1.6);
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.18);
    }

    .dot {
        width: 11px;
        height: 11px;
        border-radius: 50%;
    }
</style>
