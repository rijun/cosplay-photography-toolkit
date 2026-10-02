<script lang="ts">
  let count = $state(0)
</script>

<div class="vite-probe probe">
  <p>Svelte {count === 0 ? 'mounted' : 'is reactive'}.</p>
  <button onclick={() => count++}>clicked {count}</button>
</div>

<style>
  .probe {
    padding: 1rem;
    border: 1px dashed currentColor;
    border-radius: 8px;
  }
</style>
