<script lang="ts">
import type {Photo} from "./photo";
import Swiper from 'swiper';
import 'swiper/css';

let { photos }: { photos: Photo[] } = $props()
let openIndex = $state<number | null>(null)
let swiperEl = $state<HTMLElement | undefined>()

// Runs after the element is mounted; cleanup tears Swiper down on close
$effect(() => {
    if (!swiperEl) return
    const swiper = new Swiper(swiperEl, {
        initialSlide: openIndex ?? 0,
        // Loads the active slide plus 2 either side
        lazyPreloadPrevNext: 2,
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
                    <div class="swiper-slide" onclick={() => (openIndex = null)}>
                        <img src={photo.preview_url} alt="" loading="lazy">
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

    .swiper-slide {
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .swiper-slide img {
        max-width: 100%;
        max-height: 100%;
    }
</style>
