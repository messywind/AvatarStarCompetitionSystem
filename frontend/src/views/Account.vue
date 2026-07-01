<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { toast } from '../toast'

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
    <h1>账号设置</h1>
    <p class="muted">管理你的登录信息与安全设置。</p>

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
      </div>

      <div class="panel">
        <h3>修改密码</h3>
        <form @submit.prevent="submit">
          <div class="field">
            <label>当前密码</label>
            <input v-model="oldPassword" type="password" autocomplete="current-password" placeholder="请输入当前密码" />
          </div>
          <div class="field">
            <label>新密码（至少 6 位）</label>
            <input v-model="newPassword" type="password" autocomplete="new-password" placeholder="设置新密码" />
          </div>
          <div class="field">
            <label>确认新密码</label>
            <input v-model="confirmPassword" type="password" autocomplete="new-password" placeholder="再次输入新密码" />
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
.account-page { max-width: 820px; }
.account-grid { display: grid; grid-template-columns: 1fr; gap: 1.25rem; margin-top: 1.5rem; }
.info-card { display: flex; align-items: center; gap: 1.1rem; }
.avatar {
  width: 56px; height: 56px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; font-weight: 700; color: #fff;
  background: linear-gradient(135deg, var(--primary), #59a7ff);
  flex: none;
  animation: avatar-in 0.34s var(--ease-soft) both;
}
.avatar.admin { background: linear-gradient(135deg, #ff7a3c, var(--accent-2)); }
.uname { font-size: 1.2rem; font-weight: 600; margin-bottom: 0.3rem; }

@keyframes avatar-in {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: none; }
}

@media (max-width: 520px) {
  .info-card {
    align-items: flex-start;
  }
  .account-page .btn {
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .avatar {
    animation: none;
  }
}
</style>
