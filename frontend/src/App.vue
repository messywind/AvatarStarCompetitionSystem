<script setup>
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { toastState } from './toast'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push({ name: 'home' })
}
</script>

<template>
  <header class="navbar">
    <div class="nav-inner">
      <RouterLink to="/" class="brand">
        <span class="brand-star">★</span>
        <span class="brand-text">百变兵团<em>选花杯</em></span>
      </RouterLink>

      <nav class="nav-links">
        <RouterLink to="/browse">赛事浏览</RouterLink>
        <RouterLink v-if="auth.isAuthenticated" to="/signup">我要报名</RouterLink>
        <RouterLink v-if="auth.isAdmin" to="/admin">管理端</RouterLink>
      </nav>

      <div class="nav-auth">
        <template v-if="auth.isAuthenticated">
          <span class="user-chip">
            <span class="role-dot" :class="{ admin: auth.isAdmin }"></span>
            {{ auth.user.username }}
            <em v-if="auth.isAdmin">管理员</em>
          </span>
          <button class="btn ghost sm" @click="logout">退出</button>
        </template>
        <template v-else>
          <RouterLink to="/login" class="btn ghost sm">登录</RouterLink>
          <RouterLink to="/register" class="btn sm">注册</RouterLink>
        </template>
      </div>
    </div>
  </header>

  <main>
    <RouterView />
  </main>

  <div class="toast-wrap">
    <div v-for="t in toastState.items" :key="t.id" class="toast" :class="t.type">
      {{ t.message }}
    </div>
  </div>
</template>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 500;
  background: rgba(8, 12, 32, 0.72);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}
.nav-inner {
  max-width: 1180px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0.75rem 1.25rem;
}
.brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 800;
  font-size: 1.2rem;
  color: var(--text);
  text-decoration: none;
}
.brand-star { color: var(--accent-2); filter: drop-shadow(0 0 8px rgba(255, 176, 58, 0.6)); }
.brand-text em { color: var(--primary-2); font-style: normal; margin-left: 2px; }
.nav-links { display: flex; gap: 1.2rem; }
.nav-links a {
  color: var(--muted);
  font-weight: 600;
  padding: 0.3rem 0;
  border-bottom: 2px solid transparent;
}
.nav-links a:hover { color: var(--text); text-decoration: none; }
.nav-links a.router-link-active { color: var(--primary-2); border-bottom-color: var(--primary-2); }
.nav-auth { margin-left: auto; display: flex; align-items: center; gap: 0.6rem; }
.user-chip { display: inline-flex; align-items: center; gap: 0.4rem; font-size: 0.88rem; color: var(--text); }
.user-chip em { font-style: normal; font-size: 0.72rem; color: var(--accent-2); background: rgba(255,176,58,.14); padding: 1px 6px; border-radius: 6px; }
.role-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--primary-2); }
.role-dot.admin { background: var(--accent-2); }

@media (max-width: 720px) {
  .nav-inner { flex-wrap: wrap; gap: 0.8rem; }
  .nav-links { order: 3; width: 100%; }
}
</style>
