<script setup>
import { computed } from 'vue'
import { PROFESSIONS, MAX_SUBSTITUTES, validateRoster } from '../roster'
import { professionImage } from '../gameAssets'

const props = defineProps({
  modelValue: { type: Array, required: true }, // array of players
  professions: { type: Array, default: () => PROFESSIONS }, // 该赛事允许的职业
})
const emit = defineEmits(['update:modelValue'])

const players = computed(() => props.modelValue)

const formal = computed(() => players.value.filter((p) => !p.is_substitute))
const subs = computed(() => players.value.filter((p) => p.is_substitute))
const validation = computed(() => validateRoster(players.value))

function update(list) {
  emit('update:modelValue', list)
}

function addPlayer(isSub) {
  update([...players.value, { nickname: '', profession: props.professions[0], is_substitute: isSub }])
}

function removePlayer(target) {
  update(players.value.filter((p) => p !== target))
}
</script>

<template>
  <div class="roster">
    <!-- Live profession summary -->
    <div class="summary">
      <div class="summary-head">
        <strong>正式队员</strong>
        <span class="count" :class="{ ok: validation.formalCount === 5 }">
          {{ validation.formalCount }} / 5
        </span>
      </div>
      <div class="prof-counts">
        <span
          v-for="prof in PROFESSIONS"
          :key="prof"
          class="chip"
          :class="{ bad: validation.counts[prof] === 0 || validation.counts[prof] > 2 }"
        >
          <img :src="professionImage[prof]" alt="" class="prof-avatar" />
          {{ prof }} · {{ validation.counts[prof] }}
        </span>
      </div>
    </div>

    <!-- Formal players -->
    <div class="group-label">
      正式队员（{{ formal.length }}）
      <button type="button" class="btn sm" @click="addPlayer(false)">+ 添加正式队员</button>
    </div>
    <div v-if="!formal.length" class="muted empty">尚未添加正式队员</div>
    <div v-for="(p, i) in players" :key="'f' + i">
      <div v-if="!p.is_substitute" class="player-row">
        <span class="player-slot">{{ i + 1 }}</span>
        <input v-model="p.nickname" :aria-label="`正式队员 ${i + 1} 称呼`" placeholder="选手称呼" class="pl-name" />
        <select v-model="p.profession" :aria-label="`队员 ${i + 1} 职业`" class="pl-prof">
          <option v-for="prof in professions" :key="prof" :value="prof">{{ prof }}</option>
        </select>
        <button type="button" class="btn danger sm" @click="removePlayer(p)">移除</button>
      </div>
    </div>

    <!-- Substitutes -->
    <div class="group-label sub">
      替补队员（{{ subs.length }} / {{ MAX_SUBSTITUTES }}）· 最多 {{ MAX_SUBSTITUTES }} 人
      <button
        type="button"
        class="btn ghost sm"
        :disabled="subs.length >= MAX_SUBSTITUTES"
        @click="addPlayer(true)"
      >
        + 添加替补
      </button>
    </div>
    <div v-for="(p, i) in players" :key="'s' + i">
      <div v-if="p.is_substitute" class="player-row">
        <span class="player-slot">替</span>
        <input v-model="p.nickname" :aria-label="`替补队员 ${i + 1} 称呼`" placeholder="替补称呼" class="pl-name" />
        <select v-model="p.profession" :aria-label="`队员 ${i + 1} 职业`" class="pl-prof">
          <option v-for="prof in professions" :key="prof" :value="prof">{{ prof }}</option>
        </select>
        <button type="button" class="btn danger sm" @click="removePlayer(p)">移除</button>
      </div>
    </div>

    <!-- Errors -->
    <ul v-if="validation.errors.length" class="err-list">
      <li v-for="(e, i) in validation.errors" :key="i">{{ e }}</li>
    </ul>
    <p v-else class="success-text">✓ 阵容符合参赛规则</p>
  </div>
</template>

<style scoped>
.summary { background: #edf1f5; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
.summary-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: .8rem; font-size: .83rem; }
.count { font-weight: 750; color: var(--danger); font-variant-numeric: tabular-nums; }
.count.ok { color: var(--success); }
.prof-counts { display: flex; gap: .4rem; flex-wrap: wrap; }
.prof-counts .chip { background: #fff; border: 0; padding: .15rem .5rem .15rem .25rem; gap: .3rem; font-size: .74rem; }
.prof-avatar { width: 23px; height: 28px; object-fit: contain; }
.chip.bad { background: #ffedf0; color: var(--danger); }
.group-label { display: flex; align-items: center; flex-wrap: wrap; gap: .6rem; font-size: .82rem; font-weight: 650; margin: 1.2rem 0 .8rem; }
.group-label.sub { color: var(--muted); border-top: 1px solid var(--border); padding-top: 1.1rem; }
.group-label button { margin-left: auto; font-size: .7rem; }
.group-label .btn:not(.ghost) { background: var(--accent-soft); color: var(--primary); }
.empty { padding: .6rem 0; font-size: .8rem; }
.player-row { display: flex; align-items: center; gap: .5rem; margin-bottom: .65rem; }
.player-slot { width: 24px; color: #5d6f81; font-weight: 650; font-size: .8rem; text-align: center; flex: none; }
.pl-name { flex: 1; min-width: 0; }
.pl-prof { width: 96px; flex: none; }
.player-row .btn { background: #fff; color: var(--danger); border-color: var(--border); font-size: .72rem; padding: .4rem .55rem; }
.player-row .btn:hover { background: #ffedf0; border-color: #e7b0b7; }
.err-list { margin: 1rem 0 0; padding: .8rem .9rem .8rem 1.9rem; border-radius: 7px; color: var(--danger); background: #fff1f2; font-size: .77rem; line-height: 1.8; }
.success-text { margin: 1rem 0 0; padding: .7rem 1rem; border-radius: 7px; background: #eaf6ef; font-size: .8rem; }
@media(max-width:620px) { .summary { padding: .85rem; } .player-row { display: grid; grid-template-columns: 20px minmax(0,1fr) 78px; gap: .4rem; padding-bottom: .6rem; border-bottom: 1px solid var(--border); } .pl-prof { width: 100%; padding-left: .4rem; padding-right: .2rem; } .player-row .btn { grid-column: 2/-1; min-height: 32px; justify-self: end; } .group-label button { margin-left: auto; } .prof-counts { gap: .3rem; } }
</style>
