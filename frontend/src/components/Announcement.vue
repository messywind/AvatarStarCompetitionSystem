<script setup>
import { computed } from 'vue'
import logo from '../assets/logo.png'
import bgBattle from '../assets/bg-battle.jpg'

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
  <div class="announce">
    <!-- Hero -->
    <div class="announce-hero" :style="{ backgroundImage: `url(${bgBattle})` }">
      <div class="hero-mask"></div>
      <img :src="logo" alt="百变兵团" class="hero-logo" />
      <h1 class="hero-name">{{ tournament.name }}</h1>
      <div class="hero-ribbon">
        <span class="star">★</span>
        <span class="ribbon-text">参赛公告</span>
        <span class="star">★</span>
      </div>
    </div>

    <div v-if="isEmpty" class="announce-empty">该赛事尚未配置比赛公告。</div>

    <div v-else class="announce-frame">
      <span class="corner tl"></span><span class="corner tr"></span>
      <span class="corner bl"></span><span class="corner br"></span>
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
      <span class="banner-star">★</span>
      {{ footer }}
      <span class="banner-star">★</span>
    </div>
  </div>
</template>

<style scoped>
.announce {
  width: 100%;
  color: #eaf0ff;
  background:
    radial-gradient(700px 320px at 12% -8%, rgba(255, 90, 60, 0.28), transparent 60%),
    radial-gradient(700px 340px at 92% 4%, rgba(43, 108, 255, 0.32), transparent 58%),
    linear-gradient(180deg, #0a0e27, #10152f);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.5);
  padding-bottom: 1.35rem;
}

/* Hero（与比赛详情海报同语言） */
.announce-hero {
  position: relative;
  padding: 1.8rem 1.5rem 1.6rem;
  background-size: cover;
  background-position: center 35%;
  text-align: center;
}
.hero-mask {
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(6, 9, 24, 0.35), rgba(10, 14, 39, 0.9));
}
.hero-logo { position: relative; height: 62px; width: auto; filter: drop-shadow(0 4px 16px rgba(0, 0, 0, 0.55)); }
.hero-name {
  position: relative;
  margin: 0.7rem 0 0;
  font-size: clamp(1.6rem, 4vw, 2.3rem);
  font-weight: 800;
  letter-spacing: 0.04em;
  text-shadow: 0 3px 18px rgba(0, 0, 0, 0.6);
}
.hero-ribbon {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 0.8rem;
  margin-top: 0.9rem;
  padding: 0.42rem 1.6rem;
  font-size: clamp(1.25rem, 3.2vw, 1.7rem);
  font-weight: 900;
  letter-spacing: 0.28em;
  text-indent: 0.28em;
  color: #ffe9a8;
  background: linear-gradient(180deg, rgba(43, 108, 255, 0.55), rgba(18, 44, 120, 0.7));
  border: 1px solid rgba(140, 180, 255, 0.55);
  border-radius: 999px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.55);
  box-shadow: 0 6px 24px rgba(20, 50, 140, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.22);
}
.hero-ribbon .star { font-size: 0.8em; color: #ffd66b; letter-spacing: 0; text-indent: 0; }

.announce-empty { padding: 2.5rem 1.5rem; text-align: center; color: #9aa6d4; }

/* 科技感边框面板 */
.announce-frame {
  position: relative;
  margin: 1.3rem 1.35rem 0;
  padding: 0.55rem 1.1rem;
  background: rgba(10, 16, 44, 0.72);
  border: 1px solid rgba(120, 160, 255, 0.32);
  border-radius: 16px;
  box-shadow: inset 0 0 34px rgba(43, 108, 255, 0.14), 0 10px 30px rgba(0, 0, 0, 0.35);
}
.corner {
  position: absolute;
  width: 22px; height: 22px;
  border: 2px solid #5ad1ff;
  filter: drop-shadow(0 0 6px rgba(90, 209, 255, 0.7));
}
.corner.tl { top: -2px; left: -2px; border-right: none; border-bottom: none; border-radius: 14px 0 0 0; }
.corner.tr { top: -2px; right: -2px; border-left: none; border-bottom: none; border-radius: 0 14px 0 0; }
.corner.bl { bottom: -2px; left: -2px; border-right: none; border-top: none; border-radius: 0 0 0 14px; }
.corner.br { bottom: -2px; right: -2px; border-left: none; border-top: none; border-radius: 0 0 14px 0; }

.announce-list { list-style: none; margin: 0; padding: 0; }
.announce-item {
  display: flex;
  align-items: flex-start;
  gap: 0.9rem;
  padding: 0.85rem 0.2rem;
}
.announce-item + .announce-item { border-top: 1px dashed rgba(120, 160, 255, 0.32); }

/* 星形序号徽章：两层旋转方块叠出八角星 */
.no {
  position: relative;
  flex: none;
  width: 34px; height: 34px;
  margin-top: 0.05rem;
  display: grid;
  place-items: center;
}
.no::before,
.no::after {
  content: '';
  position: absolute;
  inset: 4px;
  border-radius: 6px;
  background: linear-gradient(180deg, #7fd4ff, #2b6cff);
  box-shadow: 0 3px 10px rgba(43, 108, 255, 0.5);
}
.no::after { transform: rotate(45deg); }
.no i {
  position: relative;
  z-index: 1;
  font-style: normal;
  font-weight: 900;
  font-size: 0.95rem;
  color: #fff;
  text-shadow: 0 1px 3px rgba(10, 30, 80, 0.6);
}

.item-text {
  margin: 0.28rem 0 0;
  font-size: 0.95rem;
  line-height: 1.75;
  font-weight: 600;
  color: rgba(234, 240, 255, 0.94);
  overflow-wrap: anywhere;
}
.item-text .hl {
  color: #ffd35e;
  font-weight: 800;
  text-shadow: 0 0 14px rgba(255, 190, 60, 0.35);
}

/* 底部金色标语横幅 */
.announce-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin: 1.15rem 1.35rem 0;
  padding: 0.78rem 1rem;
  border-radius: 12px;
  background: linear-gradient(180deg, #ffd970, #ff9e2c);
  border: 1px solid rgba(255, 240, 190, 0.85);
  color: #8a2200;
  font-weight: 900;
  font-size: clamp(1.02rem, 2.6vw, 1.3rem);
  letter-spacing: 0.06em;
  text-align: center;
  box-shadow: 0 10px 26px rgba(255, 150, 30, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.6);
}
.banner-star { font-size: 0.85em; color: #b03a00; }

@media (max-width: 560px) {
  .announce-frame { margin: 1.1rem 0.9rem 0; padding: 0.4rem 0.75rem; }
  .announce-banner { margin: 1rem 0.9rem 0; }
  .announce-item { gap: 0.7rem; }
  .no { width: 30px; height: 30px; }
  .item-text { font-size: 0.9rem; }
}
</style>
