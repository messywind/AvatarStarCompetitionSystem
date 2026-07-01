<script setup>
import { computed } from 'vue'
import { formatDeadline } from '../time'
import logo from '../assets/logo.png'
import bgBattle from '../assets/bg-battle.jpg'

const props = defineProps({
  tournament: { type: Object, required: true },
})

const poster = computed(() => props.tournament?.poster || {})

const lines = (text) => (text || '').split(/\r?\n/).map((s) => s.trim()).filter(Boolean)

const rules = computed(() =>
  [
    { icon: '⚔️', label: '比赛形式', key: 'format' },
    { icon: '🛡️', label: '职业限制', key: 'profession_limit' },
    { icon: '🚩', label: '模式限制', key: 'mode_limit' },
    { icon: '💊', label: '药物及道具限制', key: 'item_limit' },
    { icon: '🎽', label: '装备限制', key: 'equipment_limit' },
    { icon: '⭐', label: '其他限制', key: 'other_limit' },
  ]
    .map((r) => ({ ...r, items: lines(poster.value[r.key]) }))
    .filter((r) => r.items.length)
)

const rewards = computed(() =>
  [
    { icon: '🏆', label: '冠军', key: 'reward_champion', tier: 'gold' },
    { icon: '🥈', label: '亚军', key: 'reward_runner_up', tier: 'silver' },
    { icon: '🥉', label: '季军', key: 'reward_third', tier: 'bronze' },
    { icon: '🎖️', label: '殿军', key: 'reward_fourth', tier: 'purple' },
  ]
    .map((r) => ({ ...r, items: lines(poster.value[r.key]) }))
    .filter((r) => r.items.length)
)

const rewardOther = computed(() => lines(poster.value.reward_other))

const isEmpty = computed(() => !rules.value.length && !rewards.value.length && !rewardOther.value.length)
</script>

<template>
  <div class="poster">
    <!-- Hero -->
    <div class="poster-hero" :style="{ backgroundImage: `url(${bgBattle})` }">
      <div class="hero-mask"></div>
      <img :src="logo" alt="百变兵团" class="hero-logo" />
      <h1 class="hero-name">{{ tournament.name }}</h1>
      <p v-if="tournament.description" class="hero-desc">{{ tournament.description }}</p>
    </div>

    <div v-if="isEmpty" class="poster-empty">
      该赛事尚未配置比赛详情。
    </div>

    <div v-else class="poster-body">
      <!-- Rules -->
      <section v-if="rules.length" class="col rules-col">
        <h2 class="col-title"><span class="bar"></span>参赛规则</h2>
        <div v-for="r in rules" :key="r.key" class="rule">
          <div class="rule-head"><span class="rule-icon">{{ r.icon }}</span>{{ r.label }}</div>
          <ul class="rule-list">
            <li v-for="(line, i) in r.items" :key="i">{{ line }}</li>
          </ul>
        </div>
      </section>

      <!-- Rewards -->
      <section v-if="rewards.length || rewardOther.length" class="col rewards-col">
        <h2 class="col-title"><span class="bar gold"></span>官方奖励</h2>
        <div v-for="r in rewards" :key="r.key" class="reward" :class="r.tier">
          <div class="reward-medal">{{ r.icon }}</div>
          <div class="reward-body">
            <div class="reward-label">{{ r.label }}</div>
            <p v-for="(line, i) in r.items" :key="i" class="reward-text">{{ line }}</p>
          </div>
        </div>
        <div v-if="rewardOther.length" class="reward-other">
          <span class="gift">🎁</span>
          <div>
            <p v-for="(line, i) in rewardOther" :key="i">{{ line }}</p>
          </div>
        </div>
      </section>
    </div>

    <!-- Footer -->
    <div class="poster-footer">
      <span class="foot-clock">🕒 报名截止时间</span>
      <strong class="foot-deadline">{{ formatDeadline(tournament.registration_deadline) }}</strong>
    </div>
  </div>
</template>

<style scoped>
.poster {
  width: 100%;
  color: #eaf0ff;
  background:
    radial-gradient(700px 320px at 12% -8%, rgba(255, 90, 60, 0.28), transparent 60%),
    radial-gradient(700px 340px at 92% 4%, rgba(43, 108, 255, 0.32), transparent 58%),
    linear-gradient(180deg, #0a0e27, #10152f);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.5);
}

/* Hero */
.poster-hero {
  position: relative;
  padding: 1.8rem 1.5rem 1.5rem;
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
.hero-desc { position: relative; margin: 0.35rem 0 0; color: rgba(234, 240, 255, 0.82); font-size: 0.9rem; }

.poster-empty { padding: 2.5rem 1.5rem; text-align: center; color: #9aa6d4; }

.poster-body {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 1.1rem;
  padding: 1.4rem 1.35rem;
}
@media (max-width: 680px) { .poster-body { grid-template-columns: 1fr; } }

.col-title {
  display: flex; align-items: center; gap: 0.55rem;
  font-size: 1.15rem; font-weight: 800; margin: 0 0 0.9rem;
  letter-spacing: 0.03em;
}
.col-title .bar { width: 5px; height: 20px; border-radius: 3px; background: linear-gradient(180deg, #5ad1ff, #2b6cff); }
.col-title .bar.gold { background: linear-gradient(180deg, #ffd66b, #ff9500); }

/* Rules */
.rule {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(120, 160, 255, 0.16);
  border-radius: 12px;
  padding: 0.7rem 0.85rem;
  margin-bottom: 0.7rem;
}
.rule-head { font-weight: 700; margin-bottom: 0.35rem; display: flex; align-items: center; gap: 0.45rem; color: #cfe0ff; }
.rule-icon { font-size: 1.05rem; }
.rule-list { margin: 0; padding-left: 1.1rem; line-height: 1.7; font-size: 0.88rem; color: rgba(234, 240, 255, 0.9); }

/* Rewards */
.reward {
  display: flex; align-items: center; gap: 0.8rem;
  border-radius: 12px;
  padding: 0.75rem 0.9rem;
  margin-bottom: 0.7rem;
  border: 1px solid transparent;
}
.reward-medal { font-size: 1.7rem; flex: none; filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.4)); }
.reward-label { font-weight: 800; font-size: 1.05rem; margin-bottom: 0.1rem; }
.reward-text { margin: 0; font-size: 0.85rem; color: rgba(255, 255, 255, 0.9); line-height: 1.5; }
.reward.gold { background: linear-gradient(120deg, rgba(255, 196, 77, 0.22), rgba(255, 149, 0, 0.08)); border-color: rgba(255, 196, 77, 0.5); }
.reward.gold .reward-label { color: #ffd479; }
.reward.silver { background: linear-gradient(120deg, rgba(210, 224, 255, 0.2), rgba(160, 180, 220, 0.06)); border-color: rgba(210, 224, 255, 0.45); }
.reward.silver .reward-label { color: #dfe9ff; }
.reward.bronze { background: linear-gradient(120deg, rgba(255, 138, 76, 0.2), rgba(200, 90, 40, 0.06)); border-color: rgba(255, 138, 76, 0.45); }
.reward.bronze .reward-label { color: #ffb083; }
.reward.purple { background: linear-gradient(120deg, rgba(160, 120, 255, 0.22), rgba(120, 80, 220, 0.06)); border-color: rgba(160, 120, 255, 0.45); }
.reward.purple .reward-label { color: #c9b3ff; }

.reward-other {
  display: flex; align-items: center; gap: 0.6rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px dashed rgba(120, 160, 255, 0.35);
  border-radius: 12px;
  padding: 0.65rem 0.85rem;
  font-size: 0.85rem;
  color: rgba(234, 240, 255, 0.9);
}
.reward-other p { margin: 0.1rem 0; }
.gift { font-size: 1.3rem; }

/* Footer */
.poster-footer {
  display: flex; align-items: center; justify-content: center; gap: 0.7rem;
  padding: 0.9rem 1rem;
  background: rgba(0, 0, 0, 0.28);
  border-top: 1px solid rgba(120, 160, 255, 0.18);
}
.foot-clock { color: #9aa6d4; font-size: 0.9rem; }
.foot-deadline { color: #ffd479; font-size: 1.05rem; letter-spacing: 0.03em; }
</style>
