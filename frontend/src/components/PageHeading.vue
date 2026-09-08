<script setup>
import Icon from './Icon.vue'
defineProps({ title: String, description: String, icon: { type: String, default: 'flag' } })
</script>
<template>
  <div class="page-heading">
    <div class="heading-icon"><Icon :name="icon" :size="25" /></div>
    <div class="heading-copy"><h1>{{ title }}</h1><p v-if="description">{{ description }}</p></div>
    <div v-if="$slots.default" class="heading-action"><slot /></div>
  </div>
</template>
<style scoped>
.page-heading { display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; }
.heading-icon { width: 52px; height: 52px; display: grid; place-items: center; border-radius: 10px; background: var(--dark); color: var(--accent-2); flex: none; }
.heading-copy { min-width: 0; }
h1 { margin: 0; font-size: 1.85rem; }
p { color: var(--muted); margin: .4rem 0 0; max-width: 76ch; font-size: .87rem; }
.heading-action { margin-left: auto; flex: none; }
@media(max-width:720px) { .page-heading { flex-wrap: wrap; gap: .8rem; margin-bottom: 1.5rem; } .heading-icon { width: 44px; height: 44px; } .heading-copy { flex: 1; } h1 { font-size: 1.5rem; } p { font-size: .82rem; } .heading-action { margin-left: 0; } }
</style>
