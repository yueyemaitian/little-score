import api from './index'

export const projectsApi = {
  getList(params) {
    return api.get('/projects/', { params })
  },
  create(data) {
    return api.post('/projects/', data)
  },
  update(id, data) {
    return api.put(`/projects/${id}`, data)
  },
  delete(id) {
    return api.delete(`/projects/${id}`)
  }
}


