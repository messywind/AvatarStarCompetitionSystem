<script setup>
const props = defineProps({
  // [{name, type, note, advance, rounds:[{name, note, matches:[{team1,team2,winner,score1,score2}]}]}]
  stages: { type: Array, default: () => [] },
  teamMap: { type: Object, default: () => ({}) }, // { id: name }
})

function label(id) {
  if (id === null || id === undefined) return null
  return props.teamMap[id] || `#${id}`
}

function hasScore(m) {
  return m.score1 != null || m.score2 != null
}

// The champion of an elimination tree is the winner of its final (single-match) round.
function stageChampion(stage) {
  const rounds = stage.rounds || []
  const last = rounds[rounds.length - 1]
  if (last && last.matches.length === 1 && last.matches[0].winner != null) {
    return label(last.matches[0].winner)
  }
  return null
}

// Swiss standings: 1 point per win, ranked by points → head-to-head → first appearance.
function standings(stage) {
  const stats = new Map()
  const decided = []
  for (const round of stage.rounds || []) {
    for (const m of round.matches || []) {
      for (const id of [m.team1, m.team2]) {
        if (id != null && !stats.has(id)) stats.set(id, { id, played: 0, wins: 0, order: stats.size })
      }
      if (m.winner == null) continue
      if (m.team1 != null) stats.get(m.team1).played++
      if (m.team2 != null) stats.get(m.team2).played++
      if (stats.has(m.winner)) stats.get(m.winner).wins++
      if (m.team1 != null && m.team2 != null) decided.push(m)
    }
  }
  const headToHead = (a, b) => {
    for (const m of decided) {
      const pair = [m.team1, m.team2]
      if (pair.includes(a.id) && pair.includes(b.id)) return m.winner === a.id ? -1 : 1
    }
    return 0
  }
  return [...stats.values()].sort(
    (a, b) => b.wins - a.wins || headToHead(a, b) || a.order - b.order
  )
}

function loserOf(m) {
  if (!m || m.winner == null) return null
  return m.winner === m.team1 ? m.team2 : m.team1
}

// double_final rounds are expected in order: 半决赛(1v2, 3v4) → 败者组决赛 → 胜者组决赛.
function podium(stage) {
  const rounds = stage.rounds || []
  const winnerFinal = rounds[rounds.length - 1]?.matches?.[0]
  const loserFinal = rounds[rounds.length - 2]?.matches?.[0]
  const semi2 = rounds[0]?.matches?.[1]
  return [
    { title: '冠军', icon: '🏆', cls: 'gold', id: winnerFinal?.winner ?? null },
    { title: '亚军', icon: '🥈', cls: 'silver', id: loserOf(winnerFinal) },
    { title: '季军', icon: '🥉', cls: 'bronze', id: loserOf(loserFinal) },
    { title: '殿军', icon: '🎖️', cls: 'fourth', id: loserOf(semi2) },
  ]
}
</script>

<template>
  <div v-if="stages.length" class="stages">
    <section v-for="(stage, si) in stages" :key="si" class="stage" :style="{ '--si': si }">
      <header class="stage-head">
        <h4 class="stage-name">{{ stage.name }}</h4>
        <p v-if="stage.note" class="stage-note">{{ stage.note }}</p>
      </header>

      <!-- ===== elimination: classic tree with connectors ===== -->
      <div v-if="stage.type === 'elimination'" class="bracket-scroll">
        <div class="bracket">
          <div
            v-for="(round, ri) in stage.rounds"
            :key="ri"
            class="round"
            :class="{ 'has-conn': ri > 0 }"
          >
            <div class="round-title">{{ round.name }}</div>
            <div class="round-body">
              <div v-for="(m, mi) in round.matches" :key="mi" class="match-slot">
                <div class="match">
                  <div
                    v-for="side in [1, 2]"
                    :key="side"
                    class="team"
                    :class="{
                      win: m.winner != null && m.winner === m[`team${side}`],
                      empty: m[`team${side}`] == null,
                    }"
                  >
                    <span class="seed">{{ side }}</span>
                    <span class="team-name">{{ label(m[`team${side}`]) || '待定' }}</span>
                    <span v-if="hasScore(m)" class="score">{{ m[`score${side}`] ?? 0 }}</span>
                    <span
                      v-else-if="m.winner != null && m.winner === m[`team${side}`]"
                      class="win-mark"
                      >✓</span
                    >
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="stageChampion(stage)" class="round champion-col">
            <div class="round-title">冠军</div>
            <div class="round-body">
              <div class="match-slot">
                <div class="champion">
                  <span class="trophy">🏆</span>
                  <span class="champ-name">{{ stageChampion(stage) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== pairs / swiss / double_final: flow columns without connectors ===== -->
      <div v-else class="bracket-scroll">
        <div class="flow">
          <div v-for="(round, ri) in stage.rounds" :key="ri" class="flow-round">
            <div class="round-title">{{ round.name }}</div>
            <p v-if="round.note" class="round-note">{{ round.note }}</p>
            <div class="flow-matches">
              <div v-for="(m, mi) in round.matches" :key="mi" class="match">
                <div
                  v-for="side in [1, 2]"
                  :key="side"
                  class="team"
                  :class="{
                    win: m.winner != null && m.winner === m[`team${side}`],
                    empty: m[`team${side}`] == null,
                  }"
                >
                  <span class="team-name">{{ label(m[`team${side}`]) || '待定' }}</span>
                  <span v-if="hasScore(m)" class="score">{{ m[`score${side}`] ?? 0 }}</span>
                  <span
                    v-else-if="m.winner != null && m.winner === m[`team${side}`]"
                    class="win-mark"
                    >✓</span
                  >
                </div>
              </div>
            </div>
          </div>

          <!-- Final placements for the 4-team double-elimination final -->
          <div v-if="stage.type === 'double_final'" class="flow-round podium-col">
            <div class="round-title">最终名次</div>
            <div class="podium">
              <div v-for="p in podium(stage)" :key="p.title" class="podium-card" :class="p.cls">
                <span class="podium-icon">{{ p.icon }}</span>
                <span class="podium-title">{{ p.title }}</span>
                <span class="podium-name" :class="{ tbd: p.id == null }">{{
                  label(p.id) || '待定'
                }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== swiss standings table ===== -->
      <div v-if="stage.type === 'swiss'" class="standings">
        <div class="standings-title">积分榜</div>
        <table v-if="standings(stage).length">
          <thead>
            <tr>
              <th class="rank-col">排名</th>
              <th>队伍</th>
              <th class="num-col">胜场</th>
              <th class="num-col">积分</th>
              <th class="adv-col"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, idx) in standings(stage)"
              :key="row.id"
              :class="{ advancing: stage.advance && idx < stage.advance }"
            >
              <td class="rank-col">
                <span class="rank-badge">{{ idx + 1 }}</span>
              </td>
              <td class="standing-name">{{ label(row.id) }}</td>
              <td class="num-col">{{ row.wins }} / {{ row.played }}</td>
              <td class="num-col points">{{ row.wins }}</td>
              <td class="adv-col">
                <span v-if="stage.advance && idx < stage.advance" class="adv-chip">晋级</span>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-else class="muted">对局尚未填入队伍。</p>
      </div>
    </section>
  </div>
  <p v-else class="muted">对阵图尚未配置。</p>
</template>

<style scoped>
.stages {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}
.stage {
  animation: round-in 0.34s var(--ease-soft) both;
  animation-delay: calc(var(--si, 0) * 70ms);
}
.stage-head {
  margin-bottom: 0.7rem;
}
.stage-name {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}
.stage-note {
  margin: 0.3rem 0 0;
  font-size: 0.8rem;
  color: var(--muted);
}

.bracket-scroll {
  overflow-x: auto;
  padding: 0.5rem 0.25rem 1rem;
  -webkit-overflow-scrolling: touch;
  scroll-snap-type: x proximity;
}
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
  scroll-snap-align: start;
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
  transition: transform 0.18s var(--ease-out), box-shadow 0.18s var(--ease-out), border-color 0.18s var(--ease-out);
}
.match:hover {
  transform: translateY(-2px);
  border-color: rgba(0, 113, 227, 0.22);
  box-shadow: var(--shadow-md);
}
.team {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.5rem 0.7rem;
  font-size: 0.9rem;
  transition: background 0.2s var(--ease-out), color 0.2s var(--ease-out);
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
.score {
  flex: none;
  min-width: 22px;
  text-align: center;
  font-weight: 700;
  font-size: 0.8rem;
  color: var(--muted);
  background: var(--bg-2);
  border-radius: 6px;
  padding: 0.1rem 0.3rem;
}
.team.win .score { background: var(--accent-2); color: #fff; }

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
  animation: champion-in 0.38s var(--ease-soft) both;
}
.trophy { font-size: 1.8rem; }
.champ-name { font-weight: 800; color: #b8560a; text-align: center; }

/* ---- Flow layout (pairs / swiss rounds / double_final) ---- */
.flow {
  display: flex;
  align-items: flex-start;
  gap: 26px;
}
.flow-round {
  min-width: 190px;
  scroll-snap-align: start;
}
.flow-round .round-title {
  padding-bottom: 0.35rem;
}
.round-note {
  margin: 0 0 0.7rem;
  text-align: center;
  font-size: 0.72rem;
  line-height: 1.5;
  color: var(--muted);
}
.flow-matches {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

/* ---- Podium (double_final placements) ---- */
.podium-col { min-width: 180px; }
.podium {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.podium-card {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.55rem 0.8rem;
  border-radius: 11px;
  border: 1px solid var(--border-strong);
  background: #fff;
  box-shadow: var(--shadow-sm);
}
.podium-icon { font-size: 1.15rem; }
.podium-title {
  flex: none;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--muted);
  letter-spacing: 0.08em;
}
.podium-name {
  flex: 1;
  font-weight: 700;
  font-size: 0.88rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
}
.podium-name.tbd { color: var(--muted); font-weight: 500; font-style: italic; }
.podium-card.gold {
  background: linear-gradient(135deg, #fff5e0, #ffe6b8);
  border-color: var(--accent-2);
}
.podium-card.gold .podium-name { color: #b8560a; }
.podium-card.silver { background: linear-gradient(135deg, #f7f8fa, #ebedf1); }
.podium-card.bronze { background: linear-gradient(135deg, #fbf1e8, #f4e0cd); }

/* ---- Swiss standings ---- */
.standings {
  margin-top: 0.4rem;
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
}
.standings-title {
  padding: 0.6rem 0.9rem;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--muted);
  text-transform: uppercase;
  background: var(--bg-2);
  border-bottom: 1px solid var(--border);
}
.standings table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}
.standings th {
  text-align: left;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--muted);
  padding: 0.5rem 0.9rem;
  border-bottom: 1px solid var(--border);
}
.standings td {
  padding: 0.55rem 0.9rem;
  border-bottom: 1px solid var(--border);
}
.standings tbody tr:last-child td { border-bottom: none; }
.standings tbody tr {
  transition: background 0.18s var(--ease-out);
}
.standings tbody tr.advancing {
  background: linear-gradient(90deg, rgba(255, 149, 0, 0.09), rgba(255, 149, 0, 0.015));
}
.rank-col { width: 52px; }
.num-col { width: 70px; text-align: center; }
.adv-col { width: 60px; text-align: right; }
.standings td.num-col { color: var(--muted); }
.standings td.points { font-weight: 700; color: inherit; }
.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px; height: 22px;
  border-radius: 7px;
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--muted);
  background: var(--bg-2);
}
tr.advancing .rank-badge { background: var(--accent-2); color: #fff; }
tr.advancing .standing-name { font-weight: 700; }
.adv-chip {
  display: inline-block;
  padding: 0.14rem 0.5rem;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 700;
  color: #b8560a;
  background: rgba(255, 149, 0, 0.16);
}
.standings .muted { padding: 0.8rem 0.9rem; margin: 0; }

@keyframes round-in {
  from {
    opacity: 0;
    transform: translateX(12px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@keyframes champion-in {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@media (max-width: 720px) {
  .bracket-scroll {
    padding-bottom: 1.1rem;
  }
  .bracket {
    gap: 30px;
    min-height: 220px;
  }
  .round,
  .flow-round {
    min-width: 168px;
  }
  .round-title {
    padding-bottom: 0.65rem;
  }
  .flow-round .round-title {
    padding-bottom: 0.35rem;
  }
  .flow {
    gap: 18px;
  }
  .team {
    min-height: 40px;
    padding: 0.5rem 0.6rem;
  }
  .round.has-conn .match-slot::before {
    left: -30px;
    width: 15px;
  }
  .round.has-conn .match-slot::after {
    left: -15px;
    width: 15px;
  }
}

@media (hover: none) {
  .match:hover {
    transform: none;
    box-shadow: var(--shadow-sm);
  }
}

@media (prefers-reduced-motion: reduce) {
  .stage,
  .champion {
    animation: none;
  }
}
</style>
