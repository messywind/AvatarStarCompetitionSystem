<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import api from '../api'
import { toast } from '../toast'
import { PROFESSIONS, validateRoster } from '../roster'
import { formatDeadline, toLocalInput } from '../time'
import RosterEditor from '../components/RosterEditor.vue'
import Bracket from '../components/Bracket.vue'

const STATUS_LABEL = { pending: '审核中', approved: '已通过', rejected: '未通过' }
const REGISTRATION_LABEL = { team: '战队报名', solo: '个人报名' }

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

const POSTER_KEYS = [
  'format', 'profession_limit', 'mode_limit', 'item_limit', 'equipment_limit', 'other_limit',
  'reward_champion', 'reward_runner_up', 'reward_third', 'reward_fourth', 'reward_other',
]
function blankPoster() {
  return Object.fromEntries(POSTER_KEYS.map((k) => [k, '']))
}

const tourModal = ref(false)
const tourEditingId = ref(null)
const tourForm = reactive({ name: '', description: '', registration_deadline: '', poster: blankPoster() })

function openTourCreate() {
  tourEditingId.value = null
  tourForm.name = ''
  tourForm.description = ''
  tourForm.registration_deadline = ''
  Object.assign(tourForm.poster, blankPoster())
  tourModal.value = true
}
function openTourEdit(t) {
  tourEditingId.value = t.id
  tourForm.name = t.name
  tourForm.description = t.description || ''
  tourForm.registration_deadline = toLocalInput(t.registration_deadline)
  Object.assign(tourForm.poster, blankPoster(), t.poster || {})
  tourModal.value = true
}
async function saveTour() {
  if (!tourForm.name.trim()) return toast('请填写赛事名称', 'error')
  if (!tourForm.registration_deadline) return toast('请设置报名截止时间', 'error')
  const payload = {
    name: tourForm.name.trim(),
    description: tourForm.description.trim(),
    registration_deadline: tourForm.registration_deadline,
    poster: { ...tourForm.poster },
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
  if (!confirm(`确定删除赛事「${t.name}」？其下所有报名记录与对阵图都会被删除，且不可撤销。`)) return
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
  if (!confirm(`确定删除报名记录「${team.name}」？此操作不可撤销。`)) return
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
    registration_type: 'team',
    name: '',
    captain: '',
    contact: '',
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
const createIsSolo = computed(() => createForm.registration_type === 'solo')
const canCreate = computed(
  () =>
    createIsSolo.value
      ? !!createForm.players[0]?.nickname?.trim() && !!createForm.contact.trim()
      : createForm.name.trim() && createForm.captain.trim() && createForm.contact.trim() && createValidation.value.errors.length === 0
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
    const players = createIsSolo.value
      ? [
          {
            nickname: createForm.players[0].nickname.trim(),
            profession: createForm.players[0].profession,
            is_substitute: false,
          },
        ]
      : createForm.players.map((p) => ({
          nickname: p.nickname.trim(),
          profession: p.profession,
          is_substitute: p.is_substitute,
        }))
    await api.post('/admin/teams', {
      tournament_id: selectedTid.value,
      registration_type: createForm.registration_type,
      name: createForm.name.trim(),
      captain: createForm.captain.trim(),
      contact: createForm.contact.trim(),
      declaration: createForm.declaration.trim(),
      status: createForm.status,
      players,
    })
    toast('报名记录已新增', 'success')
    creating.value = false
    await loadTeams()
  } catch (e) {
    toast(e.message || '新增失败', 'error')
  }
}

// ------- Edit modal -------
const editing = ref(null) // team being edited
const editForm = reactive({ registration_type: 'team', name: '', captain: '', contact: '', declaration: '', players: [] })
const editValidation = computed(() => validateRoster(editForm.players))
const editIsSolo = computed(() => editForm.registration_type === 'solo')

function openEdit(team) {
  editing.value = team
  editForm.registration_type = team.registration_type || 'team'
  editForm.name = team.name
  editForm.captain = team.captain
  editForm.contact = team.contact || ''
  editForm.declaration = team.declaration || ''
  editForm.players = team.players.map((p) => ({
    nickname: p.nickname,
    profession: p.profession,
    is_substitute: p.is_substitute,
  }))
}

async function saveEdit() {
  if (!editForm.contact.trim()) {
    toast('请填写联系方式', 'error')
    return
  }
  if (editIsSolo.value && !editForm.players[0]?.nickname?.trim()) {
    toast('请填写个人报名称呼', 'error')
    return
  }
  if (!editIsSolo.value && editValidation.value.errors.length) {
    toast('阵容不符合规则，请修正', 'error')
    return
  }
  try {
    const players = editIsSolo.value
      ? [
          {
            nickname: editForm.players[0].nickname.trim(),
            profession: editForm.players[0].profession,
            is_substitute: false,
          },
        ]
      : editForm.players.map((p) => ({
          nickname: p.nickname.trim(),
          profession: p.profession,
          is_substitute: p.is_substitute,
        }))
    await api.put(`/admin/teams/${editing.value.id}`, {
      registration_type: editForm.registration_type,
      name: editForm.name.trim(),
      captain: editForm.captain.trim(),
      contact: editForm.contact.trim(),
      declaration: editForm.declaration.trim(),
      players,
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
  if (n < 2) return toast('通过审核的报名不足 2 条，无法生成对阵图', 'error')
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
        <button class="btn sm" :class="{ ghost: tab !== 'teams' }" @click="tab = 'teams'">报名管理</button>
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
            <tr><th>ID</th><th>赛事名称</th><th>报名截止</th><th>状态</th><th>报名数</th><th>操作</th></tr>
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
        <span class="muted">共 {{ teams.length }} 条</span>
        <button class="btn sm" :disabled="!selectedTid" @click="openCreate">+ 新增报名</button>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>类型</th><th>名称</th><th>队长/称呼</th><th>联系方式</th><th>报名账号</th><th>阵容</th><th>作战宣言</th><th>状态</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading"><td colspan="10" class="muted">加载中…</td></tr>
            <tr v-else-if="!teams.length"><td colspan="10" class="muted">暂无数据</td></tr>
            <tr v-for="t in teams" :key="t.id">
              <td>{{ t.id }}</td>
              <td><span class="chip sm type-chip">{{ REGISTRATION_LABEL[t.registration_type] || '报名' }}</span></td>
              <td><strong>{{ t.name }}</strong></td>
              <td>{{ t.captain }}</td>
              <td>{{ t.contact }}</td>
              <td class="muted">{{ t.owner.username }}</td>
              <td>
                <div v-if="t.registration_type === 'solo'" class="prof-mini">
                  <span class="chip sm">
                    <span class="dot" :style="{ background: `var(--prof-${t.players[0]?.profession || '突击'})` }"></span>
                    {{ t.players[0]?.profession || '未填职业' }}
                  </span>
                </div>
                <template v-else>
                  <div class="prof-mini">
                    <span v-for="prof in PROFESSIONS" :key="prof" class="chip sm">
                      <span class="dot" :style="{ background: `var(--prof-${prof})` }"></span>
                      {{ professionCounts(t.players)[prof] }}
                    </span>
                  </div>
                  <span class="muted tiny">正式 {{ formalCount(t.players) }} · 替补 {{ subCount(t.players) }}</span>
                </template>
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
          <button class="btn ghost sm" @click="generateSkeleton">按已通过报名自动生成</button>
          <button class="btn ghost sm" @click="addRound">+ 添加轮次</button>
          <button class="btn success sm" @click="saveBracket">保存对阵图</button>
        </div>
        <p class="muted">
          配置各轮次的对阵与获胜方；获胜方会在浏览端高亮以展示晋级情况。
          仅「已通过」的报名可被选择（当前 {{ approvedTeams.length }} 条）。
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
    <Transition name="modal-fade">
      <div v-if="tourModal" class="modal-backdrop" @click.self="tourModal = false">
        <div class="modal tour-modal">
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
            <p class="muted tiny" style="margin-top:0.35rem">截止后才会向所有人公开参赛名单与对阵图；截止前用户只能看到自己的报名。</p>
          </div>

          <h4 class="poster-group">比赛详情 · 参赛规则</h4>
          <p class="muted tiny" style="margin:-0.4rem 0 0.7rem">以下内容将自动生成为比赛详情海报，用户在「比赛详情」中查看。每行一条，留空则不显示该项。</p>
          <div class="field"><label>比赛形式</label><textarea v-model="tourForm.poster.format" rows="1" placeholder="例如：5v5"></textarea></div>
          <div class="field"><label>职业限制</label><textarea v-model="tourForm.poster.profession_limit" placeholder="每行一条，例如：&#10;各职业不得超过两名（生化限一名）&#10;每个职业至少有一个"></textarea></div>
          <div class="field"><label>模式限制</label><textarea v-model="tourForm.poster.mode_limit" placeholder="例如：预选赛模式为 占点 夺旗 团战 纯随机"></textarea></div>
          <div class="field"><label>药物及道具限制</label><textarea v-model="tourForm.poster.item_limit" placeholder="每行一条"></textarea></div>
          <div class="field"><label>装备限制</label><textarea v-model="tourForm.poster.equipment_limit" placeholder="每行一条"></textarea></div>
          <div class="field"><label>其他限制</label><textarea v-model="tourForm.poster.other_limit" placeholder="例如：其余以赛事官方为准"></textarea></div>

          <h4 class="poster-group">比赛详情 · 官方奖励</h4>
          <div class="field"><label>冠军奖励</label><textarea v-model="tourForm.poster.reward_champion" rows="2" placeholder="例如：三把 ROG 夜魔键盘 价值 5000 元（队伍自行分配）"></textarea></div>
          <div class="field"><label>亚军奖励</label><textarea v-model="tourForm.poster.reward_runner_up" rows="2" placeholder="例如：三把龙鳞 2 鼠标 价值 3000 元"></textarea></div>
          <div class="field"><label>季军奖励</label><textarea v-model="tourForm.poster.reward_third" rows="2" placeholder="例如：每人 1500 兑换卷"></textarea></div>
          <div class="field"><label>殿军奖励</label><textarea v-model="tourForm.poster.reward_fourth" rows="2" placeholder="例如：每人 500 兑换卷"></textarea></div>
          <div class="field"><label>其他奖励</label><textarea v-model="tourForm.poster.reward_other" rows="2" placeholder="例如：更有众多参与奖神秘奖等待抽选"></textarea></div>

          <button class="btn accent" style="width: 100%" @click="saveTour">
            {{ tourEditingId ? '保存修改' : '创建赛事' }}
          </button>
        </div>
      </div>
    </Transition>

    <!-- ===================== CREATE TEAM MODAL ===================== -->
    <Transition name="modal-fade">
      <div v-if="creating" class="modal-backdrop" @click.self="creating = false">
        <div class="modal">
          <div class="row">
            <h2 style="margin: 0">新增报名</h2>
            <span class="spacer"></span>
            <button class="btn ghost sm" @click="creating = false">取消</button>
          </div>
          <p class="muted">录入到「{{ selectedTournament?.name }}」；可直接指定初始审核状态。</p>
          <div class="field">
            <label>报名类型</label>
            <select v-model="createForm.registration_type" class="status-select">
              <option value="team">战队报名</option>
              <option value="solo">个人报名</option>
            </select>
          </div>
          <template v-if="!createIsSolo">
            <div class="field"><label>队伍名称 *</label><input v-model="createForm.name" maxlength="128" placeholder="例如：烈焰星辰" /></div>
            <div class="field"><label>队长 *</label><input v-model="createForm.captain" maxlength="64" placeholder="队长称呼" /></div>
          </template>
          <template v-else>
            <div class="field"><label>称呼 *</label><input v-model="createForm.players[0].nickname" maxlength="64" placeholder="个人报名称呼" /></div>
            <div class="field">
              <label>职业 *</label>
              <select v-model="createForm.players[0].profession" class="status-select">
                <option v-for="prof in PROFESSIONS" :key="prof" :value="prof">{{ prof }}</option>
              </select>
            </div>
          </template>
          <div class="field"><label>联系方式 *</label><input v-model="createForm.contact" maxlength="128" placeholder="QQ / 微信 / 手机号" /></div>
          <div class="field">
            <label>初始状态</label>
            <select v-model="createForm.status" class="status-select">
              <option value="approved">已通过</option>
              <option value="pending">审核中</option>
              <option value="rejected">未通过</option>
            </select>
          </div>
          <template v-if="!createIsSolo">
            <h4>参赛阵容 *</h4>
            <RosterEditor v-model="createForm.players" />
          </template>
          <div class="field" style="margin-top: 1rem"><label>作战宣言</label><textarea v-model="createForm.declaration" maxlength="2000"></textarea></div>
          <button class="btn accent" style="width: 100%" :disabled="!canCreate" @click="saveCreate">
            新增报名
          </button>
        </div>
      </div>
    </Transition>

    <!-- ===================== EDIT MODAL ===================== -->
    <Transition name="modal-fade">
      <div v-if="editing" class="modal-backdrop" @click.self="editing = null">
        <div class="modal">
          <div class="row">
            <h2 style="margin: 0">编辑战队 · {{ editing.name }}</h2>
            <span class="chip sm type-chip">{{ REGISTRATION_LABEL[editForm.registration_type] || '报名' }}</span>
            <span class="spacer"></span>
            <button class="btn ghost sm" @click="editing = null">取消</button>
          </div>
          <div class="field">
            <label>报名类型</label>
            <select v-model="editForm.registration_type" class="status-select">
              <option value="team">战队报名</option>
              <option value="solo">个人报名</option>
            </select>
          </div>
          <template v-if="!editIsSolo">
            <div class="field"><label>队伍名称</label><input v-model="editForm.name" /></div>
            <div class="field"><label>队长</label><input v-model="editForm.captain" /></div>
            <h4>参赛阵容</h4>
            <RosterEditor v-model="editForm.players" />
          </template>
          <template v-else>
            <div class="field"><label>称呼</label><input v-model="editForm.players[0].nickname" /></div>
            <div class="field">
              <label>职业</label>
              <select v-model="editForm.players[0].profession" class="status-select">
                <option v-for="prof in PROFESSIONS" :key="prof" :value="prof">{{ prof }}</option>
              </select>
            </div>
          </template>
          <div class="field"><label>联系方式</label><input v-model="editForm.contact" maxlength="128" /></div>
          <div class="field" style="margin-top: 1rem"><label>作战宣言</label><textarea v-model="editForm.declaration"></textarea></div>
          <button class="btn accent" style="width: 100%" :disabled="!editIsSolo && editValidation.errors.length > 0" @click="saveEdit">
            保存修改
          </button>
        </div>
      </div>
    </Transition>
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

.editor-rounds { display: flex; gap: 1rem; overflow-x: auto; padding: 1rem 0; align-items: flex-start; scroll-snap-type: x proximity; -webkit-overflow-scrolling: touch; }
.editor-round { min-width: 280px; scroll-snap-align: start; animation: editor-round-in 0.3s var(--ease-soft) both; }
.round-name { width: 140px; font-weight: 700; }
.editor-match { border-top: 1px solid var(--border); padding: 0.7rem 0; }
.mrow { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.4rem; }
.vs { color: var(--accent); font-weight: 800; font-size: 0.8rem; }
.winner-sel { width: 130px; }
.tour-modal { width: min(560px, 100%); }
.poster-group {
  margin: 1.4rem 0 0.8rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  font-size: 0.98rem;
}
.status-select { width: 200px; }

@keyframes editor-round-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@media (max-width: 760px) {
  .container > .row:first-child {
    align-items: flex-start;
  }
  .container > .row:first-child h1 {
    width: 100%;
  }
  .tabs {
    width: 100%;
    overflow-x: auto;
    padding-bottom: 0.1rem;
    scrollbar-width: none;
  }
  .tabs::-webkit-scrollbar { display: none; }
  .tabs .btn {
    flex: 0 0 auto;
  }
  .scope-bar {
    align-items: stretch;
  }
  .scope-bar label,
  .scope-bar select {
    width: 100% !important;
  }
  .toolbar {
    align-items: stretch;
  }
  .toolbar label,
  .toolbar select {
    width: 100% !important;
  }
  .toolbar .btn {
    flex: 1 1 auto;
  }
  .actions .btn {
    min-width: 74px;
  }
  .declaration-cell {
    min-width: 180px;
  }
  .editor-rounds {
    margin-left: -0.2rem;
    margin-right: -0.2rem;
  }
  .editor-round {
    min-width: min(88vw, 340px);
  }
  .editor-round > .row {
    align-items: stretch;
  }
  .round-name {
    width: 100%;
  }
  .mrow {
    display: grid;
    grid-template-columns: 1fr;
    align-items: stretch;
  }
  .vs {
    text-align: center;
  }
  .winner-sel,
  .status-select {
    width: 100%;
  }
}

@media (max-width: 520px) {
  .tabs .btn {
    min-width: 112px;
  }
  .toolbar .spacer,
  .scope-bar .spacer {
    display: none;
  }
  .actions {
    min-width: 160px;
  }
  .actions .btn {
    flex: 1 1 72px;
  }
  .modal h2 {
    font-size: 1.25rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .editor-round {
    animation: none;
  }
}
</style>
