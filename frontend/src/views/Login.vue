<script setup>
import { ref } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { toast } from '../toast'
import logo from '../assets/logo.png'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const loading = ref(false)

async function submit() {
  if (!username.value || !password.value) return
  loading.value = true
  try {
    await auth.login(username.value.trim(), password.value)
    toast('登录成功', 'success')
    router.push(route.query.redirect || { name: auth.isAdmin ? 'admin' : 'home' })
  } catch (e) {
    toast(e.message || '登录失败', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="container auth-page">
    <div class="panel auth-card">
      <img :src="logo" alt="百变兵团" class="auth-logo" />
      <h1>登录</h1>
      <p class="muted">登录后即可报名参赛、管理你的战队。</p>
      <form @submit.prevent="submit">
        <div class="field">
          <label>用户名</label>
          <input v-model="username" autocomplete="username" placeholder="请输入用户名" />
        </div>
        <div class="field">
          <label>密码</label>
          <input v-model="password" type="password" autocomplete="current-password" placeholder="请输入密码" />
        </div>
        <button class="btn" style="width: 100%" :disabled="loading">
          {{ loading ? '登录中…' : '登录' }}
        </button>
      </form>
      <p class="muted switch">还没有账号？<RouterLink to="/register">立即注册</RouterLink></p>
    </div>
  </div>
</template>

<style scoped>
.auth-page { display: flex; justify-content: center; padding-top: 3rem; }
.auth-card { width: min(420px, 100%); animation: auth-in 0.34s var(--ease-soft) both; }
.auth-logo { display: block; height: 40px; margin: 0 auto 1.2rem; transition: transform 0.24s var(--ease-soft); }
.auth-card:hover .auth-logo { transform: translateY(-2px); }
.switch { margin-top: 1rem; text-align: center; }

@keyframes auth-in {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: none; }
}

@media (max-width: 520px) {
  .auth-page {
    padding-top: 1.5rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .auth-card {
    animation: none;
  }
}
</style>
