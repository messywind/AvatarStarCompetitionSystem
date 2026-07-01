<script setup>
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { toastState } from './toast'
import logo from './assets/logo.png'

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
        <img :src="logo" alt="百变兵团" class="brand-logo" />
        <span class="brand-cup">选花杯</span>
      </RouterLink>

      <nav class="nav-links">
        <RouterLink to="/browse">赛事浏览</RouterLink>
        <RouterLink v-if="auth.isAuthenticated" to="/signup">我要报名</RouterLink>
        <RouterLink v-if="auth.isAdmin" to="/admin">管理端</RouterLink>
      </nav>

      <div class="nav-auth">
        <template v-if="auth.isAuthenticated">
          <RouterLink to="/account" class="user-chip">
            <span class="role-dot" :class="{ admin: auth.isAdmin }"></span>
            {{ auth.user.username }}
            <em v-if="auth.isAdmin">管理员</em>
          </RouterLink>
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

  <footer class="site-footer">
    <div class="footer-inner">
      <img :src="logo" alt="百变兵团" class="footer-logo" />
      <span class="muted">百变兵团 · 选花杯报名系统</span>
      <span class="footer-copy muted">© 2026 Avatar Star</span>
    </div>
  </footer>

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
  background: rgba(251, 251, 253, 0.72);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}
.nav-inner {
  max-width: 1120px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 0.55rem 1.5rem;
}
.brand {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  text-decoration: none;
}
.brand-logo { height: 34px; width: auto; display: block; }
.brand-cup {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--text);
  padding-left: 0.55rem;
  border-left: 1px solid var(--border-strong);
  letter-spacing: 0.02em;
}
.nav-links { display: flex; gap: 1.6rem; }
.nav-links a {
  color: var(--text);
  font-weight: 400;
  font-size: 0.9rem;
  padding: 0.2rem 0;
  opacity: 0.82;
  transition: opacity 0.15s;
}
.nav-links a:hover { opacity: 1; text-decoration: none; }
.nav-links a.router-link-active { opacity: 1; font-weight: 500; }
.nav-auth { margin-left: auto; display: flex; align-items: center; gap: 0.6rem; }
.user-chip {
  display: inline-flex; align-items: center; gap: 0.4rem;
  font-size: 0.88rem; color: var(--text); text-decoration: none;
  padding: 0.25rem 0.6rem; border-radius: 980px;
  transition: background 0.15s;
}
.user-chip:hover { background: rgba(0, 0, 0, 0.05); text-decoration: none; }
.user-chip em { font-style: normal; font-size: 0.72rem; color: var(--accent); background: rgba(255, 106, 0, 0.12); padding: 1px 6px; border-radius: 6px; }
.role-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--success); }
.role-dot.admin { background: var(--accent); }

.site-footer {
  border-top: 1px solid var(--border);
  background: var(--bg-2);
  margin-top: 2rem;
}
.footer-inner {
  max-width: 1120px; margin: 0 auto; padding: 1.75rem 1.5rem;
  display: flex; align-items: center; gap: 0.9rem; font-size: 0.85rem;
}
.footer-logo { height: 26px; width: auto; opacity: 0.9; }
.footer-copy { margin-left: auto; }

@media (max-width: 720px) {
  .nav-inner { flex-wrap: wrap; gap: 0.8rem; }
  .nav-links { order: 3; width: 100%; }
  .footer-inner { flex-wrap: wrap; }
}
</style>
