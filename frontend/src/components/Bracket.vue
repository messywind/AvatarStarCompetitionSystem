<script setup>
import { computed } from 'vue'

const props = defineProps({
  rounds: { type: Array, default: () => [] }, // [{name, matches:[{team1,team2,winner}]}]
  teamMap: { type: Object, default: () => ({}) }, // { id: name }
})

function label(id) {
  if (id === null || id === undefined) return null
  return props.teamMap[id] || `#${id}`
}

// The champion is the winner of the final (last) round when it has a single match.
const champion = computed(() => {
  const last = props.rounds[props.rounds.length - 1]
  if (last && last.matches.length === 1 && last.matches[0].winner != null) {
    return label(last.matches[0].winner)
  }
  return null
})
</script>

<template>
  <div v-if="rounds.length" class="bracket-scroll">
    <div class="bracket">
      <div v-for="(round, ri) in rounds" :key="ri" class="round" :class="{ 'has-conn': ri > 0 }">
        <div class="round-title">{{ round.name }}</div>
        <div class="round-body">
          <div v-for="(m, mi) in round.matches" :key="mi" class="match-slot">
            <div class="match">
              <div
                class="team"
                :class="{ win: m.winner != null && m.winner === m.team1, empty: m.team1 == null }"
              >
                <span class="seed">1</span>
                <span class="team-name">{{ label(m.team1) || '待定' }}</span>
                <span v-if="m.winner != null && m.winner === m.team1" class="win-mark">✓</span>
              </div>
              <div
                class="team"
                :class="{ win: m.winner != null && m.winner === m.team2, empty: m.team2 == null }"
              >
                <span class="seed">2</span>
                <span class="team-name">{{ label(m.team2) || '待定' }}</span>
                <span v-if="m.winner != null && m.winner === m.team2" class="win-mark">✓</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Champion column -->
      <div v-if="champion" class="round champion-col">
        <div class="round-title">冠军</div>
        <div class="round-body">
          <div class="match-slot">
            <div class="champion">
              <span class="trophy">🏆</span>
              <span class="champ-name">{{ champion }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <p v-else class="muted">对阵图尚未配置。</p>
</template>

<style scoped>
.bracket-scroll { overflow-x: auto; padding: 0.5rem 0.25rem 1rem; }
.bracket {
  display: flex;
  align-items: stretch;
  min-height: 240px;
  gap: 46px; /* horizontal gutter that connectors span */
}

.round {
  display: flex;
  flex-direction: column;
  min-width: 190px;
}
.round-title {
  text-align: center;
  font-weight: 600;
  font-size: 0.82rem;
  letter-spacing: 0.06em;
  color: var(--muted);
  text-transform: uppercase;
  padding-bottom: 0.9rem;
}
.round-body {
  flex: 1;
  display: flex;
  flex-direction: column;
}
/* Each match occupies an equal-height slot so connectors line up across rounds. */
.match-slot {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
}

.match {
  border: 1px solid var(--border-strong);
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  box-shadow: var(--shadow-sm);
}
.team {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.5rem 0.7rem;
  font-size: 0.9rem;
}
.team + .team { border-top: 1px solid var(--border); }
.seed {
  flex: none;
  width: 18px; height: 18px;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 0.68rem; font-weight: 700;
  color: var(--muted);
  background: var(--bg-2);
  border-radius: 5px;
}
.team-name { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.team.empty .team-name { color: var(--muted); font-style: italic; }
.team.win { background: linear-gradient(90deg, rgba(255, 149, 0, 0.14), rgba(255, 149, 0, 0.02)); }
.team.win .team-name { font-weight: 700; color: #b8560a; }
.team.win .seed { background: var(--accent-2); color: #fff; }
.win-mark { color: var(--accent); font-weight: 800; font-size: 0.8rem; }

/* ---- Connectors: one "]" bracket per match in rounds after the first ---- */
.round.has-conn .match-slot::before {
  content: '';
  position: absolute;
  left: -46px;              /* reach back across the gutter to previous round */
  width: 23px;             /* half-gutter: horizontals stop at the vertical bar */
  top: 25%;
  height: 50%;             /* spans from upper feeder center to lower feeder center */
  border: 2px solid var(--border-strong);
  border-left: none;
  border-top-right-radius: 6px;
  border-bottom-right-radius: 6px;
}
/* short stub from the vertical bar into this match box */
.round.has-conn .match-slot::after {
  content: '';
  position: absolute;
  left: -23px;
  width: 23px;
  top: 50%;
  height: 2px;
  background: var(--border-strong);
}

/* Champion */
.champion-col { min-width: 170px; justify-content: center; }
.champion {
  display: flex; flex-direction: column; align-items: center; gap: 0.4rem;
  padding: 1.1rem 1rem;
  border-radius: 14px;
  background: linear-gradient(135deg, #fff5e0, #ffe6b8);
  border: 1px solid var(--accent-2);
  box-shadow: 0 8px 26px rgba(255, 149, 0, 0.25);
}
.trophy { font-size: 1.8rem; }
.champ-name { font-weight: 800; color: #b8560a; text-align: center; }
</style>
