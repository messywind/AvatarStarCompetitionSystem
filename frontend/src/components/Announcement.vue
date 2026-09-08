<script setup>
import { computed } from 'vue'
import logo from '../assets/logo.png'
import bgBattle from '../assets/game/flag.webp'
import Icon from './Icon.vue'
import './poster.css'

const props = defineProps({
  tournament: { type: Object, required: true },
})

const poster = computed(() => props.tournament?.poster || {})

const lines = (text) => (text || '').split(/\r?\n/).map((s) => s.trim()).filter(Boolean)

// '**文字**' → 高亮片段；按分隔构造 span，避免注入
function segments(line) {
  return line
    .split(/\*\*(.+?)\*\*/g)
    .map((text, i) => ({ text, hl: i % 2 === 1 }))
    .filter((s) => s.text)
}

const items = computed(() => lines(poster.value.announcement).map((l) => segments(l)))
const footer = computed(() => (poster.value.announcement_footer || '').trim())
const isEmpty = computed(() => !items.value.length)
</script>

<template>
  <div class="announce competition-poster">
    <!-- Hero -->
    <div class="announce-hero" :style="{ backgroundImage: `url(${bgBattle})` }">
      <div class="hero-mask"></div>
      <img :src="logo" alt="百变兵团" class="hero-logo" />
      <h1 class="hero-name">{{ tournament.name }}</h1>
      <div class="hero-ribbon">
        <Icon name="flag" :size="17" />
        <span class="ribbon-text">参赛公告</span>

      </div>
    </div>

    <div v-if="isEmpty" class="announce-empty">该赛事尚未配置比赛公告。</div>

    <div v-else class="announce-frame">

      <ol class="announce-list">
        <li v-for="(item, i) in items" :key="i" class="announce-item">
          <span class="no"><i>{{ i + 1 }}</i></span>
          <p class="item-text">
            <template v-for="(seg, j) in item" :key="j">
              <strong v-if="seg.hl" class="hl">{{ seg.text }}</strong>
              <template v-else>{{ seg.text }}</template>
            </template>
          </p>
        </li>
      </ol>
    </div>

    <div v-if="footer && !isEmpty" class="announce-banner">
      <Icon name="star" :size="18" />
      {{ footer }}

    </div>
  </div>
</template>

<style scoped>
.announce { padding-bottom: 1.5rem; }
.hero-ribbon { display: inline-flex; align-items: center; gap: .55rem; margin-top: 1rem; color: #ffcb9b; font-size: .84rem; font-weight: 650; }
.announce-frame { margin: .4rem 2rem 0; }
.announce-list { list-style: none; padding: 0; margin: 0; }
.announce-item { display: flex; align-items: flex-start; gap: 1rem; padding: 1.3rem 0; }
.announce-item + .announce-item { border-top: 1px solid var(--border); }
.no { width: 29px; height: 29px; margin-top: .15rem; border-radius: 5px; background: #edf1f5; color: #556d82; display: grid; place-items: center; flex: none; }
.no i { font-size: .78rem; font-style: normal; font-weight: 700; }
.item-text { margin: .15rem 0 0; font-size: .88rem; line-height: 1.9; color: #536173; overflow-wrap: anywhere; }
.hl { color: #96540d; font-weight: 750; background: #fff1d8; padding: .1rem .2rem; }
.announce-banner { display: flex; align-items: center; gap: .8rem; margin: .5rem 2rem 0; padding: 1rem 1.2rem; border-radius: 7px; background: var(--dark); color: #ffcc9c; font-weight: 650; font-size: .9rem; line-height: 1.7; }
@media(max-width:560px) { .announce-frame { margin-inline: 1.25rem; } .announce-banner { margin-inline: 1.25rem; } .announce-item { gap: .7rem; } .item-text { font-size: .82rem; } }
</style>
