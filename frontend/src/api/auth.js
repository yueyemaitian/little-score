import api from './index'
import axios from 'axios'

export const authApi = {
  register(data) {
    return api.post('/auth/register', data)
  },
  login(data) {
    // 登录接口需要使用 application/x-www-form-urlencoded 格式
    // 因为后端使用 OAuth2PasswordRequestForm
    const params = new URLSearchParams()
    params.append('username', data.username || data.email)
    params.append('password', data.password)
    
    return axios.post(
      `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/auth/login`,
      params,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    ).then(response => {
      console.log('登录响应:', response.data)
      return response.data
    }).catch(error => {
      // 记录错误详情（开发环境）
      if (import.meta.env.DEV) {
        console.error('登录 API 错误详情:', {
          url: error.config?.url,
          method: error.config?.method,
          status: error.response?.status,
          statusText: error.response?.statusText,
          data: error.response?.data,
          message: error.message
        })
      }
      // 确保错误对象包含完整的响应信息
      return Promise.reject(error)
    })
  },
  getMe() {
    return api.get('/auth/me')
  }
}


