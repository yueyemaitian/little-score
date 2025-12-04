import api from './index'

export const tasksApi = {
  getList(params) {
    return api.get('/tasks/', { params })
  },
  create(data) {
    return api.post('/tasks/', data)
  },
  update(id, params, data) {
    return api.put(`/tasks/${id}?student_id=${params.student_id}`, data)
  }
}


