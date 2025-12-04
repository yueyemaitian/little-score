import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const api = axios.create({
  // 生产环境使用相对路径（通过 nginx 代理）
  // 开发环境使用 VITE_API_BASE_URL 或 localhost
  baseURL: import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? '/api/v1' : 'http://localhost:8000/api/v1'),
  timeout: 10000
})

// 请求拦截器：添加 token
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理错误
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    // 记录错误详情（开发环境）
    if (import.meta.env.DEV) {
      console.error('API 错误详情:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        dataType: typeof error.response?.data,
        headers: error.response?.headers,
        message: error.message,
        fullError: error,
        errorKeys: Object.keys(error || {})
      })
    }
    
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      window.location.href = '/login'
    }
    
    // 确保错误对象包含完整的响应信息
    // axios 错误对象结构：error.response.data 包含服务器返回的数据
    // FastAPI 错误响应格式：{detail: "错误信息"}
    // 确保 error.response.data 存在且可访问
    if (error.response && !error.response.data) {
      console.warn('错误响应没有 data 字段:', error.response)
    }
    
    return Promise.reject(error)
  }
)

export default api


