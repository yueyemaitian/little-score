import { defineStore } from 'pinia'
import { authApi } from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user?.is_admin || false
  },

  actions: {
    async login(email, password) {
      try {
        console.log('authStore.login 开始，邮箱:', email)
        const response = await authApi.login({
          username: email,
          password
        })
        console.log('登录 API 响应:', response)
        
        if (!response || !response.access_token) {
          throw new Error('登录响应中没有 access_token')
        }
        
        this.token = response.access_token
        localStorage.setItem('token', this.token)
        console.log('Token 已保存:', this.token ? '已保存' : '未保存')
        
        await this.fetchUser()
        console.log('用户信息已获取:', this.user)
        return response
      } catch (error) {
        console.error('authStore.login 错误:', error)
        throw error
      }
    },

    async register(email, password) {
      try {
        const response = await authApi.register({
          email,
          password
        })
        return response
      } catch (error) {
        throw error
      }
    },

    async fetchUser() {
      try {
        const user = await authApi.getMe()
        this.user = user
        return user
      } catch (error) {
        this.logout()
        throw error
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
    }
  }
})


