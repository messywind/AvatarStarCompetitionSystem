import { defineStore } from 'pinia'
import api from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isAuthenticated: (s) => !!s.token,
    isAdmin: (s) => s.user?.role === 'admin',
  },
  actions: {
    _persist() {
      localStorage.setItem('token', this.token)
      localStorage.setItem('user', JSON.stringify(this.user))
    },
    async login(username, password) {
      const { data } = await api.post('/auth/login', { username, password })
      this.token = data.access_token
      this.user = data.user
      this._persist()
    },
    async register(username, password) {
      const { data } = await api.post('/auth/register', { username, password })
      this.token = data.access_token
      this.user = data.user
      this._persist()
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },
  },
})
