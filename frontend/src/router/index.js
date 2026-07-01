import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import SignUp from '../views/SignUp.vue'
import Admin from '../views/Admin.vue'
import Browse from '../views/Browse.vue'

const routes = [
  { path: '/', name: 'home', component: Home },
  { path: '/login', name: 'login', component: Login },
  { path: '/register', name: 'register', component: Register },
  { path: '/signup', name: 'signup', component: SignUp, meta: { requiresAuth: true } },
  { path: '/browse', name: 'browse', component: Browse },
  { path: '/admin', name: 'admin', component: Admin, meta: { requiresAdmin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return auth.isAuthenticated ? { name: 'home' } : { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
