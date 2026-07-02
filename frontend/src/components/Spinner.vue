<script setup>
defineProps({
  label: { type: String, default: '' },
  size: { type: Number, default: 20 },
})
</script>

<template>
  <div class="spin-wrap" role="status" aria-live="polite">
    <span class="spinner" :style="{ width: size + 'px', height: size + 'px' }" aria-hidden="true"></span>
    <span v-if="label">{{ label }}</span>
  </div>
</template>
