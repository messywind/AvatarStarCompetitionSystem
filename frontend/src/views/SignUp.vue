<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '../api'
import { toast } from '../toast'
import { validateRoster, PROFESSIONS } from '../roster'
import { formatDeadline, countdown } from '../time'
import RosterEditor from '../components/RosterEditor.vue'
import signupGroupQrcode from '../assets/signup-group-qrcode.jpg'

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
const myTeams = ref([])
const tournaments = ref([])
const selectedTid = ref(null)
const showGroupDialog = ref(false)

const openTournaments = computed(() => tournaments.value.filter((t) => t.registration_open))
const selectedTournament = computed(() => tournaments.value.find((t) => t.id === selectedTid.value))
const tournamentName = (id) => tournaments.value.find((t) => t.id === id)?.name || `#${id}`

const isSolo = computed(() => form.registrationType === 'solo')
const validation = computed(() => validateRoster(form.players))
const canSubmit = computed(() => {
  if (!selectedTid.value) return false
  if (!form.contact.trim()) return false
  if (isSolo.value) return !!form.soloNickname.trim() && !!form.soloProfession
  return !!form.name.trim() && !!form.captain.trim() && validation.value.errors.length === 0
})

function resetForm() {
  form.registrationType = 'team'
  form.name = ''
  form.captain = ''
  form.contact = ''
  form.declaration = ''
  form.players = blankRoster()
  form.soloNickname = ''
  form.soloProfession = '突击'
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

onMounted(async () => {
  await Promise.all([loadTournaments(), loadMine()])
})
</script>

<template>
  <div class="container">
    <h1>赛事报名</h1>
    <p class="muted">选择赛事后，可提交战队报名或个人报名，资料提交后由管理员审核。</p>

    <div class="signup-grid">
      <div class="panel">
        <div v-if="!openTournaments.length" class="empty-note">
          当前没有正在报名的赛事。
        </div>
        <template v-else>
          <div class="field">
            <label>选择赛事 *</label>
            <select v-model="selectedTid">
              <option v-for="t in openTournaments" :key="t.id" :value="t.id">{{ t.name }}</option>
            </select>
          </div>
          <div v-if="selectedTournament" class="deadline-note">
            报名截止：<strong>{{ formatDeadline(selectedTournament.registration_deadline) }}</strong>
            <span class="cd">{{ countdown(selectedTournament.registration_deadline) }}</span>
          </div>

          <div class="field">
            <label>联系方式 *</label>
            <input v-model="form.contact" maxlength="128" placeholder="QQ / 微信 / 手机号，便于联系" />
          </div>

          <div class="field">
            <label>报名类型 *</label>
            <div class="type-switch">
              <button
                type="button"
                class="type-option"
                :class="{ active: form.registrationType === 'team' }"
                @click="form.registrationType = 'team'"
              >
                战队报名
              </button>
              <button
                type="button"
                class="type-option"
                :class="{ active: form.registrationType === 'solo' }"
                @click="form.registrationType = 'solo'"
              >
                个人报名
              </button>
            </div>
          </div>

          <template v-if="!isSolo">
            <div class="field">
              <label>队伍名称 *</label>
              <input v-model="form.name" maxlength="128" placeholder="例如：烈焰星辰" />
            </div>
            <div class="field">
              <label>队长 *</label>
              <input v-model="form.captain" maxlength="64" placeholder="队长称呼" />
            </div>

            <h3 class="roster-title">参赛选手称呼及职业 *</h3>
            <RosterEditor v-model="form.players" />
          </template>

          <template v-else>
            <div class="solo-panel">
              <div class="field">
                <label>称呼 *</label>
                <input v-model="form.soloNickname" maxlength="64" placeholder="填写个人报名称呼" />
              </div>
              <div class="field" style="margin-bottom: 0">
                <label>职业 *</label>
                <select v-model="form.soloProfession">
                  <option v-for="prof in PROFESSIONS" :key="prof" :value="prof">{{ prof }}</option>
                </select>
              </div>
            </div>
          </template>

          <div class="field" style="margin-top: 1.2rem">
            <label>{{ isSolo ? '个人宣言' : '作战宣言' }}</label>
            <textarea
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
        <div class="panel">
          <h3>我的报名</h3>
          <p v-if="!myTeams.length" class="muted">你还没有提交任何报名。</p>
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
.signup-grid { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(300px, 1fr); gap: 1.5rem; margin-top: 1.5rem; align-items: start; }
.signup-grid > .panel,
.side .panel {
  animation: panel-lift 0.34s var(--ease-soft) both;
}
.side .panel {
  animation-delay: 80ms;
}
.roster-title { margin-top: 1.5rem; }
.empty-note { color: var(--muted); padding: 1rem 0; text-align: center; }
.deadline-note {
  background: rgba(255, 149, 0, 0.1);
  border: 1px solid rgba(255, 149, 0, 0.28);
  color: #a85e00;
  border-radius: var(--radius-sm);
  padding: 0.6rem 0.85rem;
  font-size: 0.88rem;
  margin-bottom: 1.1rem;
}
.deadline-note .cd { margin-left: 0.6rem; font-weight: 700; }
.type-switch {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.6rem;
}
.type-option {
  min-height: 44px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--panel);
  color: var(--muted);
  font-size: 0.92rem;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.18s var(--ease-out), background 0.18s var(--ease-out), color 0.18s var(--ease-out), transform 0.18s var(--ease-out), box-shadow 0.18s var(--ease-out);
}
.type-option:hover {
  transform: translateY(-1px);
  border-color: rgba(0, 113, 227, 0.28);
}
.type-option.active {
  color: var(--primary);
  background: rgba(0, 113, 227, 0.08);
  border-color: rgba(0, 113, 227, 0.34);
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.08);
}
.solo-panel {
  padding: 1rem;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: linear-gradient(180deg, rgba(0, 113, 227, 0.04), rgba(0, 113, 227, 0.01));
}
.my-team { border-top: 1px solid var(--border); padding: 0.9rem 0; }
.my-team:first-of-type { border-top: none; }
.small { font-size: 0.8rem; margin: 0.3rem 0; }
.tour-tag { color: var(--primary); font-weight: 600; }
.prof-mini { display: flex; gap: 0.35rem; flex-wrap: wrap; margin: 0.4rem 0; }
.chip.sm { font-size: 0.72rem; padding: 0.12rem 0.45rem; }
.type-chip { color: var(--primary); background: rgba(0, 113, 227, 0.08); border-color: rgba(0, 113, 227, 0.12); }
.group-modal {
  width: min(560px, 100%);
  padding: 1rem;
}
.group-head {
  align-items: flex-start;
  padding: 0.35rem 0.35rem 0.85rem;
}
.group-head h2 {
  margin-bottom: 0.2rem;
}
.group-head p {
  margin: 0;
}
.group-qrcode {
  display: block;
  width: 100%;
  max-height: 76vh;
  object-fit: contain;
  border-radius: 16px;
}

@keyframes panel-lift {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@media (max-width: 880px) {
  .signup-grid { grid-template-columns: 1fr; }
  .side { order: -1; }
}

@media (max-width: 560px) {
  .type-switch {
    grid-template-columns: 1fr;
  }
  .deadline-note {
    line-height: 1.65;
  }
  .deadline-note .cd {
    display: block;
    margin: 0.25rem 0 0;
  }
  .my-team .row {
    align-items: flex-start;
  }
  .my-team .row strong {
    flex: 1 1 100%;
  }
  .my-team .btn {
    width: 100%;
  }
  .group-modal {
    padding: 0.8rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .signup-grid > .panel,
  .side .panel {
    animation: none;
  }
}
</style>
