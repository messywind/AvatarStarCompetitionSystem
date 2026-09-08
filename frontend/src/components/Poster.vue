<script setup>
import { computed } from 'vue'
import { formatDeadline } from '../time'
import logo from '../assets/logo.png'
import bgBattle from '../assets/game/flag.webp'
import Icon from './Icon.vue'
import gold from '../assets/game/rank-gold.webp'
import silver from '../assets/game/rank-silver.webp'
import bronze from '../assets/game/rank-bronze.webp'
import './poster.css'

const props = defineProps({
  tournament: { type: Object, required: true },
})

const poster = computed(() => props.tournament?.poster || {})

const lines = (text) => (text || '').split(/\r?\n/).map((s) => s.trim()).filter(Boolean)

const rules = computed(() =>
  [
    { icon: 'flag', label: '比赛形式', key: 'format' },
    { icon: 'shield', label: '职业限制', key: 'profession_limit' },
    { icon: 'grid', label: '模式限制', key: 'mode_limit' },
    { icon: 'shield', label: '药物及道具限制', key: 'item_limit' },
    { icon: 'users', label: '装备限制', key: 'equipment_limit' },
    { icon: 'star', label: '其他限制', key: 'other_limit' },
  ]
    .map((r) => ({ ...r, items: lines(poster.value[r.key]) }))
    .filter((r) => r.items.length)
)

const rewards = computed(() =>
  [
    { icon: gold, label: '冠军', key: 'reward_champion', tier: 'gold' },
    { icon: silver, label: '亚军', key: 'reward_runner_up', tier: 'silver' },
    { icon: bronze, label: '季军', key: 'reward_third', tier: 'bronze' },
    { icon: null, label: '殿军', key: 'reward_fourth', tier: 'purple' },
  ]
    .map((r) => ({ ...r, items: lines(poster.value[r.key]) }))
    .filter((r) => r.items.length)
)

const rewardOther = computed(() => lines(poster.value.reward_other))

const isEmpty = computed(() => !rules.value.length && !rewards.value.length && !rewardOther.value.length)
</script>

<template>
  <div class="poster competition-poster">
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
        <h2 class="col-title">参赛规则</h2>
        <div v-for="r in rules" :key="r.key" class="rule">
          <div class="rule-head"><Icon :name="r.icon" :size="17" class="rule-icon" />{{ r.label }}</div>
          <ul class="rule-list">
            <li v-for="(line, i) in r.items" :key="i">{{ line }}</li>
          </ul>
        </div>
      </section>

      <!-- Rewards -->
      <section v-if="rewards.length || rewardOther.length" class="col rewards-col">
        <h2 class="col-title">官方奖励</h2>
        <div v-for="r in rewards" :key="r.key" class="reward" :class="r.tier">
          <img v-if="r.icon" :src="r.icon" :alt="r.label" class="reward-medal" /><Icon v-else name="shield" :size="28" class="reward-medal" />
          <div class="reward-body">
            <div class="reward-label">{{ r.label }}</div>
            <p v-for="(line, i) in r.items" :key="i" class="reward-text">{{ line }}</p>
          </div>
        </div>
        <div v-if="rewardOther.length" class="reward-other">
          <Icon name="star" :size="22" class="gift" />
          <div>
            <p v-for="(line, i) in rewardOther" :key="i">{{ line }}</p>
          </div>
        </div>
      </section>
    </div>

    <!-- Footer -->
    <div class="poster-footer">
      <span class="foot-clock"><Icon name="clock" :size="16" />报名截止时间</span>
      <strong class="foot-deadline">{{ formatDeadline(tournament.registration_deadline) }}</strong>
    </div>
  </div>
</template>

<style scoped>
.poster-body { display: grid; grid-template-columns: 1.1fr 1fr; gap: 2rem; padding: 2rem; }
.col-title { font-size: 1.15rem; margin: 0 0 1.2rem; padding-bottom: .8rem; border-bottom: 1px solid var(--border); }
.rule { margin-bottom: 1.2rem; }
.rule-head { display: flex; align-items: center; gap: .5rem; font-size: .87rem; font-weight: 650; margin-bottom: .5rem; }
.rule-icon { color: var(--primary); }
.rule-list { margin: 0; padding-left: 1.2rem; line-height: 1.8; color: var(--muted); font-size: .8rem; overflow-wrap: anywhere; }
.reward { display: flex; align-items: flex-start; gap: .8rem; border-radius: 7px; padding: 1rem; margin-bottom: .8rem; background: #edf1f5; }
.reward-medal { width: 36px; height: 30px; object-fit: contain; flex: none; margin-top: .1rem; color: #64748b; }
.reward-body { min-width: 0; }
.reward-label { font-weight: 750; font-size: .95rem; margin-bottom: .35rem; }
.reward-text { margin: 0; font-size: .78rem; color: #536173; line-height: 1.8; overflow-wrap: anywhere; }
.reward.gold { background: #fff1d8; }
.reward.gold .reward-label { color: #88530e; }
.reward.bronze { background: #f7eae0; }
.reward.purple { background: #eeebf6; }
.reward-other { display: flex; gap: .65rem; padding: .5rem .2rem; font-size: .79rem; color: var(--muted); }
.reward-other p { margin: 0; }
.gift { color: var(--primary); }
.poster-footer { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: .5rem; padding: 1rem 2rem; background: #edf1f5; border-top: 1px solid var(--border); }
.foot-clock { display: flex; align-items: center; gap: .5rem; font-size: .78rem; color: var(--muted); }
.foot-deadline { font-size: .87rem; color: var(--primary); }
@media(max-width:650px) { .poster-body { grid-template-columns: 1fr; padding: 1.5rem; gap: 1rem; } .poster-footer { padding: 1rem 1.5rem; } }
</style>
