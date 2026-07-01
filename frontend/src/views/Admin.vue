<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import api from '../api'
import { toast } from '../toast'
import { PROFESSIONS, validateRoster } from '../roster'
import { formatDeadline, toLocalInput } from '../time'
import RosterEditor from '../components/RosterEditor.vue'
import Bracket from '../components/Bracket.vue'

const STATUS_LABEL = { pending: '审核中', approved: '已通过', rejected: '未通过' }

const tab = ref('tournaments') // tournaments | teams | bracket
const teams = ref([])
const filter = ref('')
const loading = ref(false)

// ------- Tournaments -------
const tournaments = ref([])
const selectedTid = ref(null)
const selectedTournament = computed(() => tournaments.value.find((t) => t.id === selectedTid.value))

async function loadTournaments() {
  try {
    const { data } = await api.get('/admin/tournaments')
    tournaments.value = data
    if (data.length && !data.some((t) => t.id === selectedTid.value)) {
      selectedTid.value = data[0].id
    }
  } catch (e) {
    toast(e.message || '加载赛事失败', 'error')
  }
}

const tourModal = ref(false)
const tourEditingId = ref(null)
const tourForm = reactive({ name: '', description: '', registration_deadline: '' })

function openTourCreate() {
  tourEditingId.value = null
  tourForm.name = ''
  tourForm.description = ''
  tourForm.registration_deadline = ''
  tourModal.value = true
}
function openTourEdit(t) {
  tourEditingId.value = t.id
  tourForm.name = t.name
  tourForm.description = t.description || ''
  tourForm.registration_deadline = toLocalInput(t.registration_deadline)
  tourModal.value = true
}
async function saveTour() {
  if (!tourForm.name.trim()) return toast('请填写赛事名称', 'error')
  if (!tourForm.registration_deadline) return toast('请设置报名截止时间', 'error')
  const payload = {
    name: tourForm.name.trim(),
    description: tourForm.description.trim(),
    registration_deadline: tourForm.registration_deadline,
  }
  try {
    if (tourEditingId.value) {
      await api.put(`/admin/tournaments/${tourEditingId.value}`, payload)
      toast('赛事已更新', 'success')
    } else {
      const { data } = await api.post('/admin/tournaments', payload)
      selectedTid.value = data.id
      toast('赛事已创建', 'success')
    }
    tourModal.value = false
    await loadTournaments()
  } catch (e) {
    toast(e.message || '保存失败', 'error')
  }
}
async function deleteTour(t) {
  if (!confirm(`确定删除赛事「${t.name}」？其下所有战队与对阵图都会被删除，且不可撤销。`)) return
  try {
    await api.delete(`/admin/tournaments/${t.id}`)
    toast('赛事已删除', 'info')
    if (selectedTid.value === t.id) selectedTid.value = null
    await loadTournaments()
  } catch (e) {
    toast(e.message || '删除失败', 'error')
  }
}

// ------- Teams -------
async function loadTeams() {
  if (!selectedTid.value) {
    teams.value = []
    return
  }
  loading.value = true
  try {
    const params = { tournament_id: selectedTid.value }
    if (filter.value) params.status = filter.value
    const { data } = await api.get('/admin/teams', { params })
    teams.value = data
  } catch (e) {
    toast(e.message || '加载失败', 'error')
  } finally {
    loading.value = false
  }
}

function professionCounts(players) {
  const c = Object.fromEntries(PROFESSIONS.map((p) => [p, 0]))
  players.filter((p) => !p.is_substitute).forEach((p) => (c[p.profession] += 1))
  return c
}
function formalCount(players) {
  return players.filter((p) => !p.is_substitute).length
}
function subCount(players) {
  return players.filter((p) => p.is_substitute).length
}

async function review(team, status) {
  let note = team.review_note || ''
  if (status === 'rejected') {
    note = prompt('填写驳回原因（可选）：', note) ?? note
  }
  try {
    await api.patch(`/admin/teams/${team.id}/review`, { status, review_note: note })
    toast(status === 'approved' ? '已通过审核' : status === 'rejected' ? '已驳回' : '已重置为待审核', 'success')
    await loadTeams()
  } catch (e) {
    toast(e.message || '操作失败', 'error')
  }
}

async function removeTeam(team) {
  if (!confirm(`确定删除战队「${team.name}」？此操作不可撤销。`)) return
  try {
    await api.delete(`/admin/teams/${team.id}`)
    toast('已删除', 'info')
    await loadTeams()
  } catch (e) {
    toast(e.message || '删除失败', 'error')
  }
}

// ------- Create team modal -------
function blankTeamForm() {
  return {
    name: '',
    captain: '',
    declaration: '',
    status: 'approved',
    players: [
      { nickname: '', profession: '突击', is_substitute: false },
      { nickname: '', profession: '生化', is_substitute: false },
      { nickname: '', profession: '重装', is_substitute: false },
      { nickname: '', profession: '护卫', is_substitute: false },
      { nickname: '', profession: '突击', is_substitute: false },
    ],
  }
}
const creating = ref(false)
const createForm = reactive(blankTeamForm())
const createValidation = computed(() => validateRoster(createForm.players))
const canCreate = computed(
  () => createForm.name.trim() && createForm.captain.trim() && createValidation.value.errors.length === 0
)

function openCreate() {
  Object.assign(createForm, blankTeamForm())
  creating.value = true
}

async function saveCreate() {
  if (!canCreate.value) {
    toast('请先修正表单中的问题', 'error')
    return
  }
  try {
    await api.post('/admin/teams', {
      tournament_id: selectedTid.value,
      name: createForm.name.trim(),
      captain: createForm.captain.trim(),
      declaration: createForm.declaration.trim(),
      status: createForm.status,
      players: createForm.players.map((p) => ({
        nickname: p.nickname.trim(),
        profession: p.profession,
        is_substitute: p.is_substitute,
      })),
    })
    toast('战队已新增', 'success')
    creating.value = false
    await loadTeams()
  } catch (e) {
    toast(e.message || '新增失败', 'error')
  }
}

// ------- Edit modal -------
const editing = ref(null) // team being edited
const editForm = reactive({ name: '', captain: '', declaration: '', players: [] })
const editValidation = computed(() => validateRoster(editForm.players))

function openEdit(team) {
  editing.value = team
  editForm.name = team.name
  editForm.captain = team.captain
  editForm.declaration = team.declaration || ''
  editForm.players = team.players.map((p) => ({
    nickname: p.nickname,
    profession: p.profession,
    is_substitute: p.is_substitute,
  }))
}

async function saveEdit() {
  if (editValidation.value.errors.length) {
    toast('阵容不符合规则，请修正', 'error')
    return
  }
  try {
    await api.put(`/admin/teams/${editing.value.id}`, {
      name: editForm.name.trim(),
      captain: editForm.captain.trim(),
      declaration: editForm.declaration.trim(),
      players: editForm.players.map((p) => ({
        nickname: p.nickname.trim(),
        profession: p.profession,
        is_substitute: p.is_substitute,
      })),
    })
    toast('保存成功', 'success')
    editing.value = null
    await loadTeams()
  } catch (e) {
    toast(e.message || '保存失败', 'error')
  }
}

// ------- Bracket -------
const rounds = ref([])
const approvedTeams = computed(() => teams.value.filter((t) => t.status === 'approved'))
const bracketTeamMap = computed(() => Object.fromEntries(approvedTeams.value.map((t) => [t.id, t.name])))

async function loadBracket() {
  if (!selectedTid.value) {
    rounds.value = []
    return
  }
  try {
    const { data } = await api.get(`/admin/tournaments/${selectedTid.value}/bracket`)
    rounds.value = data.rounds || []
  } catch (e) {
    toast(e.message || '加载对阵图失败', 'error')
  }
}

function addRound() {
  const defaults = ['16 强', '8 强', '四强', '决赛', '冠军']
  rounds.value.push({ name: defaults[rounds.value.length] || `第 ${rounds.value.length + 1} 轮`, matches: [{ team1: null, team2: null, winner: null }] })
}
function removeRound(ri) {
  rounds.value.splice(ri, 1)
}
function addMatch(round) {
  round.matches.push({ team1: null, team2: null, winner: null })
}
function removeMatch(round, mi) {
  round.matches.splice(mi, 1)
}

function generateSkeleton() {
  const n = approvedTeams.value.length
  if (n < 2) return toast('通过审核的战队不足 2 支，无法生成对阵图', 'error')
  let size = 2
  while (size < n && size < 16) size *= 2
  const seeds = approvedTeams.value.map((t) => t.id)
  const stageNames = { 16: '16 强', 8: '8 强', 4: '四强', 2: '决赛' }
  const newRounds = []
  let count = size
  let first = true
  while (count >= 2) {
    const matches = []
    for (let i = 0; i < count / 2; i++) {
      if (first) {
        matches.push({ team1: seeds[i * 2] ?? null, team2: seeds[i * 2 + 1] ?? null, winner: null })
      } else {
        matches.push({ team1: null, team2: null, winner: null })
      }
    }
    newRounds.push({ name: stageNames[count] || `${count} 强`, matches })
    first = false
    count /= 2
  }
  rounds.value = newRounds
  toast(`已生成 ${size} 强对阵骨架`, 'success')
}

async function saveBracket() {
  try {
    await api.put(`/admin/tournaments/${selectedTid.value}/bracket`, { rounds: rounds.value })
    toast('对阵图已保存', 'success')
  } catch (e) {
    toast(e.message || '保存失败', 'error')
  }
}

// React to tournament switch (for teams & bracket tabs).
watch(selectedTid, async () => {
  await Promise.all([loadTeams(), loadBracket()])
})

onMounted(async () => {
  await loadTournaments()
  await Promise.all([loadTeams(), loadBracket()])
})
</script>

<template>
  <div class="container">
    <div class="row">
      <h1 style="margin: 0">管理端</h1>
      <span class="spacer"></span>
      <div class="tabs">
        <button class="btn sm" :class="{ ghost: tab !== 'tournaments' }" @click="tab = 'tournaments'">赛事管理</button>
        <button class="btn sm" :class="{ ghost: tab !== 'teams' }" @click="tab = 'teams'">战队管理</button>
        <button class="btn sm" :class="{ ghost: tab !== 'bracket' }" @click="tab = 'bracket'">对阵图配置</button>
      </div>
    </div>

    <!-- Tournament scope selector (teams & bracket tabs) -->
    <div v-if="tab !== 'tournaments'" class="row scope-bar">
      <label class="muted">当前赛事：</label>
      <select v-model="selectedTid" style="width: 260px">
        <option v-for="t in tournaments" :key="t.id" :value="t.id">{{ t.name }}</option>
      </select>
      <span v-if="selectedTournament" class="badge" :class="selectedTournament.results_public ? 'approved' : 'pending'">
        {{ selectedTournament.results_public ? '已截止' : '报名中' }}
      </span>
      <span v-if="selectedTournament" class="muted small">截止：{{ formatDeadline(selectedTournament.registration_deadline) }}</span>
    </div>

    <!-- ===================== TOURNAMENTS ===================== -->
    <div v-show="tab === 'tournaments'">
      <div class="row toolbar">
        <span class="muted">共 {{ tournaments.length }} 个赛事</span>
        <span class="spacer"></span>
        <button class="btn sm" @click="openTourCreate">+ 新增赛事</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>赛事名称</th><th>报名截止</th><th>状态</th><th>战队数</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-if="!tournaments.length"><td colspan="6" class="muted">暂无赛事</td></tr>
            <tr v-for="t in tournaments" :key="t.id">
              <td>{{ t.id }}</td>
              <td><strong>{{ t.name }}</strong><div v-if="t.description" class="muted tiny">{{ t.description }}</div></td>
              <td>{{ formatDeadline(t.registration_deadline) }}</td>
              <td>
                <span class="badge" :class="t.results_public ? 'approved' : 'pending'">
                  {{ t.results_public ? '已截止' : '报名中' }}
                </span>
              </td>
              <td>{{ t.team_count }}</td>
              <td>
                <div class="actions">
                  <button class="btn ghost sm" @click="openTourEdit(t)">编辑</button>
                  <button class="btn danger sm" @click="deleteTour(t)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ===================== TEAMS ===================== -->
    <div v-show="tab === 'teams'">
      <div class="row toolbar">
        <label class="muted">筛选状态：</label>
        <select v-model="filter" style="width: 160px" @change="loadTeams">
          <option value="">全部</option>
          <option value="pending">审核中</option>
          <option value="approved">已通过</option>
          <option value="rejected">未通过</option>
        </select>
        <button class="btn ghost sm" @click="loadTeams">刷新</button>
        <span class="spacer"></span>
        <span class="muted">共 {{ teams.length }} 支</span>
        <button class="btn sm" :disabled="!selectedTid" @click="openCreate">+ 新增战队</button>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>队伍名称</th><th>队长</th><th>报名账号</th><th>阵容</th><th>作战宣言</th><th>状态</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="8" class="muted">加载中…</td></tr>
            <tr v-else-if="!teams.length"><td colspan="8" class="muted">暂无数据</td></tr>
            <tr v-for="t in teams" :key="t.id">
              <td>{{ t.id }}</td>
              <td><strong>{{ t.name }}</strong></td>
              <td>{{ t.captain }}</td>
              <td class="muted">{{ t.owner.username }}</td>
              <td>
                <div class="prof-mini">
                  <span v-for="prof in PROFESSIONS" :key="prof" class="chip sm">
                    <span class="dot" :style="{ background: `var(--prof-${prof})` }"></span>
                    {{ professionCounts(t.players)[prof] }}
                  </span>
                </div>
                <span class="muted tiny">正式 {{ formalCount(t.players) }} · 替补 {{ subCount(t.players) }}</span>
              </td>
              <td class="declaration-cell">{{ t.declaration || '—' }}</td>
              <td>
                <span class="badge" :class="t.status">{{ STATUS_LABEL[t.status] }}</span>
                <div v-if="t.review_note" class="muted tiny">{{ t.review_note }}</div>
              </td>
              <td>
                <div class="actions">
                  <button v-if="t.status !== 'approved'" class="btn success sm" @click="review(t, 'approved')">通过</button>
                  <button v-if="t.status !== 'rejected'" class="btn danger sm" @click="review(t, 'rejected')">驳回</button>
                  <button class="btn ghost sm" @click="openEdit(t)">编辑</button>
                  <button class="btn danger sm" @click="removeTeam(t)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ===================== BRACKET ===================== -->
    <div v-show="tab === 'bracket'">
      <div class="panel">
        <div class="row">
          <h2 style="margin: 0">对阵图配置</h2>
          <span class="spacer"></span>
          <button class="btn ghost sm" @click="generateSkeleton">按已通过战队自动生成</button>
          <button class="btn ghost sm" @click="addRound">+ 添加轮次</button>
          <button class="btn success sm" @click="saveBracket">保存对阵图</button>
        </div>
        <p class="muted">
          配置各轮次的对阵与获胜方；获胜方会在浏览端高亮以展示晋级情况。
          仅「已通过」的战队可被选择（当前 {{ approvedTeams.length }} 支）。
        </p>

        <div v-if="!rounds.length" class="muted">尚未添加任何轮次。</div>

        <div class="editor-rounds">
          <div v-for="(round, ri) in rounds" :key="ri" class="editor-round card">
            <div class="row">
              <input v-model="round.name" class="round-name" placeholder="轮次名称" />
              <span class="spacer"></span>
              <button class="btn ghost sm" @click="addMatch(round)">+ 对局</button>
              <button class="btn danger sm" @click="removeRound(ri)">删除轮次</button>
            </div>
            <div v-for="(m, mi) in round.matches" :key="mi" class="editor-match">
              <div class="mrow">
                <select v-model="m.team1">
                  <option :value="null">— 待定 —</option>
                  <option v-for="t in approvedTeams" :key="t.id" :value="t.id">{{ t.name }}</option>
                </select>
                <span class="vs">VS</span>
                <select v-model="m.team2">
                  <option :value="null">— 待定 —</option>
                  <option v-for="t in approvedTeams" :key="t.id" :value="t.id">{{ t.name }}</option>
                </select>
              </div>
              <div class="mrow winner-row">
                <label class="muted tiny">胜者</label>
                <select v-model="m.winner" class="winner-sel">
                  <option :value="null">未定</option>
                  <option v-if="m.team1 != null" :value="m.team1">{{ bracketTeamMap[m.team1] || '#' + m.team1 }}</option>
                  <option v-if="m.team2 != null" :value="m.team2">{{ bracketTeamMap[m.team2] || '#' + m.team2 }}</option>
                </select>
                <span class="spacer"></span>
                <button class="btn danger sm" @click="removeMatch(round, mi)">移除</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="panel" style="margin-top: 1.5rem">
        <h3>预览</h3>
        <Bracket :rounds="rounds" :team-map="bracketTeamMap" />
      </div>
    </div>

    <!-- ===================== TOURNAMENT MODAL ===================== -->
    <div v-if="tourModal" class="modal-backdrop" @click.self="tourModal = false">
      <div class="modal" style="width: min(520px, 100%)">
        <div class="row">
          <h2 style="margin: 0">{{ tourEditingId ? '编辑赛事' : '新增赛事' }}</h2>
          <span class="spacer"></span>
          <button class="btn ghost sm" @click="tourModal = false">取消</button>
        </div>
        <div class="field"><label>赛事名称 *</label><input v-model="tourForm.name" maxlength="128" placeholder="例如：百变兵团第二届选花杯" /></div>
        <div class="field"><label>赛事简介</label><textarea v-model="tourForm.description" maxlength="2000" placeholder="可选"></textarea></div>
        <div class="field">
          <label>报名截止时间 *</label>
          <input v-model="tourForm.registration_deadline" type="datetime-local" />
          <p class="muted tiny" style="margin-top:0.35rem">截止后才会向所有人公开参赛战队与对阵图；截止前用户只能看到自己的战队。</p>
        </div>
        <button class="btn accent" style="width: 100%" @click="saveTour">
          {{ tourEditingId ? '保存修改' : '创建赛事' }}
        </button>
      </div>
    </div>

    <!-- ===================== CREATE TEAM MODAL ===================== -->
    <div v-if="creating" class="modal-backdrop" @click.self="creating = false">
      <div class="modal">
        <div class="row">
          <h2 style="margin: 0">新增战队</h2>
          <span class="spacer"></span>
          <button class="btn ghost sm" @click="creating = false">取消</button>
        </div>
        <p class="muted">录入到「{{ selectedTournament?.name }}」；可直接指定初始审核状态。</p>
        <div class="field"><label>队伍名称 *</label><input v-model="createForm.name" maxlength="128" placeholder="例如：烈焰星辰" /></div>
        <div class="field"><label>队长 *</label><input v-model="createForm.captain" maxlength="64" placeholder="队长称呼" /></div>
        <div class="field">
          <label>初始状态</label>
          <select v-model="createForm.status" style="width: 200px">
            <option value="approved">已通过</option>
            <option value="pending">审核中</option>
            <option value="rejected">未通过</option>
          </select>
        </div>
        <h4>参赛阵容 *</h4>
        <RosterEditor v-model="createForm.players" />
        <div class="field" style="margin-top: 1rem"><label>作战宣言</label><textarea v-model="createForm.declaration" maxlength="2000"></textarea></div>
        <button class="btn accent" style="width: 100%" :disabled="!canCreate" @click="saveCreate">
          新增战队
        </button>
      </div>
    </div>

    <!-- ===================== EDIT MODAL ===================== -->
    <div v-if="editing" class="modal-backdrop" @click.self="editing = null">
      <div class="modal">
        <div class="row">
          <h2 style="margin: 0">编辑战队 · {{ editing.name }}</h2>
          <span class="spacer"></span>
          <button class="btn ghost sm" @click="editing = null">取消</button>
        </div>
        <div class="field"><label>队伍名称</label><input v-model="editForm.name" /></div>
        <div class="field"><label>队长</label><input v-model="editForm.captain" /></div>
        <h4>参赛阵容</h4>
        <RosterEditor v-model="editForm.players" />
        <div class="field" style="margin-top: 1rem"><label>作战宣言</label><textarea v-model="editForm.declaration"></textarea></div>
        <button class="btn accent" style="width: 100%" :disabled="editValidation.errors.length > 0" @click="saveEdit">
          保存修改
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tabs { display: flex; gap: 0.5rem; }
.scope-bar { margin: 1.2rem 0 0.4rem; padding: 0.7rem 0.9rem; background: var(--bg-2); border-radius: var(--radius-sm); }
.toolbar { margin: 1.2rem 0 1rem; }
.prof-mini { display: flex; gap: 0.3rem; margin-bottom: 0.2rem; }
.chip.sm { font-size: 0.72rem; padding: 0.1rem 0.4rem; }
.tiny { font-size: 0.72rem; }
.small { font-size: 0.8rem; }
.declaration-cell { max-width: 220px; color: var(--muted); }
.actions { display: flex; gap: 0.3rem; flex-wrap: wrap; }

.editor-rounds { display: flex; gap: 1rem; overflow-x: auto; padding: 1rem 0; align-items: flex-start; }
.editor-round { min-width: 280px; }
.round-name { width: 140px; font-weight: 700; }
.editor-match { border-top: 1px solid var(--border); padding: 0.7rem 0; }
.mrow { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.4rem; }
.vs { color: var(--accent); font-weight: 800; font-size: 0.8rem; }
.winner-sel { width: 130px; }
</style>
