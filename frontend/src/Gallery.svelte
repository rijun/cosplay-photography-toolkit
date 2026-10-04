<script lang="ts">
    import PhotoGrid from './PhotoGrid.svelte'
    import FlagPicker from './FlagPicker.svelte'
    import { gallery } from './lib/state.svelte'
    import { fade } from 'svelte/transition'
</script>

<div class="gallery">
    <FlagPicker />
    <PhotoGrid />
    <!-- Toast notification -->
    {#if gallery.toast}
        <div class="toast" transition:fade>{gallery.toast}</div>
    {/if}
</div>

<style>
    .toast {
        position: fixed;
        top: calc(1.25rem + var(--safe-top));
        left: 50%;
        transform: translateX(-50%);
        padding: 0.6rem 1.25rem;
        background: rgba(74, 50, 46, 0.93);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        color: #f5ede6;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        z-index: 400;
        white-space: nowrap;
    }
</style>
