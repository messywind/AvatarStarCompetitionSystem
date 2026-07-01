<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '../api'
import { toast } from '../toast'
import { PROFESSIONS } from '../roster'
import Bracket from '../components/Bracket.vue'

const teams = ref([])
const rounds = ref([])
const teamMap = ref({})
const loading = ref(true)
const activeTeam = ref(null)

async function load() {
  loading.value = true
  try {
    const [teamsRes, bracketRes] = await Promise.all([
      api.get('/public/teams'),
      api.get('/public/bracket'),
    ])
    teams.value = teamsRes.data
    rounds.value = bracketRes.data.bracket.rounds || []
    teamMap.value = bracketRes.data.teams || {}
  } catch (e) {
    toast(e.message || '加载失败', 'error')
  } finally {
    loading.value = false
  }
}

function formal(players) {
  return players.filter((p) => !p.is_substitute)
}
function subs(players) {
  return players.filter((p) => p.is_substitute)
}

onMounted(load)
</script>

<template>
  <div class="container">
    <h1>赛事浏览</h1>
    <p class="muted">展示所有通过审核的参赛战队与晋级对阵。</p>

    <!-- Bracket -->
    <section class="panel bracket-panel">
      <h2>赛事对阵图</h2>
      <Bracket :rounds="rounds" :team-map="teamMap" />
    </section>

    <!-- Teams -->
    <h2 class="teams-title">参赛战队 <span class="muted">（{{ teams.length }} 支）</span></h2>
    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="!teams.length" class="muted">暂无通过审核的战队。</p>

    <div class="team-grid">
      <div v-for="t in teams" :key="t.id" class="card team-card" @click="activeTeam = t">
        <div class="row">
          <h3 style="margin: 0">{{ t.name }}</h3>
          <span class="spacer"></span>
          <span class="muted small">队长 {{ t.captain }}</span>
        </div>
        <p v-if="t.declaration" class="declaration">「{{ t.declaration }}」</p>
        <div class="players">
          <span v-for="p in formal(t.players)" :key="p.id" class="chip">
            <span class="dot" :style="{ background: `var(--prof-${p.profession})` }"></span>
            {{ p.nickname }}
          </span>
        </div>
        <p v-if="subs(t.players).length" class="muted small">替补 {{ subs(t.players).length }} 人</p>
      </div>
    </div>

    <!-- Detail modal -->
    <div v-if="activeTeam" class="modal-backdrop" @click.self="activeTeam = null">
      <div class="modal">
        <div class="row">
          <h2 style="margin: 0">{{ activeTeam.name }}</h2>
          <span class="spacer"></span>
          <button class="btn ghost sm" @click="activeTeam = null">关闭</button>
        </div>
        <p class="muted">队长：{{ activeTeam.captain }}</p>
        <p v-if="activeTeam.declaration" class="declaration">「{{ activeTeam.declaration }}」</p>

        <h4>正式队员</h4>
        <div class="table-wrap">
          <table>
            <thead><tr><th>称呼</th><th>职业</th></tr></thead>
            <tbody>
              <tr v-for="p in formal(activeTeam.players)" :key="p.id">
                <td>{{ p.nickname }}</td>
                <td><span :class="'prof-' + p.profession">{{ p.profession }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>

        <template v-if="subs(activeTeam.players).length">
          <h4>替补队员</h4>
          <div class="table-wrap">
            <table>
              <thead><tr><th>称呼</th><th>职业</th></tr></thead>
              <tbody>
                <tr v-for="p in subs(activeTeam.players)" :key="p.id">
                  <td>{{ p.nickname }}</td>
                  <td><span :class="'prof-' + p.profession">{{ p.profession }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bracket-panel { margin: 1.5rem 0 2rem; }
.teams-title { margin-top: 1.5rem; }
.team-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; margin-top: 1rem; }
.team-card { cursor: pointer; transition: transform 0.12s, border-color 0.12s; }
.team-card:hover { transform: translateY(-3px); border-color: var(--primary-2); }
.declaration { color: var(--accent-2); font-style: italic; margin: 0.5rem 0; }
.players { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.5rem; }
.small { font-size: 0.8rem; }
</style>
