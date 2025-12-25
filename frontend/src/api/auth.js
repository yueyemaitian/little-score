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
  },
  loginWithWechat(code, state = null) {
    return api.post('/auth/login/wechat', { code, state })
  },
  loginWithDingtalk(code, state = null) {
    return api.post('/auth/login/dingtalk', { code, state })
  },
  getMyAccounts() {
    return api.get('/auth/accounts')
  },
  bindAccount(data) {
    return api.post('/auth/accounts/bind', data)
  },
  getWechatJSSDKConfig(url) {
    return api.get('/auth/wechat/jssdk-config', { params: { url } })
  },
  getWechatAppId() {
    return api.get('/auth/wechat/app-id')
  }
}


