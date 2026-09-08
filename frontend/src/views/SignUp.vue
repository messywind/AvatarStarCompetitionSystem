<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import api from '../api'
import { toast } from '../toast'
import { validateRoster, PROFESSIONS } from '../roster'
import { formatDeadline, countdown } from '../time'
import RosterEditor from '../components/RosterEditor.vue'
import Spinner from '../components/Spinner.vue'
import signupGroupQrcode from '../assets/signup-group-qrcode.jpg'
import PageHeading from '../components/PageHeading.vue'
import Icon from '../components/Icon.vue'
import teamBattle from '../assets/game/team-battle.webp'

const STATUS_LABEL = { pending: '审核中', approved: '已通过', rejected: '未通过' }

function blankRoster() {
  return [
    { nickname: '', profession: '突击', is_substitute: false },
    { nickname: '', profession: '生化', is_substitute: false },
    { nickname: '', profession: '重装', is_substitute: false },
    { nickname: '', profession: '护卫', is_substitute: false },
    { nickname: '', profession: '突击', is_substitute: false },
  ]
}

const REGISTRATION_LABEL = { team: '战队报名', solo: '个人报名' }

const form = reactive({
  registrationType: 'team',
  name: '',
  captain: '',
  contact: '',
  declaration: '',
  players: blankRoster(),
  soloNickname: '',
  soloProfession: '突击',
})
const submitting = ref(false)
const booting = ref(true)
const bootError = ref('')
const myTeams = ref([])
const tournaments = ref([])
const selectedTid = ref(null)
const showGroupDialog = ref(false)

const openTournaments = computed(() => tournaments.value.filter((t) => t.registration_open))
const selectedTournament = computed(() => tournaments.value.find((t) => t.id === selectedTid.value))
const tournamentName = (id) => tournaments.value.find((t) => t.id === id)?.name || `#${id}`

// 每个赛事可单独限制报名类型与职业（如 SOLO 赛只开放个人报名、部分职业）
const allowedTypes = computed(
  () => selectedTournament.value?.rules?.registration_types || ['team', 'solo']
)
const allowedProfessions = computed(
  () => selectedTournament.value?.rules?.professions || PROFESSIONS
)

// 切换赛事后，把表单里不被该赛事允许的选择重置为允许值
watch([allowedTypes, allowedProfessions], ([types, profs]) => {
  if (!types.includes(form.registrationType)) form.registrationType = types[0]
  if (!profs.includes(form.soloProfession)) form.soloProfession = profs[0]
  form.players.forEach((p) => {
    if (!profs.includes(p.profession)) p.profession = profs[0]
  })
})

const isSolo = computed(() => form.registrationType === 'solo')
const validation = computed(() => validateRoster(form.players))
const canSubmit = computed(() => {
  if (!selectedTid.value) return false
  if (!form.contact.trim()) return false
  if (isSolo.value) return !!form.soloNickname.trim() && !!form.soloProfession
  return !!form.name.trim() && !!form.captain.trim() && validation.value.errors.length === 0
})

function resetForm() {
  form.registrationType = allowedTypes.value[0]
  form.name = ''
  form.captain = ''
  form.contact = ''
  form.declaration = ''
  form.players = blankRoster()
  form.soloNickname = ''
  form.soloProfession = allowedProfessions.value[0]
}

async function loadTournaments() {
  const { data } = await api.get('/public/tournaments')
  tournaments.value = data
  const open = data.filter((t) => t.registration_open)
  if (open.length && !open.some((t) => t.id === selectedTid.value)) {
    selectedTid.value = open[0].id
  }
}

async function loadMine() {
  try {
    const { data } = await api.get('/teams/mine')
    myTeams.value = data
  } catch (e) {
    toast(e.message || '加载失败', 'error')
  }
}

async function submit() {
  if (!canSubmit.value) {
    toast('请先选择赛事并修正表单中的问题', 'error')
    return
  }
  submitting.value = true
  try {
    const players = isSolo.value
      ? [
          {
            nickname: form.soloNickname.trim(),
            profession: form.soloProfession,
            is_substitute: false,
          },
        ]
      : form.players.map((p) => ({
          nickname: p.nickname.trim(),
          profession: p.profession,
          is_substitute: p.is_substitute,
        }))
    await api.post('/teams', {
      tournament_id: selectedTid.value,
      registration_type: isSolo.value ? 'solo' : 'team',
      name: isSolo.value ? form.soloNickname.trim() : form.name.trim(),
      captain: isSolo.value ? form.soloNickname.trim() : form.captain.trim(),
      contact: form.contact.trim(),
      declaration: form.declaration.trim(),
      players,
    })
    toast('报名提交成功，等待管理员审核', 'success')
    resetForm()
    await loadMine()
    showGroupDialog.value = true
  } catch (e) {
    toast(e.message || '提交失败', 'error')
  } finally {
    submitting.value = false
  }
}

async function withdraw(team) {
  if (!confirm(`确定撤回报名「${team.name}」吗？`)) return
  try {
    await api.delete(`/teams/${team.id}`)
    toast('已撤回', 'info')
    await loadMine()
  } catch (e) {
    toast(e.message || '撤回失败', 'error')
  }
}

function professionCounts(players) {
  const c = Object.fromEntries(PROFESSIONS.map((p) => [p, 0]))
  players.filter((p) => !p.is_substitute).forEach((p) => (c[p.profession] += 1))
  return c
}

async function boot() {
  booting.value = true
  bootError.value = ''
  try {
    await Promise.all([loadTournaments(), loadMine()])
  } catch (e) {
    bootError.value = e.message || '赛事加载失败，请重试'
  } finally {
    booting.value = false
  }
}
onMounted(boot)
</script>

<template>
  <div class="container">
    <PageHeading title="赛事报名" description="整队出征，或以个人身份加入。填写参赛信息，准备你的下一场精彩对局。" icon="flag" />
    <div class="signup-progress" aria-label="报名流程"><span class="current"><b>1</b>填写参赛信息</span><i></i><span><b>2</b>提交报名</span><i></i><span><b>3</b>等待审核</span></div>

    <div class="signup-grid">
      <div class="panel signup-form">
        <div class="form-heading"><h2>填写报名资料</h2><span>* 为必填项</span></div>
        <Spinner v-if="booting" label="加载中" />
        <div v-else-if="bootError" class="empty-note" role="alert"><Icon name="flag" :size="32" /><h3>赛事暂时未能加载</h3><p>{{ bootError }}</p><button class="btn" @click="boot">重新加载</button></div>
        <div v-else-if="!openTournaments.length" class="empty-note"><Icon name="clock" :size="32" /><h3>等待下一次集结</h3><p>当前没有开放报名的赛事，可以先去赛事浏览页查看比赛进展。</p><RouterLink to="/browse" class="btn ghost">查看全部赛事</RouterLink></div>
        <template v-else>
          <div class="field">
            <label for="signup-field-1">选择赛事 *</label>
            <select id="signup-field-1" v-model="selectedTid">
              <option v-for="t in openTournaments" :key="t.id" :value="t.id">{{ t.name }}</option>
            </select>
          </div>
          <div v-if="selectedTournament" class="deadline-note">
            报名截止：<strong>{{ formatDeadline(selectedTournament.registration_deadline) }}</strong>
            <span class="cd">{{ countdown(selectedTournament.registration_deadline) }}</span>
          </div>

          <div class="field">
            <label for="signup-field-2">联系方式 *</label>
            <input id="signup-field-2" v-model="form.contact" maxlength="128" placeholder="QQ / 微信 / 手机号，便于联系" />
          </div>

          <div class="field">
            <label>报名类型 *</label>
            <div class="type-switch" :class="{ single: allowedTypes.length === 1 }">
              <button
                v-for="rt in allowedTypes"
                :key="rt"
                type="button"
                class="type-option"
                :aria-pressed="form.registrationType === rt"
                :class="{ active: form.registrationType === rt }"
                @click="form.registrationType = rt"
              >
                <Icon :name="rt === 'team' ? 'users' : 'user'" :size="20" />{{ REGISTRATION_LABEL[rt] || rt }}
              </button>
            </div>
            <p v-if="allowedTypes.length === 1" class="muted tiny rule-note">
              该赛事仅支持{{ REGISTRATION_LABEL[allowedTypes[0]] }}
            </p>
          </div>

          <template v-if="!isSolo">
            <div class="field">
              <label for="signup-field-3">队伍名称 *</label>
              <input id="signup-field-3" v-model="form.name" maxlength="128" placeholder="例如：烈焰星辰" />
            </div>
            <div class="field">
              <label for="signup-field-4">队长 *</label>
              <input id="signup-field-4" v-model="form.captain" maxlength="64" placeholder="队长称呼" />
            </div>

            <h3 class="roster-title">参赛选手称呼及职业 *</h3>
            <RosterEditor v-model="form.players" :professions="allowedProfessions" />
          </template>

          <template v-else>
            <div class="solo-panel">
              <div class="field">
                <label for="signup-field-5">称呼 *</label>
                <input id="signup-field-5" v-model="form.soloNickname" maxlength="64" placeholder="填写个人报名称呼" />
              </div>
              <div class="field" style="margin-bottom: 0">
                <label for="signup-field-6">职业 *</label>
                <select id="signup-field-6" v-model="form.soloProfession">
                  <option v-for="prof in allowedProfessions" :key="prof" :value="prof">{{ prof }}</option>
                </select>
                <p v-if="allowedProfessions.length < PROFESSIONS.length" class="muted tiny rule-note">
                  该赛事仅限职业：{{ allowedProfessions.join(' / ') }}
                </p>
              </div>
            </div>
          </template>

          <div class="field" style="margin-top: 1.2rem">
            <label for="signup-field-7">{{ isSolo ? '个人宣言' : '作战宣言' }}</label>
            <textarea id="signup-field-7"
              v-model="form.declaration"
              maxlength="2000"
              :placeholder="isSolo ? '写点你的报名介绍或想说的话' : '喊出你们的口号！'"
            ></textarea>
          </div>

          <button class="btn accent" style="width: 100%" :disabled="!canSubmit || submitting" @click="submit">
            {{ submitting ? '提交中…' : '提交报名' }}
          </button>
        </template>
      </div>

      <aside class="side">
        <div class="signup-side-banner"><img :src="teamBattle" alt="百变兵团战队集结" /><div><Icon name="users" :size="20" /><strong>每一位战友，都很重要</strong><p>资料提交后，可在下方关注审核结果。</p></div></div>
        <div class="panel">
          <div class="my-registration-heading"><h3>我的报名</h3><span>{{ myTeams.length }}</span></div>
          <Spinner v-if="booting && !myTeams.length" label="加载中" />
          <p v-else-if="!myTeams.length" class="muted">你还没有提交任何报名。</p>
          <div v-for="t in myTeams" :key="t.id" class="my-team">
            <div class="row">
              <strong>{{ t.name }}</strong>
              <span class="chip sm type-chip">{{ REGISTRATION_LABEL[t.registration_type] || '报名' }}</span>
              <span class="badge" :class="t.status">{{ STATUS_LABEL[t.status] }}</span>
              <span class="spacer"></span>
              <button class="btn danger sm" @click="withdraw(t)">撤回</button>
            </div>
            <p class="muted small tour-tag">{{ tournamentName(t.tournament_id) }}</p>
            <p class="muted small">{{ t.registration_type === 'solo' ? '报名称呼' : '队长' }}：{{ t.captain }}</p>
            <p class="muted small">联系方式：{{ t.contact }}</p>
            <div v-if="t.registration_type === 'solo'" class="prof-mini">
              <span class="chip sm">
                <span class="dot" :style="{ background: `var(--prof-${t.players[0]?.profession || '突击'})` }"></span>
                {{ t.players[0]?.profession || '未填职业' }}
              </span>
            </div>
            <div v-else class="prof-mini">
              <span v-for="prof in PROFESSIONS" :key="prof" class="chip sm">
                <span class="dot" :style="{ background: `var(--prof-${prof})` }"></span>
                {{ prof }}·{{ professionCounts(t.players)[prof] }}
              </span>
            </div>
            <p v-if="t.review_note" class="muted small">审核备注：{{ t.review_note }}</p>
          </div>
        </div>
      </aside>
    </div>

    <Transition name="modal-fade">
      <div v-if="showGroupDialog" class="modal-backdrop" @click.self="showGroupDialog = false">
        <div class="modal group-modal">
          <div class="row group-head">
            <div>
              <h2>报名成功</h2>
              <p class="muted">请扫码加入赛事群，方便接收后续通知与安排。</p>
            </div>
            <span class="spacer"></span>
            <button class="btn ghost sm" @click="showGroupDialog = false">关闭</button>
          </div>
          <img :src="signupGroupQrcode" alt="赛事群二维码" class="group-qrcode" />
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.signup-progress { display: flex; align-items: center; gap: 1.4rem; padding: 1rem 1.5rem; background: #e8edf2; border-radius: 9px; margin-bottom: 1.5rem; color: #667484; font-size: .82rem; }
.signup-progress span { display: flex; align-items: center; gap: .6rem; white-space: nowrap; }
.signup-progress b { width: 25px; height: 25px; border-radius: 50%; background: #d7dee6; display: grid; place-items: center; font-size: .73rem; }
.signup-progress .current { color: var(--primary); font-weight: 650; }
.signup-progress .current b { background: var(--primary); color: #fff; }
.signup-progress i { width: 50px; height: 1px; background: #c8d1da; }
.signup-grid { display: grid; grid-template-columns: minmax(0,1.75fr) minmax(300px,1fr); gap: 1.5rem; align-items: start; }
.signup-form { padding: 1.75rem; }
.form-heading { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.6rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border); }
.form-heading h2 { font-size: 1.15rem; margin: 0; }
.form-heading > span { color: var(--muted); font-size: .73rem; }
.roster-title { margin: 1.7rem 0 1rem; font-size: 1rem; }
.empty-note { text-align: center; padding: 2.2rem 0; color: var(--muted); }
.empty-note .ui-icon { color: var(--primary); margin-bottom: 1rem; }
.empty-note p { margin-bottom: 1.25rem; }
.deadline-note { background: #fff3e3; color: #855216; border-radius: 6px; padding: .65rem .85rem; font-size: .78rem; margin: -.4rem 0 1.5rem; }
.deadline-note .cd { display: inline-block; margin-left: .5rem; font-weight: 650; }
.type-switch { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: .7rem; }
.type-switch.single { grid-template-columns: 1fr; }
.type-option { display: flex; align-items: center; justify-content: center; gap: .6rem; min-height: 57px; border-radius: 7px; border: 1px solid var(--border-strong); background: #fff; color: var(--muted); font-size: .89rem; font-weight: 650; cursor: pointer; transition: border-color .18s, background .18s; }
.type-option:hover { border-color: var(--primary); }
.type-option.active { color: var(--primary); background: var(--accent-soft); border-color: var(--primary); }
.rule-note { margin: .5rem 0 0; font-size: .75rem; }
.solo-panel { padding: 1.2rem; border-radius: 8px; background: var(--panel-2); }
.signup-side-banner { border-radius: 10px; overflow: hidden; margin-bottom: 1.2rem; background: var(--dark); color: #fff; }
.signup-side-banner img { width: 100%; height: 160px; object-fit: cover; display: block; }
.signup-side-banner > div { padding: 1.15rem 1.3rem; }
.signup-side-banner .ui-icon { color: var(--accent-2); margin-right: .5rem; }
.signup-side-banner strong { font-size: .92rem; }
.signup-side-banner p { color: #b6c5d3; margin: .5rem 0 0; font-size: .77rem; }
.my-registration-heading { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.my-registration-heading h3 { margin: 0; }
.my-registration-heading > span { border-radius: 4px; padding: .1rem .45rem; color: #566373; background: var(--bg-2); font-size: .72rem; }
.my-team { border-top: 1px solid var(--border); padding: 1.15rem 0; }
.my-team:first-of-type { border-top: 0; }
.my-team:last-child { padding-bottom: 0; }
.my-team .row strong { flex: 1 1 100%; }
.my-team .btn.danger { color: var(--danger); background: #ffedf0; font-size: .72rem; }
.small { font-size: .76rem; margin: .35rem 0; overflow-wrap: anywhere; }
.tour-tag { color: var(--primary); font-weight: 550; margin-top: .6rem; }
.prof-mini { display: flex; gap: .35rem; flex-wrap: wrap; margin: .6rem 0; }
.chip.sm { font-size: .7rem; padding: .1rem .4rem; }
.type-chip { color: #526679; background: #edf1f5; border: none; }
.group-modal { width: min(560px,100%); }
.group-head { align-items: flex-start; padding-bottom: 1rem; }
.group-head h2 { margin-bottom: .4rem; }
.group-head p { margin: 0; font-size: .83rem; }
.group-qrcode { display: block; width: 100%; max-height: 65dvh; object-fit: contain; border-radius: 8px; }
@media(max-width:950px) { .signup-grid { grid-template-columns: minmax(0,1.5fr) minmax(260px,1fr); gap: 1rem; } .signup-form { padding: 1.3rem; } }
@media(max-width:760px) { .signup-grid { grid-template-columns: 1fr; } .signup-progress { padding: .8rem; gap: .5rem; font-size: .65rem; justify-content: space-between; } .signup-progress span { gap: .3rem; } .signup-progress i { flex: 1; width: auto; min-width: 6px; } .signup-progress b { width: 21px; height: 21px; font-size: .65rem; } .signup-form { padding: 1.15rem; } .side { order: 1; } .signup-side-banner { display: none; } .type-option { min-height: 50px; font-size: .8rem; } .deadline-note { line-height: 1.8; } .deadline-note .cd { display: block; margin: .15rem 0 0; } }
</style>
