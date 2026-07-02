<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import api from '../api'
import { toast } from '../toast'
import { PROFESSIONS } from '../roster'
import { formatDeadline, countdown } from '../time'
import { useAuthStore } from '../stores/auth'
import Bracket from '../components/Bracket.vue'
import Poster from '../components/Poster.vue'
import Spinner from '../components/Spinner.vue'
import { tournamentVisual } from '../tournamentAssets'

const auth = useAuthStore()

const STATUS_LABEL = { pending: '审核中', approved: '已通过', rejected: '未通过' }
const REGISTRATION_LABEL = { team: '战队报名', solo: '个人报名' }

const tournaments = ref([])
const selectedTid = ref(null)
const teams = ref([])
const myTeams = ref([])
const rounds = ref([])
const teamMap = ref({})
const loading = ref(false)
const booting = ref(true)
const activeTeam = ref(null)
const detailTournament = ref(null)

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

function selectTournament(tournament) {
  selectedTid.value = tournament.id
}

function openTournamentDetail(tournament) {
  detailTournament.value = tournament
}

watch(selectedTid, loadContent)
onMounted(async () => {
  try {
    await loadTournaments()
    await loadContent()
  } finally {
    booting.value = false
  }
})
</script>

<template>
  <div class="container">
    <h1>赛事浏览</h1>
    <p class="muted">报名截止后公布全部参赛名单与晋级对阵；报名期间仅可查看自己的报名。</p>

    <!-- Tournament cards -->
    <Spinner v-if="booting && !tournaments.length" label="加载赛事中" />
    <div v-if="tournaments.length" class="tournament-grid">
      <article
        v-for="(t, i) in tournaments"
        :key="t.id"
        class="tournament-card"
        :class="{ active: t.id === selectedTid }"
        :style="{ '--i': i }"
        @click="selectTournament(t)"
      >
        <div class="tournament-main">
          <img :src="tournamentVisual(t).avatar" :alt="`${t.name} 头像`" class="tournament-avatar" />
          <div class="tournament-copy">
            <div class="row">
              <h3>{{ t.name }}</h3>
              <span class="spacer"></span>
              <span class="tour-state" :class="t.results_public ? 'done' : 'live'">
                {{ t.results_public ? '已公布' : '报名中' }}
              </span>
            </div>
            <p class="muted">{{ t.description || '百变兵团民间赛事，等待报名者集结。' }}</p>
          </div>
        </div>

        <div class="tournament-meta">
          <span>
            <strong>{{ t.team_count }}</strong>
            条报名
          </span>
          <span>
            截止：<strong>{{ formatDeadline(t.registration_deadline) }}</strong>
          </span>
        </div>

        <button class="btn accent detail-btn" @click.stop="openTournamentDetail(t)">比赛详情</button>
      </article>
    </div>

    <Transition name="content-swap" mode="out-in">
      <div v-if="selected" :key="`${selectedTid}-${isPublic}`">
        <!-- Registration still open: gated -->
        <div v-if="!isPublic">
          <div class="panel gate">
            <div class="gate-icon">🔒</div>
            <h2>报名进行中</h2>
            <p class="muted">
              该赛事将于 <strong>{{ formatDeadline(selected.registration_deadline) }}</strong>
              （{{ countdown(selected.registration_deadline) }}）报名截止，届时公布全部参赛名单与对阵图。
            </p>
          </div>

          <template v-if="auth.isAuthenticated">
            <h2 class="teams-title">我的报名 <span class="muted">（报名期间仅你可见）</span></h2>
            <Spinner v-if="loading" label="加载中" />
            <p v-else-if="!myTeams.length" class="muted">你还没有在该赛事提交报名。</p>
            <div class="team-grid">
              <div
                v-for="(t, i) in myTeams"
                :key="t.id"
                class="card team-card"
                :style="{ '--i': i }"
                @click="activeTeam = t"
              >
                <div class="row">
                  <h3 style="margin: 0">{{ t.name }}</h3>
                  <span class="chip type-chip">{{ REGISTRATION_LABEL[t.registration_type] || '报名' }}</span>
                  <span class="badge" :class="t.status">{{ STATUS_LABEL[t.status] }}</span>
                  <span class="spacer"></span>
                  <span class="muted small">{{ t.registration_type === 'solo' ? '称呼' : '队长' }} {{ t.captain }}</span>
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
            <RouterLink to="/login">登录</RouterLink> 后可在报名期间查看自己已提交的报名。
          </p>
        </div>

        <!-- Registration closed: public -->
        <template v-else>
          <section class="panel bracket-panel">
            <h2>赛事对阵图</h2>
            <Bracket :rounds="rounds" :team-map="teamMap" />
          </section>

          <h2 class="teams-title">参赛名单 <span class="muted">（{{ teams.length }} 条）</span></h2>
          <Spinner v-if="loading" label="加载中" />
          <p v-else-if="!teams.length" class="muted">暂无通过审核的报名记录。</p>

          <div class="team-grid">
            <div
              v-for="(t, i) in teams"
              :key="t.id"
              class="card team-card"
              :style="{ '--i': i }"
              @click="activeTeam = t"
            >
              <div class="row">
                <h3 style="margin: 0">{{ t.name }}</h3>
                <span class="chip type-chip">{{ REGISTRATION_LABEL[t.registration_type] || '报名' }}</span>
                <span class="spacer"></span>
                <span class="muted small">{{ t.registration_type === 'solo' ? '称呼' : '队长' }} {{ t.captain }}</span>
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
      </div>
    </Transition>

    <!-- Detail modal -->
    <Transition name="modal-fade">
      <div v-if="activeTeam" class="modal-backdrop" @click.self="activeTeam = null">
        <div class="modal">
          <div class="row">
            <h2 style="margin: 0">{{ activeTeam.name }}</h2>
            <span class="chip type-chip">{{ REGISTRATION_LABEL[activeTeam.registration_type] || '报名' }}</span>
            <span class="spacer"></span>
            <button class="btn ghost sm" @click="activeTeam = null">关闭</button>
          </div>
          <p class="muted">{{ activeTeam.registration_type === 'solo' ? '报名称呼' : '队长' }}：{{ activeTeam.captain }}</p>
          <p v-if="activeTeam.contact" class="muted">联系方式：{{ activeTeam.contact }}</p>
          <p v-if="activeTeam.declaration" class="declaration">「{{ activeTeam.declaration }}」</p>

          <h4>{{ activeTeam.registration_type === 'solo' ? '个人信息' : '正式队员' }}</h4>
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
    </Transition>

    <!-- Tournament poster modal -->
    <Transition name="modal-fade">
      <div v-if="detailTournament" class="modal-backdrop poster-backdrop" @click.self="detailTournament = null">
        <div class="poster-shell">
          <button class="poster-close" @click="detailTournament = null">✕</button>
          <Poster :tournament="detailTournament" />
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.tournament-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
  margin: 1.25rem 0 1.75rem;
}
.tournament-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.15rem;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--panel);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  animation: card-rise 0.38s var(--ease-soft) both;
  animation-delay: calc(min(var(--i), 8) * 55ms);
  transition: border-color 0.18s var(--ease-out), box-shadow 0.18s var(--ease-out), transform 0.18s var(--ease-out);
}
.tournament-card:hover { border-color: rgba(0, 113, 227, 0.38); }
.tournament-card.active {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.12), var(--shadow-sm);
}
.tournament-main {
  display: grid;
  grid-template-columns: 72px 1fr;
  gap: 1rem;
  align-items: start;
}
.tournament-avatar {
  width: 72px;
  height: 72px;
  border-radius: 18px;
  object-fit: cover;
  border: 1px solid var(--border);
  transition: transform 0.28s var(--ease-soft), filter 0.28s var(--ease-out);
}
.tournament-card:hover .tournament-avatar { transform: scale(1.035); }
.tournament-copy h3 {
  margin: 0;
  font-size: 1.08rem;
  line-height: 1.35;
}
.tournament-copy p {
  margin: 0.35rem 0 0;
  line-height: 1.6;
}
.tournament-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  color: var(--muted);
  font-size: 0.85rem;
}
.tournament-meta span {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  background: var(--bg-2);
}
.tournament-meta strong { color: var(--text); }
.detail-btn {
  width: 100%;
  margin-top: auto;
  padding: 0.72rem 1.25rem;
}
.tour-state { font-size: 0.68rem; padding: 1px 7px; border-radius: 999px; font-weight: 700; }
.tour-state.live { background: rgba(255, 149, 0, 0.18); color: #a85e00; }
.tour-state.done { background: rgba(52, 199, 89, 0.2); color: #1f7a34; }

.gate { text-align: center; padding: 2.5rem 1.5rem; }
.gate-icon {
  font-size: 2.4rem;
  margin-bottom: 0.4rem;
  animation: lock-pop 0.42s var(--ease-soft) both;
}
.gate p { max-width: 560px; margin: 0.4rem auto 0; }
.login-hint { margin-top: 1rem; }

.bracket-panel { margin: 0 0 2rem; }
.teams-title { margin-top: 1.5rem; }
.team-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; margin-top: 1rem; }
.team-card {
  cursor: pointer;
  animation: card-rise 0.35s var(--ease-soft) both;
  animation-delay: calc(min(var(--i), 10) * 45ms);
}
.team-card:hover { border-color: rgba(0, 113, 227, 0.24); }
.declaration { color: var(--accent); font-style: italic; margin: 0.5rem 0; }
.players { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.5rem; }
.small { font-size: 0.8rem; }

.poster-backdrop { padding: 1rem; }
.poster-shell {
  position: relative;
  width: min(720px, 100%);
  max-height: 92vh;
  overflow: auto;
  border-radius: var(--radius);
}
.poster-close {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 2;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: #fff;
  font-size: 0.9rem;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(6px);
  transition: background 0.15s;
}
.poster-close:hover { background: rgba(0, 0, 0, 0.65); }

.content-swap-enter-active,
.content-swap-leave-active {
  transition: opacity 0.18s var(--ease-out), transform 0.2s var(--ease-out), filter 0.2s var(--ease-out);
}
.content-swap-enter-from {
  opacity: 0;
  transform: translateY(8px);
  filter: blur(4px);
}
.content-swap-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@keyframes card-rise {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@keyframes lock-pop {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@media (max-width: 560px) {
  .tournament-grid {
    grid-template-columns: 1fr;
    gap: 0.85rem;
  }
  .tournament-card {
    padding: 1rem;
  }
  .tournament-main {
    grid-template-columns: 58px 1fr;
    gap: 0.8rem;
  }
  .tournament-avatar {
    width: 58px;
    height: 58px;
    border-radius: 14px;
  }
  .tournament-copy .row {
    align-items: flex-start;
  }
  .tournament-copy h3 {
    flex: 1 1 100%;
  }
  .tournament-meta {
    gap: 0.4rem;
  }
  .tournament-meta span {
    width: 100%;
    justify-content: space-between;
  }
  .team-grid {
    grid-template-columns: 1fr;
  }
  .team-card .row h3 {
    flex: 1 1 100%;
  }
  .gate {
    padding: 2rem 1rem;
  }
  .bracket-panel {
    padding-left: 0.85rem;
    padding-right: 0.85rem;
  }
  .poster-backdrop {
    align-items: center;
  }
  .poster-modal {
    padding: 0.75rem;
    max-height: 94vh;
  }
  .poster-head {
    padding: 0.2rem 0.2rem 0.65rem;
  }
  .poster-head h2 {
    font-size: 1.1rem;
  }
  .poster-image {
    width: 100%;
    max-height: 78vh;
  }
}

@media (hover: hover) and (pointer: fine) {
  .tournament-card:hover,
  .team-card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-md);
  }
}

@media (prefers-reduced-motion: reduce) {
  .tournament-card,
  .team-card,
  .gate-icon {
    animation: none;
  }

  .content-swap-enter-active,
  .content-swap-leave-active {
    transition: none;
  }
}
</style>
