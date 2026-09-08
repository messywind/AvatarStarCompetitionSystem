<script setup>
import Icon from './Icon.vue'
import gold from '../assets/game/rank-gold.webp'
import silver from '../assets/game/rank-silver.webp'
import bronze from '../assets/game/rank-bronze.webp'
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
    { title: '冠军', icon: gold, cls: 'gold', id: winnerFinal?.winner ?? null },
    { title: '亚军', icon: silver, cls: 'silver', id: loserOf(winnerFinal) },
    { title: '季军', icon: bronze, cls: 'bronze', id: loserOf(loserFinal) },
    { title: '殿军', icon: null, cls: 'fourth', id: loserOf(semi2) },
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
                  <Icon name="trophy" :size="38" class="trophy" />
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
                <img v-if="p.icon" :src="p.icon" :alt="p.title" class="podium-icon" /><Icon v-else name="shield" class="podium-icon" :size="24" />
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
  <div v-else class="bracket-empty"><Icon name="flag" :size="32" /><h3>对阵即将揭晓</h3><p>赛程配置完成后，将在这里展示每轮对局与晋级结果。</p></div>
</template>

<style scoped>
.stages { display: flex; flex-direction: column; gap: 2.3rem; }
.stage-head { margin-bottom: 1rem; }
.stage-name { margin: 0; font-size: 1.02rem; font-weight: 750; }
.stage-note { margin: .4rem 0 0; font-size: .78rem; color: var(--muted); max-width: 75ch; }
.bracket-scroll { overflow-x: auto; padding: .7rem 0 1.4rem; -webkit-overflow-scrolling: touch; }
.bracket { display: flex; align-items: stretch; min-height: 260px; gap: 46px; }
.round { display: flex; flex-direction: column; width: 210px; flex: none; }
.round-title { text-align: center; font-weight: 650; font-size: .78rem; color: #51677a; padding: .65rem .5rem; background: #eaf0f5; border-radius: 5px; margin-bottom: 1rem; }
.round-body { flex: 1; display: flex; flex-direction: column; }
.match-slot { flex: 1; display: flex; flex-direction: column; justify-content: center; position: relative; padding: .35rem 0; }
.match { border: 1px solid #ccd6df; border-radius: 7px; overflow: hidden; background: #fff; transition: border-color .18s; }
.match:hover { border-color: #899eaf; }
.team { display: flex; align-items: center; gap: .55rem; padding: .7rem .8rem; min-height: 44px; font-size: .83rem; }
.team + .team { border-top: 1px solid var(--border); }
.seed { width: 19px; height: 19px; display: inline-flex; align-items: center; justify-content: center; font-size: .65rem; font-weight: 650; color: #617589; background: #edf1f5; border-radius: 3px; flex: none; }
.team-name { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.team.empty .team-name { color: #687583; }
.team.win { background: #fff0e4; }
.team.win .team-name { font-weight: 750; color: #9d4018; }
.team.win .seed { background: #e3b48f; color: #53280f; }
.win-mark { color: var(--primary); font-weight: 750; }
.score { min-width: 23px; text-align: center; font-weight: 750; font-size: .82rem; color: #4f6377; background: #eaf0f5; border-radius: 4px; padding: .1rem .3rem; font-variant-numeric: tabular-nums; flex: none; }
.team.win .score { background: var(--primary); color: #fff; }
.round.has-conn .match-slot::before { content: ''; position: absolute; left: -46px; width: 23px; top: 25%; height: 50%; border: 1px solid #aebdca; border-left: none; border-radius: 0 4px 4px 0; }
.round.has-conn .match-slot::after { content: ''; position: absolute; left: -23px; width: 23px; top: 50%; height: 1px; background: #aebdca; }
.champion-col { width: 175px; }
.champion { display: flex; flex-direction: column; align-items: center; gap: .8rem; padding: 1.6rem 1rem; border-radius: 8px; background: var(--dark); color: #ffd093; }
.champion .trophy { color: #ffb969; }
.champ-name { font-weight: 750; text-align: center; font-size: .93rem; overflow-wrap: anywhere; }
.flow { display: flex; align-items: flex-start; gap: 24px; }
.flow-round { width: 220px; flex: none; }
.round-note { margin: -.4rem 0 .85rem; text-align: center; font-size: .72rem; line-height: 1.6; color: var(--muted); }
.flow-matches { display: flex; flex-direction: column; gap: .75rem; }
.podium-col { width: 230px; }
.podium { display: flex; flex-direction: column; gap: .7rem; }
.podium-card { display: flex; align-items: center; gap: .55rem; padding: .7rem .8rem; border-radius: 6px; background: #edf1f5; }
.podium-icon { width: 32px; height: 26px; object-fit: contain; color: #667a8b; flex: none; }
.podium-title { flex: none; font-size: .7rem; font-weight: 650; color: var(--muted); }
.podium-name { flex: 1; min-width: 0; font-weight: 700; font-size: .8rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: right; }
.podium-name.tbd { color: var(--muted); font-weight: 400; }
.podium-card.gold { background: #fff0d9; }
.podium-card.gold .podium-name { color: #8c5209; }
.podium-card.bronze { background: #f4e8df; }
.standings { margin-top: .7rem; border: 1px solid var(--border); border-radius: 8px; overflow-x: auto; background: #fff; }
.standings-title { padding: .8rem 1rem; font-size: .86rem; font-weight: 750; color: #3e556b; background: #eaf0f5; }
.standings table { font-size: .8rem; min-width: 440px; }
.standings th, .standings td { padding: .7rem 1rem; }
.rank-col { width: 65px; text-align: center; }
.num-col { width: 80px; text-align: center; white-space: nowrap; font-variant-numeric: tabular-nums; }
.adv-col { width: 75px; }
.rank-badge { display: inline-grid; place-items: center; width: 24px; height: 24px; border-radius: 4px; background: #edf1f5; color: #617589; font-size: .73rem; font-weight: 650; }
.advancing { background: #f3faf6; }
.advancing .rank-badge { background: #dbefdf; color: var(--success); }
.standing-name { font-weight: 600; }
.points { font-weight: 750; }
.adv-chip { font-size: .68rem; padding: .2rem .4rem; background: #e0f1e5; color: var(--success); border-radius: 4px; }
.bracket-empty { text-align: center; padding: 2rem 1rem; color: #63798c; }
.bracket-empty h3 { margin: .8rem 0 .5rem; font-size: 1rem; }
.bracket-empty p { font-size: .8rem; color: var(--muted); margin: 0; }
@media(max-width:720px) { .round { width: 185px; } .flow-round { width: 195px; } .bracket { gap: 30px; } .flow { gap: 18px; } .round.has-conn .match-slot::before { left: -30px; width: 15px; } .round.has-conn .match-slot::after { left: -15px; width: 15px; } .team { padding: .6rem; } .standings th,.standings td { padding: .65rem .6rem; } .podium-col { width: 220px; } }
</style>
