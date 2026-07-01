<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import api from '../api'
import { toast } from '../toast'
import { PROFESSIONS } from '../roster'
import { formatDeadline, countdown } from '../time'
import { useAuthStore } from '../stores/auth'
import Bracket from '../components/Bracket.vue'

const auth = useAuthStore()

const STATUS_LABEL = { pending: '审核中', approved: '已通过', rejected: '未通过' }

const tournaments = ref([])
const selectedTid = ref(null)
const teams = ref([])
const myTeams = ref([])
const rounds = ref([])
const teamMap = ref({})
const loading = ref(false)
const activeTeam = ref(null)

const selected = computed(() => tournaments.value.find((t) => t.id === selectedTid.value))
const isPublic = computed(() => !!selected.value?.results_public)

async function loadTournaments() {
  const { data } = await api.get('/public/tournaments')
  tournaments.value = data
  if (data.length && !data.some((t) => t.id === selectedTid.value)) {
    selectedTid.value = data[0].id
  }
}

async function loadContent() {
  if (!selected.value) return
  loading.value = true
  teams.value = []
  myTeams.value = []
  rounds.value = []
  teamMap.value = {}
  try {
    if (isPublic.value) {
      const [teamsRes, bracketRes] = await Promise.all([
        api.get(`/public/tournaments/${selectedTid.value}/teams`),
        api.get(`/public/tournaments/${selectedTid.value}/bracket`),
      ])
      teams.value = teamsRes.data
      rounds.value = bracketRes.data.bracket.rounds || []
      teamMap.value = bracketRes.data.teams || {}
    } else if (auth.isAuthenticated) {
      // During registration users may only see their own teams.
      const { data } = await api.get('/teams/mine', { params: { tournament_id: selectedTid.value } })
      myTeams.value = data
    }
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

watch(selectedTid, loadContent)
onMounted(async () => {
  await loadTournaments()
  await loadContent()
})
</script>

<template>
  <div class="container">
    <h1>赛事浏览</h1>
    <p class="muted">报名截止后公布全部参赛战队与晋级对阵；报名期间仅可查看自己的战队。</p>

    <!-- Tournament tabs -->
    <div v-if="tournaments.length" class="tour-tabs">
      <button
        v-for="t in tournaments"
        :key="t.id"
        class="tour-tab"
        :class="{ active: t.id === selectedTid }"
        @click="selectedTid = t.id"
      >
        {{ t.name }}
        <span class="tour-state" :class="t.results_public ? 'done' : 'live'">
          {{ t.results_public ? '已公布' : '报名中' }}
        </span>
      </button>
    </div>

    <template v-if="selected">
      <!-- Registration still open: gated -->
      <div v-if="!isPublic">
        <div class="panel gate">
          <div class="gate-icon">🔒</div>
          <h2>报名进行中</h2>
          <p class="muted">
            该赛事将于 <strong>{{ formatDeadline(selected.registration_deadline) }}</strong>
            （{{ countdown(selected.registration_deadline) }}）报名截止，届时公布全部参赛战队与对阵图。
          </p>
        </div>

        <template v-if="auth.isAuthenticated">
          <h2 class="teams-title">我的战队 <span class="muted">（报名期间仅你可见）</span></h2>
          <p v-if="loading" class="muted">加载中…</p>
          <p v-else-if="!myTeams.length" class="muted">你还没有在该赛事报名的战队。</p>
          <div class="team-grid">
            <div v-for="t in myTeams" :key="t.id" class="card team-card" @click="activeTeam = t">
              <div class="row">
                <h3 style="margin: 0">{{ t.name }}</h3>
                <span class="badge" :class="t.status">{{ STATUS_LABEL[t.status] }}</span>
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
            </div>
          </div>
        </template>
        <p v-else class="muted login-hint">
          <RouterLink to="/login">登录</RouterLink> 后可在报名期间查看自己已提交的战队。
        </p>
      </div>

      <!-- Registration closed: public -->
      <template v-else>
        <section class="panel bracket-panel">
          <h2>赛事对阵图</h2>
          <Bracket :rounds="rounds" :team-map="teamMap" />
        </section>

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
      </template>
    </template>

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
.tour-tabs { display: flex; gap: 0.6rem; flex-wrap: wrap; margin: 1.25rem 0 1.75rem; }
.tour-tab {
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.5rem 1rem; border-radius: 980px;
  border: 1px solid var(--border-strong); background: #fff;
  color: var(--text); font-weight: 500; font-size: 0.9rem; cursor: pointer;
  transition: all 0.15s;
}
.tour-tab:hover { border-color: var(--primary); }
.tour-tab.active { background: var(--primary); color: #fff; border-color: var(--primary); }
.tour-state { font-size: 0.68rem; padding: 1px 7px; border-radius: 999px; font-weight: 700; }
.tour-state.live { background: rgba(255, 149, 0, 0.18); color: #a85e00; }
.tour-state.done { background: rgba(52, 199, 89, 0.2); color: #1f7a34; }
.tour-tab.active .tour-state { background: rgba(255, 255, 255, 0.25); color: #fff; }

.gate { text-align: center; padding: 2.5rem 1.5rem; }
.gate-icon { font-size: 2.4rem; margin-bottom: 0.4rem; }
.gate p { max-width: 560px; margin: 0.4rem auto 0; }
.login-hint { margin-top: 1rem; }

.bracket-panel { margin: 0 0 2rem; }
.teams-title { margin-top: 1.5rem; }
.team-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; margin-top: 1rem; }
.team-card { cursor: pointer; transition: transform 0.12s, box-shadow 0.12s; }
.team-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
.declaration { color: var(--accent); font-style: italic; margin: 0.5rem 0; }
.players { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.5rem; }
.small { font-size: 0.8rem; }
</style>
