import api from './index'

export const adminApi = {
  getSettings() {
    return api.get('/admin/settings')
  },
  updateSettings(data) {
    return api.put('/admin/settings', data)
  },
  getUsers() {
    return api.get('/users/')
  }
}


