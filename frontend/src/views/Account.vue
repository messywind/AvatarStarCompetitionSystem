<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { toast } from '../toast'
import PageHeading from '../components/PageHeading.vue'
import Icon from '../components/Icon.vue'

const auth = useAuthStore()

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)

async function submit() {
  if (!oldPassword.value) return toast('请输入当前密码', 'error')
  if (newPassword.value.length < 6) return toast('新密码至少 6 个字符', 'error')
  if (newPassword.value !== confirmPassword.value) return toast('两次输入的新密码不一致', 'error')
  if (newPassword.value === oldPassword.value) return toast('新密码不能与当前密码相同', 'error')
  loading.value = true
  try {
    await auth.changePassword(oldPassword.value, newPassword.value)
    toast('密码修改成功', 'success')
    oldPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (e) {
    toast(e.message || '修改失败', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="container account-page">
    <PageHeading title="账号设置" description="管理你的选手账号与登录安全。" icon="user" />

    <div class="account-grid">
      <div class="panel info-card">
        <div class="avatar" :class="{ admin: auth.isAdmin }">
          {{ auth.user?.username?.[0]?.toUpperCase() || 'U' }}
        </div>
        <div>
          <div class="uname">{{ auth.user?.username }}</div>
          <span class="badge" :class="auth.isAdmin ? 'approved' : 'pending'">
            {{ auth.isAdmin ? '管理员' : '普通用户' }}
          </span>
        </div>
        <p class="profile-note">你的专属选手账号<br />报名记录与参赛信息将关联此账号。</p>
      </div>

      <div class="panel password-panel">
        <div class="password-heading"><Icon name="lock" :size="21" /><h3>修改登录密码</h3></div>
        <p class="muted password-hint">使用至少 6 位的新密码，保护你的参赛信息。</p>
        <form @submit.prevent="submit">
          <div class="field">
            <label for="oldPassword">当前密码</label>
            <input id="oldPassword" required v-model="oldPassword" type="password" autocomplete="current-password" placeholder="请输入当前密码" />
          </div>
          <div class="field">
            <label for="newPassword">新密码（至少 6 位）</label>
            <input id="newPassword" required v-model="newPassword" type="password" autocomplete="new-password" placeholder="设置新密码" />
          </div>
          <div class="field">
            <label for="confirmPassword">确认新密码</label>
            <input id="confirmPassword" required v-model="confirmPassword" type="password" autocomplete="new-password" placeholder="再次输入新密码" />
          </div>
          <button class="btn" :disabled="loading">
            {{ loading ? '提交中…' : '确认修改' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.account-page { max-width: 1050px; }
.account-grid { display: grid; grid-template-columns: 280px minmax(0,1fr); gap: 1.5rem; align-items: start; }
.info-card { padding: 2rem 1.6rem; text-align: center; background: var(--dark); border: none; color: #fff; }
.avatar { width: 68px; height: 68px; margin: 0 auto 1rem; border-radius: 12px; display: grid; place-items: center; color: #172330; background: #ffad72; font-weight: 800; font-size: 1.8rem; }
.uname { font-size: 1.25rem; font-weight: 700; margin-bottom: .6rem; overflow-wrap: anywhere; }
.profile-note { font-size: .78rem; line-height: 1.9; color: #b6c5d3; padding-top: 1.3rem; border-top: 1px solid #ffffff20; margin: 1.5rem 0 0; }
.password-heading { display: flex; align-items: center; gap: .65rem; }
.password-heading .ui-icon { color: var(--primary); }
.password-heading h3 { margin: 0; font-size: 1.2rem; }
.password-hint { font-size: .82rem; margin: .7rem 0 1.6rem; }
.password-panel { padding: 2rem; }
@media(max-width:720px) { .account-grid { grid-template-columns: 1fr; } .info-card { display: flex; flex-wrap: wrap; align-items: center; gap: 1rem; text-align: left; padding: 1.25rem; } .avatar { margin: 0; width: 52px; height: 52px; } .profile-note { width: 100%; margin-top: .2rem; padding-top: .8rem; } .password-panel { padding: 1.25rem; } .password-panel .btn { width: 100%; } }
</style>
