<script lang="ts">
import type {Photo} from "./photo";

let { photos }: { photos: Photo[] } = $props()
let openIndex = $state<number | null>(null)
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
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="lightbox" onclick={() => (openIndex = null)}>
        <img class="lightbox-image" src={photos[openIndex].preview_url} alt="">
    </div>
{/if}
