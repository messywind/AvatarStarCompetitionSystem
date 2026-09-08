<script setup>
import { ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { toast } from '../toast'
import AuthLayout from '../components/AuthLayout.vue'

const auth = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const password2 = ref('')
const loading = ref(false)

async function submit() {
  if (username.value.trim().length < 3) return toast('用户名至少 3 个字符', 'error')
  if (password.value.length < 6) return toast('密码至少 6 个字符', 'error')
  if (password.value !== password2.value) return toast('两次输入的密码不一致', 'error')
  loading.value = true
  try {
    await auth.register(username.value.trim(), password.value)
    toast('注册成功，已自动登录', 'success')
    router.push({ name: 'signup' })
  } catch (e) {
    toast(e.message || '注册失败', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthLayout register>
      <h1>注册账号</h1>
      <p class="auth-intro">注册后即可报名参赛。</p>
      <form @submit.prevent="submit">
        <div class="field">
          <label for="register-username">用户名（至少 3 位）</label>
          <input id="register-username" required v-model="username" autocomplete="username" placeholder="设置你的用户名" />
        </div>
        <div class="field">
          <label for="register-password">密码（至少 6 位）</label>
          <input id="register-password" required v-model="password" type="password" autocomplete="new-password" placeholder="设置密码" />
        </div>
        <div class="field">
          <label for="register-password2">确认密码</label>
          <input id="register-password2" required v-model="password2" type="password" autocomplete="new-password" placeholder="再次输入密码" />
        </div>
        <button class="btn accent" style="width: 100%" :disabled="loading">
          {{ loading ? '注册中…' : '注册' }}
        </button>
      </form>
      <p class="muted switch">已有账号？<RouterLink to="/login">去登录</RouterLink></p>
  </AuthLayout>
</template>
