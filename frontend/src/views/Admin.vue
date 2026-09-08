<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import api from '../api'
import { toast } from '../toast'
import { PROFESSIONS, validateRoster } from '../roster'
import { formatDeadline, toLocalInput } from '../time'
import RosterEditor from '../components/RosterEditor.vue'
import Bracket from '../components/Bracket.vue'
import Spinner from '../components/Spinner.vue'
import { useAuthStore } from '../stores/auth'
import PageHeading from '../components/PageHeading.vue'
import Icon from '../components/Icon.vue'

const STATUS_LABEL = { pending: '审核中', approved: '已通过', rejected: '未通过' }
const REGISTRATION_LABEL = { team: '战队报名', solo: '个人报名' }

const auth = useAuthStore()

const tab = ref('tournaments') // tournaments | teams | bracket | users
const teams = ref([])
const filter = ref('')
const typeFilter = ref('')
const loading = ref(false)

// ------- 确认对话框（删除 / 驳回等危险操作） -------
const confirmState = reactive({
  open: false,
  title: '',
  message: '',
  confirmText: '确定',
  showNote: false,
  note: '',
  notePlaceholder: '',
  action: null,
})
function openConfirm(opts) {
  Object.assign(confirmState, {
    confirmText: '确定',
    showNote: false,
    note: '',
    notePlaceholder: '',
    action: null,
    ...opts,
    open: true,
  })
}
async function doConfirm() {
  const { action, note } = confirmState
  confirmState.open = false
  if (action) await action(note)
}

// ------- Tournaments -------
const tournaments = ref([])
const tourLoading = ref(false)
const selectedTid = ref(null)
const selectedTournament = computed(() => tournaments.value.find((t) => t.id === selectedTid.value))

async function loadTournaments() {
  tourLoading.value = true
  try {
    const { data } = await api.get('/admin/tournaments')
    tournaments.value = data
    if (data.length && !data.some((t) => t.id === selectedTid.value)) {
      selectedTid.value = data[0].id
    }
  } catch (e) {
    toast(e.message || '加载赛事失败', 'error')
  } finally {
    tourLoading.value = false
  }
}

const RULE_KEYS = [
  'format', 'profession_limit', 'mode_limit', 'item_limit', 'equipment_limit', 'other_limit',
  'reward_champion', 'reward_runner_up', 'reward_third', 'reward_fourth', 'reward_other',
]
const ANNOUNCE_KEYS = ['announcement', 'announcement_footer']
const POSTER_KEYS = [...RULE_KEYS, ...ANNOUNCE_KEYS]
function blankPoster() {
  return Object.fromEntries(POSTER_KEYS.map((k) => [k, '']))
}

const REGISTRATION_TYPES = ['team', 'solo']

// 当前选中赛事允许的报名类型与职业（新增/编辑报名时按此过滤选项）
const scopeAllowedTypes = computed(
  () => selectedTournament.value?.rules?.registration_types || REGISTRATION_TYPES
)
const scopeAllowedProfessions = computed(
  () => selectedTournament.value?.rules?.professions || PROFESSIONS
)

const tourModal = ref(false)
const tourEditingId = ref(null)
const tourForm = reactive({
  name: '',
  description: '',
  registration_deadline: '',
  registration_types: [...REGISTRATION_TYPES],
  professions: [...PROFESSIONS],
  avatar: '',
})

function openTourCreate() {
  tourEditingId.value = null
  tourForm.name = ''
  tourForm.description = ''
  tourForm.registration_deadline = ''
  tourForm.registration_types = [...REGISTRATION_TYPES]
  tourForm.professions = [...PROFESSIONS]
  tourForm.avatar = ''
  tourModal.value = true
}
function openTourEdit(t) {
  tourEditingId.value = t.id
  tourForm.name = t.name
  tourForm.description = t.description || ''
  tourForm.registration_deadline = toLocalInput(t.registration_deadline)
  tourForm.registration_types = [...(t.rules?.registration_types || REGISTRATION_TYPES)]
  tourForm.professions = [...(t.rules?.professions || PROFESSIONS)]
  tourForm.avatar = t.avatar || ''
  tourModal.value = true
}

// ------- 赛事头像：本地压缩为 512px 内的 data URL 后随表单提交 -------
const avatarInput = ref(null)

function compressImage(file, maxSize = 512) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(url)
      const scale = Math.min(1, maxSize / Math.max(img.width, img.height))
      const canvas = document.createElement('canvas')
      canvas.width = Math.max(1, Math.round(img.width * scale))
      canvas.height = Math.max(1, Math.round(img.height * scale))
      canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height)
      resolve(canvas.toDataURL('image/jpeg', 0.85))
    }
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('图片读取失败'))
    }
    img.src = url
  })
}

async function onAvatarChange(e) {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) return toast('请选择图片文件', 'error')
  try {
    tourForm.avatar = await compressImage(file)
  } catch (err) {
    toast(err.message || '图片读取失败', 'error')
  }
}
async function saveTour() {
  if (!tourForm.name.trim()) return toast('请填写赛事名称', 'error')
  if (!tourForm.registration_deadline) return toast('请设置报名截止时间', 'error')
  if (!tourForm.registration_types.length) return toast('至少勾选一种报名类型', 'error')
  if (!tourForm.professions.length) return toast('至少勾选一个可选职业', 'error')
  const payload = {
    name: tourForm.name.trim(),
    description: tourForm.description.trim(),
    registration_deadline: tourForm.registration_deadline,
    rules: {
      registration_types: REGISTRATION_TYPES.filter((t) => tourForm.registration_types.includes(t)),
      professions: PROFESSIONS.filter((p) => tourForm.professions.includes(p)),
    },
    avatar: tourForm.avatar,
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

// ------- Poster：编辑规则 / 编辑公告 -------
const rulesModal = ref(false)
const rulesTour = ref(null)
const rulesForm = reactive(Object.fromEntries(RULE_KEYS.map((k) => [k, ''])))

const announceModal = ref(false)
const announceTour = ref(null)
const announceForm = reactive(Object.fromEntries(ANNOUNCE_KEYS.map((k) => [k, ''])))

function openRulesEdit(t) {
  rulesTour.value = t
  RULE_KEYS.forEach((k) => (rulesForm[k] = t.poster?.[k] || ''))
  rulesModal.value = true
}
function openAnnounceEdit(t) {
  announceTour.value = t
  ANNOUNCE_KEYS.forEach((k) => (announceForm[k] = t.poster?.[k] || ''))
  announceModal.value = true
}
// 只覆盖本次编辑的字段，保留海报其余内容
async function savePoster(tour, form, keys, doneMsg) {
  const poster = { ...blankPoster(), ...(tour.poster || {}) }
  keys.forEach((k) => (poster[k] = form[k]))
  try {
    await api.put(`/admin/tournaments/${tour.id}`, { poster })
    toast(doneMsg, 'success')
    await loadTournaments()
    return true
  } catch (e) {
    toast(e.message || '保存失败', 'error')
    return false
  }
}
async function saveRules() {
  if (await savePoster(rulesTour.value, rulesForm, RULE_KEYS, '参赛规则已保存')) rulesModal.value = false
}
async function saveAnnounce() {
  if (await savePoster(announceTour.value, announceForm, ANNOUNCE_KEYS, '比赛公告已保存')) announceModal.value = false
}
function deleteTour(t) {
  openConfirm({
    title: '删除赛事',
    message: `你确定要删除赛事「${t.name}」吗？其下所有报名记录与对阵图都会被删除，且不可撤销。`,
    confirmText: '删除',
    action: async () => {
      try {
        await api.delete(`/admin/tournaments/${t.id}`)
        toast('赛事已删除', 'info')
        if (selectedTid.value === t.id) selectedTid.value = null
        await loadTournaments()
      } catch (e) {
        toast(e.message || '删除失败', 'error')
      }
    },
  })
}

async function toggleTourVisibility(t) {
  try {
    await api.put(`/admin/tournaments/${t.id}`, { is_visible: !t.is_visible })
    toast(t.is_visible ? '赛事已隐藏' : '赛事已恢复展示', 'success')
    await loadTournaments()
  } catch (e) {
    toast(e.message || '操作失败', 'error')
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
    if (typeFilter.value) params.registration_type = typeFilter.value
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

function review(team, status) {
  if (status === 'rejected') {
    openConfirm({
      title: '驳回报名',
      message: `你确定要驳回「${team.name}」吗？`,
      confirmText: '驳回',
      showNote: true,
      note: team.review_note || '',
      notePlaceholder: '驳回原因（可选）',
      action: (note) => submitReview(team, status, note),
    })
    return
  }
  submitReview(team, status, team.review_note || '')
}

async function submitReview(team, status, note) {
  try {
    await api.patch(`/admin/teams/${team.id}/review`, { status, review_note: note })
    toast(status === 'approved' ? '已通过审核' : status === 'rejected' ? '已驳回' : '已重置为待审核', 'success')
    await loadTeams()
  } catch (e) {
    toast(e.message || '操作失败', 'error')
  }
}

function removeTeam(team) {
  openConfirm({
    title: '删除报名',
    message: `你确定要删除报名记录「${team.name}」吗？此操作不可撤销。`,
    confirmText: '删除',
    action: async () => {
      try {
        await api.delete(`/admin/teams/${team.id}`)
        toast('已删除', 'info')
        await loadTeams()
      } catch (e) {
        toast(e.message || '删除失败', 'error')
      }
    },
  })
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
  createForm.registration_type = scopeAllowedTypes.value[0]
  createForm.players.forEach((p) => {
    if (!scopeAllowedProfessions.value.includes(p.profession)) {
      p.profession = scopeAllowedProfessions.value[0]
    }
  })
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
const stages = ref([])
const approvedTeams = computed(() => teams.value.filter((t) => t.status === 'approved'))
const bracketTeamMap = computed(() => Object.fromEntries(approvedTeams.value.map((t) => [t.id, t.name])))

const STAGE_TYPE_LABEL = {
  elimination: '淘汰赛（树形）',
  pairs: '并列对决',
  swiss: '瑞士轮 / 循环积分',
  double_final: '4强双败决赛',
}

function emptyMatch() {
  return { team1: null, team2: null, winner: null, score1: null, score2: null }
}
function emptyMatches(n) {
  return Array.from({ length: n }, emptyMatch)
}

async function loadBracket() {
  if (!selectedTid.value) {
    stages.value = []
    return
  }
  try {
    const { data } = await api.get(`/admin/tournaments/${selectedTid.value}/bracket`)
    stages.value = data.stages || []
  } catch (e) {
    toast(e.message || '加载对阵图失败', 'error')
  }
}

function addStage() {
  stages.value.push({
    name: `阶段 ${stages.value.length + 1}`,
    type: 'pairs',
    note: '',
    advance: null,
    rounds: [{ name: '第 1 轮', note: '', matches: [emptyMatch()] }],
  })
}
function removeStage(si) {
  stages.value.splice(si, 1)
}
function moveStage(si, dir) {
  const target = si + dir
  if (target < 0 || target >= stages.value.length) return
  const [s] = stages.value.splice(si, 1)
  stages.value.splice(target, 0, s)
}
function onStageTypeChange(stage) {
  if (stage.type === 'swiss' && stage.advance == null) stage.advance = 4
}
function addRound(stage) {
  stage.rounds.push({ name: `第 ${stage.rounds.length + 1} 轮`, note: '', matches: [emptyMatch()] })
}
function removeRound(stage, ri) {
  stage.rounds.splice(ri, 1)
}
function addMatch(round) {
  round.matches.push(emptyMatch())
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
        matches.push({ ...emptyMatch(), team1: seeds[i * 2] ?? null, team2: seeds[i * 2 + 1] ?? null })
      } else {
        matches.push(emptyMatch())
      }
    }
    newRounds.push({ name: stageNames[count] || `${count} 强`, note: '', matches })
    first = false
    count /= 2
  }
  stages.value = [{ name: '淘汰赛', type: 'elimination', note: '', advance: null, rounds: newRounds }]
  toast(`已生成 ${size} 强对阵骨架`, 'success')
}

// 选花杯赛制：小组赛 12进6 → 复活赛 → 6强瑞士轮 → 4强双败决赛。
function generateXuanhuaTemplate() {
  const seeds = approvedTeams.value.map((t) => t.id)
  const pick = (i) => seeds[i] ?? null
  const groupMatches = Array.from({ length: 6 }, (_, i) => ({
    ...emptyMatch(),
    team1: pick(i * 2),
    team2: pick(i * 2 + 1),
  }))
  const swissPairs = ['A-F、B-E、C-D', 'A-E、F-D、B-C', 'A-D、E-C、F-B', 'A-C、D-B、E-F', 'A-B、C-F、D-E']
  stages.value = [
    {
      name: '小组赛 12进6',
      type: 'pairs',
      note: 'BO3｜模式顺序：团战 → 站点 → 夺旗｜地图随机，红蓝边抽签决定先选，每场 BO1 后交换',
      advance: null,
      rounds: [{ name: '小组赛', note: '胜者进入胜者组，败者跌入败者组', matches: groupMatches }],
    },
    {
      name: '复活赛',
      type: 'pairs',
      note: 'BO3｜模式顺序：团战 → 站点 → 夺旗｜地图随机',
      advance: null,
      rounds: [
        { name: '败者组 6进3', note: '胜者进入复活席', matches: emptyMatches(3) },
        { name: '胜者组 6进3', note: '胜者直接晋级 6 强', matches: emptyMatches(3) },
        { name: '复活对决', note: '胜者组败者 vs 复活席，决出剩余 3 个 6 强席位', matches: emptyMatches(3) },
      ],
    },
    {
      name: '6强瑞士轮排位赛',
      type: 'swiss',
      note: '歼灭 BO1｜系统随机分配编号 A-F｜每胜一场积 1 分，前 4 名晋级 4 强',
      advance: 4,
      rounds: swissPairs.map((pairing, i) => ({ name: `轮 ${i + 1}`, note: pairing, matches: emptyMatches(3) })),
    },
    {
      name: '4强淘汰赛',
      type: 'double_final',
      note: '继承瑞士轮排名：1v2、3v4｜BO3 歼灭三图都打，红蓝边抽签决定先选，每场 BO1 后交换',
      advance: null,
      rounds: [
        {
          name: '半决赛',
          note: '上：1v2，胜者进胜者组决赛、败者进败者组决赛；下：3v4，胜者进败者组决赛、败者锁定殿军',
          matches: emptyMatches(2),
        },
        { name: '败者组决赛', note: 'BO5 歼灭｜胜者进胜者组决赛，败者锁定季军', matches: emptyMatches(1) },
        { name: '胜者组决赛', note: '胜者夺得冠军，败者锁定亚军', matches: emptyMatches(1) },
      ],
    },
  ]
  toast('已生成赛制模板', 'success')
}

// Normalize editor state (empty inputs become null) before persisting.
function cleanBracket() {
  const num = (v) => (v === '' || v == null ? null : Number(v))
  return {
    stages: stages.value.map((s) => ({
      name: s.name,
      type: s.type,
      note: s.note || '',
      advance: num(s.advance),
      rounds: s.rounds.map((r) => ({
        name: r.name,
        note: r.note || '',
        matches: r.matches.map((m) => ({
          team1: m.team1 ?? null,
          team2: m.team2 ?? null,
          winner: m.winner ?? null,
          score1: num(m.score1),
          score2: num(m.score2),
        })),
      })),
    })),
  }
}

async function saveBracket() {
  try {
    await api.put(`/admin/tournaments/${selectedTid.value}/bracket`, cleanBracket())
    toast('对阵图已保存', 'success')
  } catch (e) {
    toast(e.message || '保存失败', 'error')
  }
}

// ------- Users（账号管理） -------
const users = ref([])
const usersLoading = ref(false)

async function loadUsers() {
  usersLoading.value = true
  try {
    const { data } = await api.get('/admin/users')
    users.value = data
  } catch (e) {
    toast(e.message || '加载账号失败', 'error')
  } finally {
    usersLoading.value = false
  }
}

const userModal = ref(false)
const userForm = reactive({ username: '', password: '', role: 'admin' })

function openUserCreate() {
  userForm.username = ''
  userForm.password = ''
  userForm.role = 'admin'
  userModal.value = true
}
async function saveUser() {
  if (userForm.username.trim().length < 3) return toast('用户名至少 3 个字符', 'error')
  if (userForm.password.length < 6) return toast('密码至少 6 位', 'error')
  try {
    await api.post('/admin/users', {
      username: userForm.username.trim(),
      password: userForm.password,
      role: userForm.role,
    })
    toast(userForm.role === 'admin' ? '管理员账号已创建' : '账号已创建', 'success')
    userModal.value = false
    await loadUsers()
  } catch (e) {
    toast(e.message || '创建失败', 'error')
  }
}

async function submitRole(u, role) {
  try {
    await api.patch(`/admin/users/${u.id}/role`, { role })
    toast(role === 'admin' ? `已将「${u.username}」设为管理员` : `已取消「${u.username}」的管理员身份`, 'success')
    await loadUsers()
  } catch (e) {
    toast(e.message || '操作失败', 'error')
  }
}
function setRole(u, role) {
  if (role !== 'admin') {
    openConfirm({
      title: '取消管理员',
      message: `你确定要取消「${u.username}」的管理员身份吗？该账号将变为普通用户。`,
      confirmText: '取消管理员',
      action: () => submitRole(u, role),
    })
    return
  }
  submitRole(u, role)
}

// React to tournament switch (for teams & bracket tabs).
watch(selectedTid, async () => {
  await Promise.all([loadTeams(), loadBracket()])
})

watch(tab, (v) => {
  if (v === 'users') loadUsers()
})

onMounted(async () => {
  await loadTournaments()
  await Promise.all([loadTeams(), loadBracket()])
})
</script>

<template>
  <div class="container admin-page">
    <PageHeading title="赛事管理中心" description="管理每一次集结，从赛事发布、报名审核，到冠军诞生。" icon="shield"><span class="admin-identity"><Icon name="user" :size="16" />{{ auth.user?.username }} · 管理员</span></PageHeading>
    <header class="page-head">
      <div class="segmented admin-tabs" aria-label="管理功能">
        <button :aria-pressed="tab === 'tournaments'" :class="{ active: tab === 'tournaments' }" @click="tab = 'tournaments'"><Icon name="trophy" :size="17" />赛事管理</button>
        <button :aria-pressed="tab === 'teams'" :class="{ active: tab === 'teams' }" @click="tab = 'teams'"><Icon name="users" :size="17" />报名管理</button>
        <button :aria-pressed="tab === 'bracket'" :class="{ active: tab === 'bracket' }" @click="tab = 'bracket'"><Icon name="flag" :size="17" />对阵图配置</button>
        <button :aria-pressed="tab === 'users'" :class="{ active: tab === 'users' }" @click="tab = 'users'"><Icon name="user" :size="17" />账号管理</button>
      </div>
    </header>

    <!-- Tournament scope selector (teams & bracket tabs) -->
    <div v-if="tab === 'teams' || tab === 'bracket'" class="row scope-bar">
      <label class="scope-label">当前赛事</label>
      <select v-model="selectedTid" class="scope-select">
        <option v-for="t in tournaments" :key="t.id" :value="t.id">{{ t.name }}</option>
      </select>
      <span v-if="selectedTournament" class="badge" :class="selectedTournament.results_public ? 'approved' : 'pending'">
        {{ selectedTournament.results_public ? '已截止' : '报名中' }}
      </span>
      <span v-if="selectedTournament" class="muted small">截止：{{ formatDeadline(selectedTournament.registration_deadline) }}</span>
    </div>

    <Transition name="tab-swap" mode="out-in">

    <!-- ===================== TOURNAMENTS ===================== -->
    <div v-if="tab === 'tournaments'" key="tournaments">
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
            <tr v-if="tourLoading && !tournaments.length"><td colspan="6"><Spinner label="加载中" /></td></tr>
            <tr v-else-if="!tournaments.length"><td colspan="6" class="table-empty">暂无赛事</td></tr>
            <tr v-for="t in tournaments" :key="t.id">
              <td class="muted">{{ t.id }}</td>
              <td><strong>{{ t.name }}</strong><div v-if="t.description" class="muted tiny">{{ t.description }}</div></td>
              <td>{{ formatDeadline(t.registration_deadline) }}</td>
              <td>
                <div class="actions">
                  <span class="badge" :class="t.results_public ? 'approved' : 'pending'">
                    {{ t.results_public ? '已截止' : '报名中' }}
                  </span>
                  <span v-if="!t.is_visible" class="badge rejected">已隐藏</span>
                </div>
              </td>
              <td>{{ t.team_count }}</td>
              <td>
                <div class="actions">
                  <button class="btn tint sm" @click="openTourEdit(t)">编辑</button>
                  <button class="btn tint sm" @click="openRulesEdit(t)">编辑规则</button>
                  <button class="btn tint sm" @click="openAnnounceEdit(t)">编辑公告</button>
                  <button class="btn tint sm" @click="toggleTourVisibility(t)">
                    {{ t.is_visible ? '隐藏' : '显示' }}
                  </button>
                  <button class="btn tint danger sm" @click="deleteTour(t)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ===================== TEAMS ===================== -->
    <div v-else-if="tab === 'teams'" key="teams">
      <div class="row toolbar">
        <label class="muted">筛选状态：</label>
        <select v-model="filter" style="width: 140px" @change="loadTeams">
          <option value="">全部</option>
          <option value="pending">审核中</option>
          <option value="approved">已通过</option>
          <option value="rejected">未通过</option>
        </select>
        <label class="muted">类型：</label>
        <select v-model="typeFilter" style="width: 140px" @change="loadTeams">
          <option value="">全部</option>
          <option value="team">战队报名</option>
          <option value="solo">个人报名</option>
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
            <tr v-if="loading"><td colspan="10"><Spinner label="加载中" /></td></tr>
            <tr v-else-if="!teams.length"><td colspan="10" class="table-empty">暂无数据</td></tr>
            <tr v-for="t in teams" :key="t.id">
              <td class="muted">{{ t.id }}</td>
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
                  <button v-if="t.status !== 'approved'" class="btn tint success sm" @click="review(t, 'approved')">通过</button>
                  <button v-if="t.status !== 'rejected'" class="btn tint danger sm" @click="review(t, 'rejected')">驳回</button>
                  <button class="btn tint sm" @click="openEdit(t)">编辑</button>
                  <button class="btn tint danger sm" @click="removeTeam(t)">删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ===================== USERS ===================== -->
    <div v-else-if="tab === 'users'" key="users">
      <div class="row toolbar">
        <span class="muted">共 {{ users.length }} 个账号</span>
        <span class="spacer"></span>
        <button class="btn ghost sm" @click="loadUsers">刷新</button>
        <button class="btn sm" @click="openUserCreate">+ 新增账号</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>用户名</th><th>角色</th><th>注册时间</th><th>报名数</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-if="usersLoading && !users.length"><td colspan="6"><Spinner label="加载中" /></td></tr>
            <tr v-else-if="!users.length"><td colspan="6" class="table-empty">暂无账号</td></tr>
            <tr v-for="u in users" :key="u.id">
              <td class="muted">{{ u.id }}</td>
              <td>
                <strong>{{ u.username }}</strong>
                <span v-if="u.id === auth.user?.id" class="muted tiny">（当前登录）</span>
              </td>
              <td>
                <span class="role-badge" :class="u.role">{{ u.role === 'admin' ? '管理员' : '普通用户' }}</span>
              </td>
              <td class="muted">{{ formatDeadline(u.created_at) }}</td>
              <td>{{ u.team_count }}</td>
              <td>
                <div class="actions">
                  <button
                    v-if="u.role !== 'admin'"
                    class="btn tint sm"
                    @click="setRole(u, 'admin')"
                  >设为管理员</button>
                  <button
                    v-else
                    class="btn tint danger sm"
                    :disabled="u.id === auth.user?.id"
                    :title="u.id === auth.user?.id ? '不能取消自己的管理员身份' : ''"
                    @click="setRole(u, 'user')"
                  >取消管理员</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ===================== BRACKET ===================== -->
    <div v-else key="bracket">
      <div class="panel">
        <div class="row">
          <h2 style="margin: 0">对阵图配置</h2>
          <span class="spacer"></span>
          <button class="btn ghost sm" @click="generateXuanhuaTemplate">生成赛制模板</button>
          <button class="btn ghost sm" @click="generateSkeleton">按已通过报名自动生成</button>
          <button class="btn ghost sm" @click="addStage">+ 添加阶段</button>
          <button class="btn sm" @click="saveBracket">保存对阵图</button>
        </div>
        <p class="muted bracket-hint">
          对阵图按「阶段」组织：淘汰赛（树形连接线）、并列对决（无连接线）、瑞士轮（自动积分榜）、4强双败决赛（自动名次）。
          仅「已通过」的报名可被选择（当前 {{ approvedTeams.length }} 条）。
        </p>

        <div v-if="!stages.length" class="muted">尚未添加任何阶段。</div>

        <div v-for="(stage, si) in stages" :key="si" class="editor-stage card">
          <div class="row stage-row">
            <input v-model="stage.name" class="stage-name-input" placeholder="阶段名称" />
            <select v-model="stage.type" class="stage-type-sel" @change="onStageTypeChange(stage)">
              <option v-for="(lbl, val) in STAGE_TYPE_LABEL" :key="val" :value="val">{{ lbl }}</option>
            </select>
            <label v-if="stage.type === 'swiss'" class="muted tiny adv-label">
              晋级名额
              <input v-model.number="stage.advance" type="number" min="1" class="adv-input" />
            </label>
            <span class="spacer"></span>
            <button class="btn tint sm" :disabled="si === 0" @click="moveStage(si, -1)">↑</button>
            <button class="btn tint sm" :disabled="si === stages.length - 1" @click="moveStage(si, 1)">↓</button>
            <button class="btn tint sm" @click="addRound(stage)">+ 轮次</button>
            <button class="btn tint danger sm" @click="removeStage(si)">删除阶段</button>
          </div>
          <input v-model="stage.note" class="note-input" placeholder="阶段说明（可选，展示在阶段标题下，可写 BO 数、模式顺序等规则）" />

          <div class="editor-rounds">
            <div v-for="(round, ri) in stage.rounds" :key="ri" class="editor-round card">
              <div class="row">
                <input v-model="round.name" class="round-name" placeholder="轮次名称" />
                <span class="spacer"></span>
                <button class="btn tint sm" @click="addMatch(round)">+ 对局</button>
                <button class="btn tint danger sm" @click="removeRound(stage, ri)">删除轮次</button>
              </div>
              <input v-model="round.note" class="note-input" placeholder="轮次说明（可选）" />
              <div v-for="(m, mi) in round.matches" :key="mi" class="editor-match">
                <div class="mrow">
                  <select v-model="m.team1">
                    <option :value="null">— 待定 —</option>
                    <option v-for="t in approvedTeams" :key="t.id" :value="t.id">{{ t.name }}</option>
                  </select>
                  <input v-model.number="m.score1" type="number" min="0" class="score-input" placeholder="比分" />
                  <span class="vs">VS</span>
                  <input v-model.number="m.score2" type="number" min="0" class="score-input" placeholder="比分" />
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
                  <button class="btn tint danger sm" @click="removeMatch(round, mi)">移除</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="panel" style="margin-top: 1.5rem">
        <h3>预览</h3>
        <Bracket :stages="stages" :team-map="bracketTeamMap" />
      </div>
    </div>

    </Transition>

    <!-- ===================== TOURNAMENT MODAL ===================== -->
    <Transition name="modal-fade">
      <div v-if="tourModal" class="modal-backdrop" @click.self="tourModal = false">
        <div class="modal tour-modal">
          <div class="modal-head">
            <h2>{{ tourEditingId ? '编辑赛事' : '新增赛事' }}</h2>
            <button class="icon-close" aria-label="关闭" @click="tourModal = false">✕</button>
          </div>
          <div class="field"><label for="admin-field-1">赛事名称 *</label><input id="admin-field-1" v-model="tourForm.name" maxlength="128" placeholder="例如：百变兵团第二届赛事" /></div>
          <div class="field">
            <label>赛事头像</label>
            <div class="avatar-edit">
              <img v-if="tourForm.avatar" :src="tourForm.avatar" alt="赛事头像预览" class="avatar-preview" />
              <div v-else class="avatar-preview avatar-empty">默认</div>
              <div class="avatar-btns">
                <button type="button" class="btn tint sm" @click="avatarInput?.click()">上传图片</button>
                <button v-if="tourForm.avatar" type="button" class="btn tint danger sm" @click="tourForm.avatar = ''">移除</button>
              </div>
              <input ref="avatarInput" type="file" accept="image/*" class="avatar-file" @change="onAvatarChange" />
            </div>
            <p class="muted tiny" style="margin-top:0.35rem">显示在赛事浏览卡片上，建议正方形图片，上传时会自动压缩；不上传则使用默认头像。</p>
          </div>
          <div class="field"><label for="admin-field-2">赛事简介</label><textarea id="admin-field-2" v-model="tourForm.description" maxlength="2000" placeholder="可选"></textarea></div>
          <div class="field">
            <label for="admin-field-3">报名截止时间 *</label>
            <input id="admin-field-3" v-model="tourForm.registration_deadline" type="datetime-local" />
            <p class="muted tiny" style="margin-top:0.35rem">截止后才会向所有人公开参赛名单与对阵图；截止前用户只能看到自己的报名。</p>
          </div>
          <div class="field">
            <label>报名类型 *</label>
            <div class="check-row">
              <label v-for="rt in REGISTRATION_TYPES" :key="rt" class="check-item">
                <input v-model="tourForm.registration_types" type="checkbox" :value="rt" />
                {{ REGISTRATION_LABEL[rt] }}
              </label>
            </div>
            <p class="muted tiny" style="margin-top:0.35rem">例如 SOLO 赛只勾选「个人报名」。</p>
          </div>
          <div class="field">
            <label>可选职业 *</label>
            <div class="check-row">
              <label v-for="prof in PROFESSIONS" :key="prof" class="check-item">
                <input v-model="tourForm.professions" type="checkbox" :value="prof" />
                <span class="dot" :style="{ background: `var(--prof-${prof})` }"></span>
                {{ prof }}
              </label>
            </div>
            <p class="muted tiny" style="margin-top:0.35rem">报名时只能选择勾选的职业，例如三职业赛不勾选「生化」。</p>
          </div>
          <p class="muted tiny">参赛规则与比赛公告请在赛事列表中通过「编辑规则」「编辑公告」按钮单独配置。</p>

          <button class="btn modal-submit" @click="saveTour">
            {{ tourEditingId ? '保存修改' : '创建赛事' }}
          </button>
        </div>
      </div>
    </Transition>

    <!-- ===================== RULES MODAL ===================== -->
    <Transition name="modal-fade">
      <div v-if="rulesModal" class="modal-backdrop" @click.self="rulesModal = false">
        <div class="modal tour-modal">
          <div class="modal-head">
            <h2>编辑规则 · {{ rulesTour?.name }}</h2>
            <button class="icon-close" aria-label="关闭" @click="rulesModal = false">✕</button>
          </div>
          <p class="muted tiny" style="margin:0 0 0.9rem">以下内容将自动生成为比赛详情海报，用户在「比赛详情」中查看。每行一条，留空则不显示该项。</p>

          <h4 class="poster-group">参赛规则</h4>
          <div class="field"><label for="admin-field-4">比赛形式</label><textarea id="admin-field-4" v-model="rulesForm.format" rows="1" placeholder="例如：5v5"></textarea></div>
          <div class="field"><label for="admin-field-5">职业限制</label><textarea id="admin-field-5" v-model="rulesForm.profession_limit" placeholder="每行一条，例如：&#10;各职业不得超过两名&#10;若没有生化，可换成一个非突击职业"></textarea></div>
          <div class="field"><label for="admin-field-6">模式限制</label><textarea id="admin-field-6" v-model="rulesForm.mode_limit" placeholder="例如：预选赛模式为 占点 夺旗 团战 纯随机"></textarea></div>
          <div class="field"><label for="admin-field-7">药物及道具限制</label><textarea id="admin-field-7" v-model="rulesForm.item_limit" placeholder="每行一条"></textarea></div>
          <div class="field"><label for="admin-field-8">装备限制</label><textarea id="admin-field-8" v-model="rulesForm.equipment_limit" placeholder="每行一条"></textarea></div>
          <div class="field"><label for="admin-field-9">其他限制</label><textarea id="admin-field-9" v-model="rulesForm.other_limit" placeholder="例如：其余以赛事官方为准"></textarea></div>

          <h4 class="poster-group">官方奖励</h4>
          <div class="field"><label for="admin-field-10">冠军奖励</label><textarea id="admin-field-10" v-model="rulesForm.reward_champion" rows="2" placeholder="例如：三把 ROG 夜魔键盘 价值 5000 元（队伍自行分配）"></textarea></div>
          <div class="field"><label for="admin-field-11">亚军奖励</label><textarea id="admin-field-11" v-model="rulesForm.reward_runner_up" rows="2" placeholder="例如：三把龙鳞 2 鼠标 价值 3000 元"></textarea></div>
          <div class="field"><label for="admin-field-12">季军奖励</label><textarea id="admin-field-12" v-model="rulesForm.reward_third" rows="2" placeholder="例如：每人 1500 兑换卷"></textarea></div>
          <div class="field"><label for="admin-field-13">殿军奖励</label><textarea id="admin-field-13" v-model="rulesForm.reward_fourth" rows="2" placeholder="例如：每人 500 兑换卷"></textarea></div>
          <div class="field"><label for="admin-field-14">其他奖励</label><textarea id="admin-field-14" v-model="rulesForm.reward_other" rows="2" placeholder="例如：更有众多参与奖神秘奖等待抽选"></textarea></div>

          <button class="btn modal-submit" @click="saveRules">保存规则</button>
        </div>
      </div>
    </Transition>

    <!-- ===================== ANNOUNCEMENT MODAL ===================== -->
    <Transition name="modal-fade">
      <div v-if="announceModal" class="modal-backdrop" @click.self="announceModal = false">
        <div class="modal tour-modal">
          <div class="modal-head">
            <h2>编辑公告 · {{ announceTour?.name }}</h2>
            <button class="icon-close" aria-label="关闭" @click="announceModal = false">✕</button>
          </div>
          <p class="muted tiny" style="margin:0 0 0.9rem">以下内容将自动生成为参赛公告海报，用户在「比赛公告」中查看。</p>

          <div class="field">
            <label for="admin-field-15">公告内容</label>
            <textarea id="admin-field-15"
              v-model="announceForm.announcement"
              rows="8"
              placeholder="每行一条，用 **文字** 高亮重点，例如：&#10;本活动绝对**公平免费**&#10;面向**全服玩家**，欢迎大家踊跃报名&#10;**单人**也可以报名&#10;满**16支队伍**开赛"
            ></textarea>
            <p class="muted tiny" style="margin-top:0.35rem">每行生成一条带序号的公告；两个星号包裹的文字会以金色高亮显示。</p>
          </div>
          <div class="field">
            <label for="admin-field-16">底部标语</label>
            <input id="admin-field-16" v-model="announceForm.announcement_footer" maxlength="200" placeholder="例如：快来组队参赛，赢取丰厚奖励！" />
            <p class="muted tiny" style="margin-top:0.35rem">显示在公告底部的金色横幅，留空则不显示。</p>
          </div>

          <button class="btn modal-submit" @click="saveAnnounce">保存公告</button>
        </div>
      </div>
    </Transition>

    <!-- ===================== CREATE USER MODAL ===================== -->
    <Transition name="modal-fade">
      <div v-if="userModal" class="modal-backdrop" @click.self="userModal = false">
        <div class="modal confirm-modal">
          <div class="modal-head">
            <h2>新增账号</h2>
            <button class="icon-close" aria-label="关闭" @click="userModal = false">✕</button>
          </div>
          <div class="field">
            <label for="admin-field-17">用户名 *</label>
            <input id="admin-field-17" v-model="userForm.username" maxlength="64" placeholder="至少 3 个字符" autocomplete="off" />
          </div>
          <div class="field">
            <label for="admin-field-18">初始密码 *</label>
            <input id="admin-field-18" v-model="userForm.password" type="password" maxlength="128" placeholder="至少 6 位" autocomplete="new-password" />
            <p class="muted tiny" style="margin-top:0.35rem">请将初始密码告知对方，登录后可在「账号设置」中自行修改。</p>
          </div>
          <div class="field">
            <label for="admin-field-19">角色</label>
            <select id="admin-field-19" v-model="userForm.role">
              <option value="admin">管理员</option>
              <option value="user">普通用户</option>
            </select>
          </div>
          <button class="btn modal-submit" @click="saveUser">创建账号</button>
        </div>
      </div>
    </Transition>

    <!-- ===================== CONFIRM DIALOG ===================== -->
    <Transition name="modal-fade">
      <div v-if="confirmState.open" class="modal-backdrop" @click.self="confirmState.open = false">
        <div class="modal confirm-modal">
          <div class="modal-head">
            <h2>{{ confirmState.title }}</h2>
            <button class="icon-close" aria-label="关闭" @click="confirmState.open = false">✕</button>
          </div>
          <p class="confirm-message">{{ confirmState.message }}</p>
          <div v-if="confirmState.showNote" class="field">
            <textarea v-model="confirmState.note" rows="2" :placeholder="confirmState.notePlaceholder"></textarea>
          </div>
          <div class="confirm-actions">
            <button class="btn ghost" @click="confirmState.open = false">取消</button>
            <button class="btn danger" @click="doConfirm">{{ confirmState.confirmText }}</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ===================== CREATE TEAM MODAL ===================== -->
    <Transition name="modal-fade">
      <div v-if="creating" class="modal-backdrop" @click.self="creating = false">
        <div class="modal">
          <div class="modal-head">
            <h2>新增报名</h2>
            <button class="icon-close" aria-label="关闭" @click="creating = false">✕</button>
          </div>
          <p class="muted">录入到「{{ selectedTournament?.name }}」；可直接指定初始审核状态。</p>
          <div class="field">
            <label for="admin-field-20">报名类型</label>
            <select id="admin-field-20" v-model="createForm.registration_type" class="status-select">
              <option v-for="rt in scopeAllowedTypes" :key="rt" :value="rt">{{ REGISTRATION_LABEL[rt] }}</option>
            </select>
          </div>
          <template v-if="!createIsSolo">
            <div class="field"><label for="admin-field-21">队伍名称 *</label><input id="admin-field-21" v-model="createForm.name" maxlength="128" placeholder="例如：烈焰星辰" /></div>
            <div class="field"><label for="admin-field-22">队长 *</label><input id="admin-field-22" v-model="createForm.captain" maxlength="64" placeholder="队长称呼" /></div>
          </template>
          <template v-else>
            <div class="field"><label for="admin-field-23">称呼 *</label><input id="admin-field-23" v-model="createForm.players[0].nickname" maxlength="64" placeholder="个人报名称呼" /></div>
            <div class="field">
              <label for="admin-field-24">职业 *</label>
              <select id="admin-field-24" v-model="createForm.players[0].profession" class="status-select">
                <option v-for="prof in scopeAllowedProfessions" :key="prof" :value="prof">{{ prof }}</option>
              </select>
            </div>
          </template>
          <div class="field"><label for="admin-field-25">联系方式 *</label><input id="admin-field-25" v-model="createForm.contact" maxlength="128" placeholder="QQ / 微信 / 手机号" /></div>
          <div class="field">
            <label for="admin-field-26">初始状态</label>
            <select id="admin-field-26" v-model="createForm.status" class="status-select">
              <option value="approved">已通过</option>
              <option value="pending">审核中</option>
              <option value="rejected">未通过</option>
            </select>
          </div>
          <template v-if="!createIsSolo">
            <h4>参赛阵容 *</h4>
            <RosterEditor v-model="createForm.players" :professions="scopeAllowedProfessions" />
          </template>
          <div class="field" style="margin-top: 1rem"><label for="admin-field-27">作战宣言</label><textarea id="admin-field-27" v-model="createForm.declaration" maxlength="2000"></textarea></div>
          <button class="btn modal-submit" :disabled="!canCreate" @click="saveCreate">
            新增报名
          </button>
        </div>
      </div>
    </Transition>

    <!-- ===================== EDIT MODAL ===================== -->
    <Transition name="modal-fade">
      <div v-if="editing" class="modal-backdrop" @click.self="editing = null">
        <div class="modal">
          <div class="modal-head">
            <div class="modal-title-group">
              <h2>编辑战队 · {{ editing.name }}</h2>
              <span class="chip sm type-chip">{{ REGISTRATION_LABEL[editForm.registration_type] || '报名' }}</span>
            </div>
            <button class="icon-close" aria-label="关闭" @click="editing = null">✕</button>
          </div>
          <div class="field">
            <label for="admin-field-28">报名类型</label>
            <select id="admin-field-28" v-model="editForm.registration_type" class="status-select">
              <option v-for="rt in scopeAllowedTypes" :key="rt" :value="rt">{{ REGISTRATION_LABEL[rt] }}</option>
            </select>
          </div>
          <template v-if="!editIsSolo">
            <div class="field"><label for="admin-field-29">队伍名称</label><input id="admin-field-29" v-model="editForm.name" /></div>
            <div class="field"><label for="admin-field-30">队长</label><input id="admin-field-30" v-model="editForm.captain" /></div>
            <h4>参赛阵容</h4>
            <RosterEditor v-model="editForm.players" :professions="scopeAllowedProfessions" />
          </template>
          <template v-else>
            <div class="field"><label for="admin-field-31">称呼</label><input id="admin-field-31" v-model="editForm.players[0].nickname" /></div>
            <div class="field">
              <label for="admin-field-32">职业</label>
              <select id="admin-field-32" v-model="editForm.players[0].profession" class="status-select">
                <option v-for="prof in scopeAllowedProfessions" :key="prof" :value="prof">{{ prof }}</option>
              </select>
            </div>
          </template>
          <div class="field"><label for="admin-field-33">联系方式</label><input id="admin-field-33" v-model="editForm.contact" maxlength="128" /></div>
          <div class="field" style="margin-top: 1rem"><label for="admin-field-34">作战宣言</label><textarea id="admin-field-34" v-model="editForm.declaration"></textarea></div>
          <button class="btn modal-submit" :disabled="!editIsSolo && editValidation.errors.length > 0" @click="saveEdit">
            保存修改
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.admin-page { max-width: 1370px; }
.admin-identity { display: inline-flex; align-items: center; gap: .4rem; color: #5d6c7c; font-size: .8rem; }
.page-head { margin-bottom: 1.5rem; }
.admin-tabs { display: flex; gap: .4rem; width: 100%; border-radius: 9px; background: #fff; border: 1px solid var(--border); padding: .5rem; }
.admin-tabs button { display: inline-flex; align-items: center; justify-content: center; gap: .6rem; padding: .75rem 1.5rem; }
.scope-bar { padding: 1rem 1.2rem; margin: 1rem 0; border-radius: 8px; background: #e7edf2; }
.scope-label { color: #4f6375; font-size: .83rem; font-weight: 600; }
.scope-select { width: 280px; background: #fff; }
.toolbar { margin: 1.3rem 0 1rem; font-size: .83rem; }
.prof-mini { display: flex; gap: .3rem; margin-bottom: .3rem; }
.chip.sm { font-size: .69rem; padding: .12rem .4rem; }
.tiny { font-size: .73rem; }
.small { font-size: .79rem; }
.declaration-cell { max-width: 220px; color: var(--muted); overflow-wrap: anywhere; }
td strong { display: inline-block; max-width: 18em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; vertical-align: bottom; }
.actions { display: flex; gap: .4rem; flex-wrap: wrap; min-width: 140px; }
.bracket-hint { font-size: .83rem; margin: 1rem 0 1.5rem; }
.editor-stage { margin-top: 1.5rem; padding: 1.3rem 0 0; border: 0; border-top: 1px solid var(--border); border-radius: 0; background: transparent; }
.stage-row { flex-wrap: wrap; }
.stage-name-input { width: 210px; font-weight: 700; }
.stage-type-sel { width: 170px; }
.adv-label { display: inline-flex; align-items: center; gap: .4rem; white-space: nowrap; }
.adv-input { width: 64px; }
.note-input { width: 100%; margin-top: .65rem; font-size: .8rem; background: #f9fafb; }
.editor-rounds { display: flex; gap: 1.3rem; overflow-x: auto; padding: 1rem 0; align-items: flex-start; -webkit-overflow-scrolling: touch; }
.editor-round { min-width: 320px; width: 360px; flex: none; background: transparent; border: 0; border-radius: 0; padding: 0 1.3rem 0 0; border-right: 1px solid var(--border); }
.editor-round:last-child { border-right: 0; }
.editor-round .note-input { margin-top: .5rem; }
.round-name { width: 140px; font-weight: 600; }
.score-input { width: 56px; text-align: center; padding-inline: .25rem; font-variant-numeric: tabular-nums; }
.editor-match { background: #eef2f6; border-radius: 7px; padding: .75rem; margin-top: .8rem; }
.mrow { display: flex; align-items: center; gap: .4rem; margin-bottom: .5rem; }
.mrow:last-child { margin-bottom: 0; }
.vs { color: #5c6d7e; font-weight: 750; font-size: .65rem; flex: none; }
.winner-sel { width: 130px; }
.tour-modal { width: min(600px,100%); }
.confirm-modal { width: min(440px,100%); }
.role-badge { display: inline-block; padding: .2rem .55rem; border-radius: 4px; font-size: .73rem; font-weight: 600; background: #edf1f5; color: #536779; }
.role-badge.admin { background: var(--accent-soft); color: var(--primary); }
.confirm-message { margin: 0 0 1.2rem; line-height: 1.8; }
.confirm-actions { display: flex; justify-content: flex-end; gap: .6rem; margin-top: 1.3rem; }
.confirm-actions .btn { min-width: 88px; }
.modal-head { display: flex; align-items: center; justify-content: space-between; gap: .8rem; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.modal-head h2 { margin: 0; font-size: 1.3rem; }
.modal-title-group { display: flex; align-items: center; gap: .6rem; flex-wrap: wrap; min-width: 0; }
.icon-close { flex: none; width: 36px; height: 36px; border: 1px solid var(--border); border-radius: 6px; background: #f4f6f8; color: var(--muted); font-size: .85rem; line-height: 1; cursor: pointer; display: grid; place-items: center; transition: background .18s; }
.icon-close:hover { background: #e7ecf1; color: var(--text); }
.modal-submit { width: 100%; margin-top: .6rem; min-height: 46px; }
.avatar-edit { display: flex; align-items: center; gap: 1rem; }
.avatar-preview { width: 70px; height: 70px; border-radius: 8px; object-fit: cover; border: 1px solid var(--border); flex: none; }
.avatar-empty { display: grid; place-items: center; color: var(--muted); font-size: .75rem; background: var(--bg-2); }
.avatar-btns { display: flex; gap: .4rem; flex-wrap: wrap; }
.avatar-file { display: none; }
.check-row { display: flex; gap: .8rem 1.2rem; flex-wrap: wrap; }
.check-item { display: inline-flex; align-items: center; gap: .5rem; font-size: .86rem; cursor: pointer; user-select: none; min-height: 30px; }
.check-item input[type=checkbox] { width: 17px; margin: 0; }
.check-item .dot { width: 7px; height: 7px; border-radius: 50%; }
.poster-group { margin: 1.5rem 0 1rem; padding-top: 1rem; border-top: 1px solid var(--border); font-size: .9rem; color: var(--primary); }
.status-select { width: 200px; }
.tab-swap-enter-active, .tab-swap-leave-active { transition: opacity .15s; }
.tab-swap-enter-from, .tab-swap-leave-to { opacity: 0; }
@media(max-width:760px) { .admin-tabs { overflow-x: auto; gap: .15rem; scrollbar-width: none; } .admin-tabs button { flex: 1; padding: .65rem .8rem; gap: .35rem; font-size: .76rem; } .admin-tabs .ui-icon { display: none; } .scope-bar { padding: .9rem; } .scope-label,.scope-select { width: 100%; } .toolbar { align-items: stretch; } .toolbar label,.toolbar select { width: 100% !important; } .toolbar .btn { flex: 1; } .actions { min-width: 160px; } .actions .btn { min-width: 65px; flex: 1; } .declaration-cell { min-width: 160px; } .editor-round { min-width: 280px; width: 310px; } .stage-name-input,.stage-type-sel { width: 100%; } .editor-match .mrow { display: grid; grid-template-columns: minmax(0,1fr) 50px; } .editor-match .vs { grid-column: 1/-1; text-align: center; } .editor-match .mrow > select:last-child { grid-column: 1; grid-row: 3; } .score-input { width: 50px; } .winner-row { display: flex !important; flex-wrap: wrap; } .winner-sel,.status-select { width: 100%; } .editor-match .winner-sel { width: 120px; } }
@media(max-width:380px) { .admin-tabs button { padding-inline: .55rem; font-size: .72rem; } }
</style>
