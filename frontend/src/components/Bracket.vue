<script setup>
const props = defineProps({
  rounds: { type: Array, default: () => [] }, // [{name, matches:[{team1,team2,winner}]}]
  teamMap: { type: Object, default: () => ({}) }, // { id: name }
})

function label(id) {
  if (id === null || id === undefined) return null
  return props.teamMap[id] || `#${id}`
}
</script>

<template>
  <div v-if="rounds.length" class="bracket">
    <div v-for="(round, ri) in rounds" :key="ri" class="round">
      <div class="round-title">{{ round.name }}</div>
      <div class="matches">
        <div v-for="(m, mi) in round.matches" :key="mi" class="match">
          <div
            class="slot"
            :class="{ winner: m.winner != null && m.winner === m.team1, empty: m.team1 == null }"
          >
            <span class="slot-name">{{ label(m.team1) || '待定' }}</span>
            <span v-if="m.winner != null && m.winner === m.team1" class="crown">▲</span>
          </div>
          <div
            class="slot"
            :class="{ winner: m.winner != null && m.winner === m.team2, empty: m.team2 == null }"
          >
            <span class="slot-name">{{ label(m.team2) || '待定' }}</span>
            <span v-if="m.winner != null && m.winner === m.team2" class="crown">▲</span>
          </div>
        </div>
      </div>
    </div>
  </div>
  <p v-else class="muted">对阵图尚未配置。</p>
</template>

<style scoped>
.bracket {
  display: flex;
  gap: 2.5rem;
  overflow-x: auto;
  padding: 0.5rem 0.25rem 1rem;
}
.round { display: flex; flex-direction: column; min-width: 190px; }
.round-title {
  text-align: center;
  font-weight: 800;
  color: var(--primary-2);
  letter-spacing: 1px;
  margin-bottom: 1rem;
}
.matches {
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  flex: 1;
  gap: 1.2rem;
}
.match {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  position: relative;
}
/* connector line to the next round */
.round:not(:last-child) .match::after {
  content: '';
  position: absolute;
  top: 50%;
  right: -2.5rem;
  width: 2.5rem;
  height: 2px;
  background: var(--border);
}
.slot {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 0.7rem;
  font-size: 0.88rem;
  border-bottom: 1px solid var(--border);
}
.slot:last-child { border-bottom: none; }
.slot.empty .slot-name { color: var(--muted); font-style: italic; }
.slot.winner {
  background: linear-gradient(90deg, rgba(255, 176, 58, 0.18), transparent);
  color: var(--accent-2);
  font-weight: 800;
}
.slot-name { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.crown { color: var(--accent-2); font-size: 0.7rem; }
</style>
