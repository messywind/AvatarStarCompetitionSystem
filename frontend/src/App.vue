<script setup>
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { toastState } from './toast'
import Icon from './components/Icon.vue'
import logo from './assets/logo.png'
import logoFooter from './assets/logo-footer.png'
import logoClaude from './assets/logo-claude.svg'
import logoOpenai from './assets/logo-openai.svg'
import avatarMessywind from './assets/credit-messywind.jpg'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push({ name: 'home' })
}
</script>

<template>
  <a class="skip-link" href="#main-content">跳到主要内容</a>
  <header class="navbar">
    <div class="nav-inner">
      <RouterLink to="/" class="brand">
        <img :src="logo" alt="百变兵团" class="brand-logo" />
        <span class="brand-cup">百变兵团<small>赛事中心</small></span>
      </RouterLink>

      <nav class="nav-links" aria-label="主导航">
        <RouterLink to="/"><Icon name="grid" :size="16" />赛事大厅</RouterLink>
        <RouterLink to="/browse"><Icon name="trophy" :size="17" />赛事浏览</RouterLink>
        <RouterLink to="/signup"><Icon name="flag" :size="17" />我要报名</RouterLink>
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
          <RouterLink to="/login" class="nav-auth-link nav-auth-login">登录</RouterLink>
          <RouterLink to="/register" class="nav-auth-link nav-auth-register">注册参赛 <Icon name="arrow" :size="15" /></RouterLink>
        </template>
      </div>
    </div>
  </header>

  <main id="main-content" tabindex="-1">
    <RouterView v-slot="{ Component }">
      <Transition name="route" mode="out-in">
        <component :is="Component" />
      </Transition>
    </RouterView>
  </main>

  <footer class="site-footer">
    <div class="footer-inner">
      <img :src="logoFooter" alt="百变兵团" class="footer-logo" />
      <span class="muted">百变兵团 · 赛事报名系统</span>
      <span class="footer-support muted">
        技术支持：
        <span class="credit"><img :src="logoClaude" alt="" class="credit-icon" />ClaudeCode</span>
        <span class="credit"><img :src="logoOpenai" alt="" class="credit-icon" />Codex</span>
        <span class="credit"><img :src="avatarMessywind" alt="凌乱之风头像" class="credit-icon credit-avatar" />凌乱之风</span>
      </span>
      <span class="footer-copy muted">© 2026 Avatar Star</span>
    </div>
  </footer>

  <div class="toast-wrap" aria-live="polite" aria-atomic="false">
    <div v-for="t in toastState.items" :key="t.id" class="toast" :class="t.type">
      {{ t.message }}
    </div>
  </div>
</template>

<style scoped>
.skip-link { position: fixed; left: 1rem; top: -100px; z-index: var(--z-toast); background: #fff; padding: .6rem 1rem; }
.skip-link:focus { top: 1rem; }
.navbar { position: sticky; top: 0; z-index: var(--z-nav); background: var(--dark); border-bottom: 1px solid #ffffff14; }
.nav-inner { max-width: 1248px; margin: 0 auto; display: flex; align-items: center; gap: 2.8rem; padding: 0 2rem; min-height: 80px; }
.brand { display: flex; align-items: center; gap: .85rem; color: #fff; text-decoration: none; flex: none; }
.brand-logo { width: 108px; height: 49px; object-fit: contain; display: block; }
.brand-cup { font-weight: 750; font-size: 1.13rem; line-height: 1.35; padding-left: .85rem; border-left: 1px solid #ffffff30; letter-spacing: .04em; }
.brand-cup small { display: block; font-size: .64rem; font-weight: 400; letter-spacing: .2em; color: #a9b6c3; margin-top: .2rem; }
.nav-links { display: flex; align-self: stretch; gap: 1.7rem; }
.nav-links a { position: relative; display: flex; align-items: center; gap: .45rem; white-space: nowrap; color: #aebbc7; font-size: .87rem; font-weight: 550; text-decoration: none; transition: color .18s; }
.nav-links a:hover, .nav-links a.router-link-exact-active { color: #fff; }
.nav-links a.router-link-exact-active::after { content: ''; position: absolute; bottom: 0; height: 3px; background: var(--accent-2); left: 0; right: 0; }
.nav-links a.router-link-exact-active .ui-icon { color: var(--accent-2); }
.nav-auth { margin-left: auto; display: flex; align-items: center; gap: .75rem; flex: none; }
.nav-auth-link { display: inline-flex; align-items: center; justify-content: center; gap: .5rem; min-height: 38px; padding: .5rem 1rem; border-radius: 6px; font-size: .82rem; font-weight: 600; text-decoration: none; transition: background .18s; }
.nav-auth-login { color: #e0e6ed; }
.nav-auth-login:hover { background: #ffffff0d; }
.nav-auth-register { color: #172330; background: var(--accent-2); }
.nav-auth-register:hover { background: #ffa974; }
.user-chip { display: inline-flex; align-items: center; gap: .4rem; font-size: .84rem; color: #e0e6ed; padding: .4rem .5rem; border-radius: 5px; max-width: 200px; overflow-wrap: anywhere; }
.user-chip:hover { text-decoration: none; background: #ffffff0d; }
.user-chip em { font-style: normal; font-size: .68rem; color: #ffc79f; }
.role-dot { width: 7px; height: 7px; border-radius: 50%; background: #6dcc93; flex: none; }
.role-dot.admin { background: var(--accent-2); }
.nav-auth .btn.ghost { background: #ffffff08; border-color: #ffffff20; color: #c7d1db; }
.route-enter-active, .route-leave-active { transition: opacity .13s; }
.route-enter-from, .route-leave-to { opacity: 0; }
.site-footer { background: #e9edf1; border-top: 1px solid var(--border); }
.footer-inner { max-width: 1248px; margin: 0 auto; padding: 1.6rem 2rem; display: flex; align-items: center; gap: .9rem; font-size: .74rem; }
.footer-logo { width: 72px; height: 32px; object-fit: contain; opacity: .75; }
.footer-support { display: inline-flex; align-items: center; flex-wrap: wrap; gap: .2rem .7rem; margin-left: auto; }
.credit { display: inline-flex; align-items: center; gap: .32rem; }
.credit-icon { width: 14px; height: 14px; object-fit: contain; }
.credit-avatar { border-radius: 50%; object-fit: cover; }
.footer-copy { margin-left: .75rem; }
@media(max-width:1050px) { .nav-inner { gap: 1.6rem; } .nav-links { gap: 1rem; } .brand-logo { width: 88px; } .nav-auth { gap: .25rem; } .nav-auth-link { padding: .5rem .7rem; } .footer-inner { flex-wrap: wrap; } .footer-support { margin-left: 0; } }
@media(max-width:760px) {
 .nav-inner { flex-wrap: wrap; min-height: auto; gap: 0 .6rem; padding: .55rem 1rem 0; }
 .brand { flex: 1; gap: .55rem; } .brand-logo { width: 82px; height: 40px; }
 .brand-cup { font-size: .98rem; padding-left: .6rem; } .brand-cup small { font-size: .58rem; }
 .nav-links { order: 3; width: 100%; min-height: 45px; gap: 1.6rem; overflow-x: auto; scrollbar-width: none; }
 .nav-links a { font-size: .8rem; gap: .35rem; flex: none; } .nav-auth-link { font-size: .78rem; min-height: 36px; padding: .4rem .6rem; }
 .nav-auth-register .ui-icon { display: none; } .user-chip { max-width: 120px; font-size: .75rem; } .user-chip em { display: none; }
 .footer-inner { padding: 1.4rem 1rem; gap: .6rem; font-size: .7rem; } .footer-support { width: 100%; } .footer-copy { margin-left: 0; }
}
</style>
