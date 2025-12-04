import api from './index'

export const studentsApi = {
  getList() {
    return api.get('/students/')
  },
  create(data) {
    return api.post('/students/', data)
  },
  update(id, data) {
    return api.put(`/students/${id}`, data)
  },
  delete(id) {
    return api.delete(`/students/${id}`)
  }
}


