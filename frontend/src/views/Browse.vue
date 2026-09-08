<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import api from '../api'
import { toast } from '../toast'
import { PROFESSIONS } from '../roster'
import { formatDeadline, countdown } from '../time'
import { useAuthStore } from '../stores/auth'
import Bracket from '../components/Bracket.vue'
import Poster from '../components/Poster.vue'
import Announcement from '../components/Announcement.vue'
import Spinner from '../components/Spinner.vue'
import { tournamentVisual } from '../tournamentAssets'
import PageHeading from '../components/PageHeading.vue'
import Icon from '../components/Icon.vue'

const auth = useAuthStore()

const STATUS_LABEL = { pending: '审核中', approved: '已通过', rejected: '未通过' }
const REGISTRATION_LABEL = { team: '战队报名', solo: '个人报名' }

const tournaments = ref([])
const selectedTid = ref(null)
const teams = ref([])
const myTeams = ref([])
const stages = ref([])
const teamMap = ref({})
const loading = ref(false)
const booting = ref(true)
const bootError = ref('')
const activeTeam = ref(null)
const detailTournament = ref(null)
const announceTournament = ref(null)

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
  stages.value = []
  teamMap.value = {}
  try {
    if (isPublic.value) {
      const [teamsRes, bracketRes] = await Promise.all([
        api.get(`/public/tournaments/${selectedTid.value}/teams`),
        api.get(`/public/tournaments/${selectedTid.value}/bracket`),
      ])
      teams.value = teamsRes.data
      stages.value = bracketRes.data.bracket.stages || []
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

function openTournamentAnnounce(tournament) {
  announceTournament.value = tournament
}

watch(selectedTid, loadContent)
async function boot() {
  booting.value = true
  bootError.value = ''
  try {
    await loadTournaments()
    await loadContent()
  } catch (e) {
    bootError.value = e.message || '赛事加载失败，请稍后重试'
  } finally {
    booting.value = false
  }
}
onMounted(boot)
</script>

<template>
  <div class="container">
<PageHeading title="赛事浏览" description="选择一场赛事，查看比赛公告、参赛名单与晋级对阵。" icon="trophy"><RouterLink to="/signup" class="btn">我要报名<Icon name="arrow" :size="17" /></RouterLink></PageHeading>

    <!-- Tournament cards -->
    <Spinner v-if="booting && !tournaments.length" label="加载赛事中" />
    <div v-if="bootError" class="empty-state" role="alert"><Icon name="flag" /><h2>赛事暂时未能加载</h2><p>{{ bootError }}</p><button class="btn" @click="boot">重新加载</button></div>
    <div v-else-if="!booting && !tournaments.length" class="empty-state"><Icon name="trophy" /><h2>下一场精彩，正在准备</h2><p>暂时没有公开赛事。赛事发布后，你可以在这里查看规则和报名安排。</p><RouterLink to="/" class="btn ghost">返回赛事大厅</RouterLink></div>
    <div v-if="tournaments.length" class="list-heading"><h2>全部赛事 <span>{{ tournaments.length }}</span></h2><p>选择赛事查看详细信息</p></div>
    <div v-if="tournaments.length" class="tournament-grid">
      <article
        v-for="(t, i) in tournaments"
        :key="t.id"
        class="tournament-card"
        :class="{ active: t.id === selectedTid }"
        :style="{ '--i': i }"
        tabindex="0"
        role="group"
        :aria-label="`${t.name}${t.id === selectedTid ? '，当前选中' : '，按回车选择赛事'}`"
        @keydown.enter.self="selectTournament(t)"
        @keydown.space.prevent.self="selectTournament(t)"
        @click="selectTournament(t)"
      >
        <div class="tournament-main">
          <img :src="tournamentVisual(t).avatar" :alt="`${t.name} 头像`" class="tournament-avatar" />
          <div class="tournament-copy">
            <div class="row">
              <h3>{{ t.name }}</h3>
              <span class="spacer"></span>
              <span class="tour-state" :class="t.results_public ? 'done' : 'live'">
                {{ t.results_public ? '已公布' : t.registration_open ? '报名中' : '待公布' }}
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

        <div class="card-actions">
          <button class="btn ghost announce-btn" @click.stop="openTournamentAnnounce(t)">比赛公告</button>
          <button class="btn accent detail-btn" @click.stop="openTournamentDetail(t)">比赛详情</button>
        </div>
      </article>
    </div>

    <Transition name="content-swap" mode="out-in">
      <div v-if="selected" :key="`${selectedTid}-${isPublic}`">
        <!-- Registration still open: gated -->
        <div v-if="!isPublic">
          <div class="panel gate">
            <div class="gate-icon"><Icon name="clock" :size="29" /></div>
            <h2>{{ selected.registration_open ? '战队集结中，敬请期待对阵' : '报名已截止，等待赛事公布' }}</h2>
            <p class="muted">
              报名截止时间：<strong>{{ formatDeadline(selected.registration_deadline) }}</strong>
              （{{ countdown(selected.registration_deadline) }}）。赛事公布后，可在这里查看参赛名单与晋级对阵。
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
                tabindex="0" role="button" :aria-label="`查看${t.name}报名详情`"
                @keydown.enter="activeTeam = t" @keydown.space.prevent="activeTeam = t"
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
            <Bracket :stages="stages" :team-map="teamMap" />
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
              tabindex="0" role="button" :aria-label="`查看${t.name}报名详情`"
                @keydown.enter="activeTeam = t" @keydown.space.prevent="activeTeam = t"
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
          <button class="poster-close" aria-label="关闭弹窗" @click="detailTournament = null">✕</button>
          <Poster :tournament="detailTournament" />
        </div>
      </div>
    </Transition>

    <!-- Tournament announcement modal -->
    <Transition name="modal-fade">
      <div v-if="announceTournament" class="modal-backdrop poster-backdrop" @click.self="announceTournament = null">
        <div class="poster-shell">
          <button class="poster-close" aria-label="关闭弹窗" @click="announceTournament = null">✕</button>
          <Announcement :tournament="announceTournament" />
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.list-heading { display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-bottom: .9rem; }
.list-heading h2 { font-size: 1rem; margin: 0; display: flex; align-items: center; gap: .55rem; }
.list-heading h2 span { font-size: .72rem; background: #e0e5eb; padding: .15rem .45rem; border-radius: 4px; color: #566373; }
.list-heading p { margin: 0; color: var(--muted); font-size: .76rem; }
.tournament-grid { display: grid; gap: .85rem; margin: 0 0 2rem; }
.tournament-card { display: grid; grid-template-columns: minmax(0,1fr) 200px auto; align-items: center; gap: 1.5rem; padding: 1.4rem; border: 1px solid var(--border); border-radius: 10px; background: #fff; cursor: pointer; transition: border-color .18s, background .18s; }
.tournament-card:hover { border-color: #aab6c1; }
.tournament-card.active { border-color: var(--primary); background: #fffcfa; }
.tournament-main { display: grid; grid-template-columns: 74px minmax(0,1fr); gap: 1rem; align-items: center; }
.tournament-avatar { width: 74px; height: 74px; border-radius: 8px; object-fit: cover; }
.tournament-copy { min-width: 0; }
.tournament-copy h3 { margin: 0; font-size: 1.08rem; }
.tournament-copy .spacer { display: none; }
.tournament-copy p { margin: .5rem 0 0; font-size: .8rem; line-height: 1.6; }
.tournament-meta { display: flex; flex-direction: column; gap: .4rem; font-size: .73rem; color: var(--muted); padding-left: 1.5rem; border-left: 1px solid var(--border); }
.tournament-meta strong { color: var(--text); font-weight: 600; }
.tournament-meta span:first-child strong { font-size: 1.15rem; margin-right: .25rem; }
.card-actions { display: flex; gap: .5rem; }
.card-actions .btn { min-height: 39px; padding: .6rem .75rem; font-size: .76rem; }
.tour-state { display: inline-flex; align-items: center; font-size: .68rem; line-height: 1.5; padding: .15rem .45rem; border-radius: 4px; font-weight: 600; white-space: nowrap; }
.tour-state.live { background: #fff0d9; color: #87510a; }
.tour-state.done { background: #e5f3eb; color: #187447; }
.gate { text-align: center; padding: 2.7rem 1.5rem; background: #e8edf2; border: 0; }
.gate-icon { width: 62px; height: 62px; background: #fff; color: #596e82; display: grid; place-items: center; border-radius: 12px; margin: 0 auto 1rem; }
.gate h2 { font-size: 1.25rem; }
.gate p { max-width: 65ch; margin: .6rem auto 0; font-size: .85rem; line-height: 1.9; }
.login-hint { text-align: center; font-size: .82rem; margin: 1.4rem 0; }
.bracket-panel { margin: 0 0 2rem; padding: 1.7rem; }
.bracket-panel > h2 { padding-bottom: 1.1rem; border-bottom: 1px solid var(--border); font-size: 1.2rem; margin-bottom: 1.5rem; }
.teams-title { margin: 1.8rem 0 1rem; font-size: 1.2rem; }
.teams-title .muted { font-weight: 400; font-size: .8rem; }
.team-grid { display: grid; grid-template-columns: repeat(auto-fill,minmax(280px,1fr)); gap: 1rem; }
.team-card { cursor: pointer; }
.team-card:hover { border-color: var(--primary); }
.team-card h3 { font-size: 1rem; }
.declaration { color: #8b531c; font-size: .84rem; margin: .75rem 0; overflow-wrap: anywhere; }
.players { display: flex; gap: .4rem; flex-wrap: wrap; margin-top: .85rem; }
.small { font-size: .77rem; }
.type-chip { background: #eef1f5; font-size: .68rem; }
.poster-shell { position: relative; width: min(790px,100%); max-height: 90dvh; overflow: auto; border-radius: 12px; }
.poster-close { position: sticky; top: 12px; float: right; margin: 12px 12px -56px 0; z-index: 2; width: 40px; height: 40px; border: 1px solid #ffffff60; border-radius: 7px; cursor: pointer; color: #fff; background: #172330; font-size: .9rem; }
.poster-close:hover { background: #33495c; }
.content-swap-enter-active, .content-swap-leave-active { transition: opacity .16s; }
.content-swap-enter-from, .content-swap-leave-to { opacity: 0; }
@media(max-width:1050px) { .tournament-card { grid-template-columns: minmax(0,1fr) 180px; gap: 1rem; } .card-actions { grid-column: 1/-1; padding-top: .9rem; border-top: 1px solid var(--border); justify-content: flex-end; } }
@media(max-width:620px) { .tournament-card { display: flex; flex-direction: column; align-items: stretch; padding: 1.1rem; gap: 1rem; } .tournament-main { grid-template-columns: 60px minmax(0,1fr); gap: .8rem; } .tournament-avatar { width: 60px; height: 60px; } .tournament-copy h3 { font-size: .98rem; } .tournament-meta { border: 0; padding: 0; flex-direction: row; flex-wrap: wrap; gap: .5rem 1.2rem; align-items: center; } .tournament-meta span:first-child strong { font-size: .9rem; } .card-actions { padding-top: .85rem; } .card-actions .btn { flex: 1; min-height: 42px; } .team-grid { grid-template-columns: 1fr; } .gate { padding: 2rem 1.2rem; } .gate h2 { font-size: 1.15rem; } .gate p { font-size: .8rem; } .bracket-panel { padding: 1.1rem; } .list-heading p { font-size: .68rem; } }
</style>
