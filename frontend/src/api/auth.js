import api from './index'

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
    
    // 使用统一的 api 实例，但指定特殊的 Content-Type
    return api.post('/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
  },
  getMe() {
    return api.get('/auth/me')
  }
}


