<script setup>
import { ref } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { toast } from '../toast'
import AuthLayout from '../components/AuthLayout.vue'

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
  <AuthLayout>
      <h1>登录选手账号</h1>
      <p class="auth-intro">登录后即可报名参赛，并管理你的报名记录。</p>
      <form @submit.prevent="submit">
        <div class="field">
          <label for="login-username">用户名</label>
          <input id="login-username" required v-model="username" autocomplete="username" placeholder="请输入用户名" />
        </div>
        <div class="field">
          <label for="login-password">密码</label>
          <input id="login-password" required v-model="password" type="password" autocomplete="current-password" placeholder="请输入密码" />
        </div>
        <button class="btn" style="width: 100%" :disabled="loading">
          {{ loading ? '登录中…' : '登录' }}
        </button>
      </form>
      <p class="muted switch">还没有账号？<RouterLink to="/register">立即注册</RouterLink></p>
  </AuthLayout>
</template>
