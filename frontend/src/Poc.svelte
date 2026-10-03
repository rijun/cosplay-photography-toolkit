<script lang="ts">
import type { Photo } from "./photo";
import Swiper from 'swiper';
import { Zoom } from 'swiper/modules'
import 'swiper/css';
import 'swiper/css/zoom';

let { photos }: { photos: Photo[] } = $props()
let openIndex = $state<number | null>(null)
let swiperEl = $state<HTMLElement | undefined>()

// Runs after the element is mounted; cleanup tears Swiper down on close
$effect(() => {
    if (!swiperEl) return
    const swiper = new Swiper(swiperEl, {
        modules: [Zoom],
        initialSlide: openIndex ?? 0,
        // Loads the active slide plus 2 either side
        lazyPreloadPrevNext: 2,
        zoom: {
            limitToOriginalSize: true, // When set to true, the image will not be scaled past 100% of its original size
            toggle: true                // enable/disable zoom-in by slide's double tap
        }
    })
    // Stops the grid scrolling behind the lightbox
    document.body.style.overflow = 'hidden'
    return () => {
        swiper.destroy()
        document.body.style.overflow = ''
    }
})
</script>

<div class="photo-grid">
    {#each photos as photo, i}
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div class="photo-card" onclick={() => (openIndex = i)}>
            <img src={photo.thumbnail_url} alt={photo.filename} loading="lazy">
        </div>
    {/each}
</div>
{#if openIndex !== null}
    <div class="lightbox">
        <div class="swiper" bind:this={swiperEl}>
            <div class="swiper-wrapper">
                {#each photos as photo}
                    <!-- svelte-ignore a11y_click_events_have_key_events -->
                    <!-- svelte-ignore a11y_no_static_element_interactions -->
                    <div class="swiper-slide">
                        <div class="swiper-zoom-container">
                            <img src={photo.preview_url} alt="" loading="lazy">
                        </div>
                    </div>
                {/each}
            </div>
        </div>
    </div>
{/if}

<style>
    .swiper {
        width: 100%;
        height: 100%;
    }
</style>
