<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '../api'
import { toast } from '../toast'
import { PROFESSIONS, validateRoster } from '../roster'
import RosterEditor from '../components/RosterEditor.vue'
import Bracket from '../components/Bracket.vue'

const STATUS_LABEL = { pending: '审核中', approved: '已通过', rejected: '未通过' }

const tab = ref('teams') // teams | bracket
const teams = ref([])
const filter = ref('')
const loading = ref(false)

// ------- Teams -------
async function loadTeams() {
  loading.value = true
  try {
    const { data } = await api.get('/admin/teams', { params: filter.value ? { status: filter.value } : {} })
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
  try {
    const { data } = await api.get('/admin/bracket')
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
  // largest power of two >= n, capped at 16
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
    await api.put('/admin/bracket', { rounds: rounds.value })
    toast('对阵图已保存', 'success')
  } catch (e) {
    toast(e.message || '保存失败', 'error')
  }
}

onMounted(async () => {
  await loadTeams()
  await loadBracket()
})
</script>

<template>
  <div class="container">
    <div class="row">
      <h1 style="margin: 0">管理端</h1>
      <span class="spacer"></span>
      <div class="tabs">
        <button class="btn sm" :class="{ ghost: tab !== 'teams' }" @click="tab = 'teams'">战队管理</button>
        <button class="btn sm" :class="{ ghost: tab !== 'bracket' }" @click="tab = 'bracket'">对阵图配置</button>
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
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>队伍名称</th>
              <th>队长</th>
              <th>报名账号</th>
              <th>阵容</th>
              <th>作战宣言</th>
              <th>状态</th>
              <th>操作</th>
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
.toolbar { margin: 1.2rem 0 1rem; }
.prof-mini { display: flex; gap: 0.3rem; margin-bottom: 0.2rem; }
.chip.sm { font-size: 0.72rem; padding: 0.1rem 0.4rem; }
.tiny { font-size: 0.72rem; }
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
