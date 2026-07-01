<script setup>
import { computed } from 'vue'
import { PROFESSIONS, validateRoster } from '../roster'

const props = defineProps({
  modelValue: { type: Array, required: true }, // array of players
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
  update([...players.value, { nickname: '', profession: PROFESSIONS[0], is_substitute: isSub }])
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
          <span class="dot" :style="{ background: `var(--prof-${prof})` }"></span>
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
        <input v-model="p.nickname" placeholder="选手称呼" class="pl-name" />
        <select v-model="p.profession" class="pl-prof">
          <option v-for="prof in PROFESSIONS" :key="prof" :value="prof">{{ prof }}</option>
        </select>
        <button type="button" class="btn danger sm" @click="removePlayer(p)">移除</button>
      </div>
    </div>

    <!-- Substitutes -->
    <div class="group-label sub">
      替补队员（{{ subs.length }}）· 数量不限
      <button type="button" class="btn ghost sm" @click="addPlayer(true)">+ 添加替补</button>
    </div>
    <div v-for="(p, i) in players" :key="'s' + i">
      <div v-if="p.is_substitute" class="player-row">
        <input v-model="p.nickname" placeholder="替补称呼" class="pl-name" />
        <select v-model="p.profession" class="pl-prof">
          <option v-for="prof in PROFESSIONS" :key="prof" :value="prof">{{ prof }}</option>
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
.summary {
  background: rgba(43, 108, 255, 0.1);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.8rem 1rem;
  margin-bottom: 1rem;
}
.summary-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; }
.count { font-weight: 800; color: var(--danger); }
.count.ok { color: var(--success); }
.prof-counts { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.chip.bad { border-color: var(--danger); color: var(--danger); }

.group-label {
  display: flex; align-items: center; gap: 0.6rem;
  font-weight: 700; margin: 1rem 0 0.5rem;
}
.group-label.sub { color: var(--muted); }
.group-label button { margin-left: auto; }
.empty { padding: 0.5rem 0; }

.player-row { display: flex; gap: 0.5rem; margin-bottom: 0.5rem; align-items: center; }
.pl-name { flex: 1; }
.pl-prof { width: 120px; flex: none; }

.err-list { margin: 0.8rem 0 0; padding-left: 1.1rem; color: var(--danger); font-size: 0.85rem; line-height: 1.7; }
</style>
