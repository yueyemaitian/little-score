import api from './index'

export const scoresApi = {
  getSummary(studentId) {
    return api.get('/scores/summary', { params: { student_id: studentId } })
  },
  getIncreases(studentId, limit = 100) {
    return api.get('/scores/increases', { params: { student_id: studentId, limit } })
  },
  getExchanges(studentId, limit = 100) {
    return api.get('/scores/exchanges', { params: { student_id: studentId, limit } })
  },
  createExchange(data) {
    return api.post('/scores/exchanges', data)
  },
  // 奖励选项
  getRewardOptions() {
    return api.get('/scores/reward-options')
  },
  createRewardOption(data) {
    return api.post('/scores/reward-options', data)
  },
  updateRewardOption(id, data) {
    return api.put(`/scores/reward-options/${id}`, data)
  },
  deleteRewardOption(id) {
    return api.delete(`/scores/reward-options/${id}`)
  },
  // 惩罚选项
  getPunishmentOptions() {
    return api.get('/scores/punishment-options')
  },
  createPunishmentOption(data) {
    return api.post('/scores/punishment-options', data)
  },
  updatePunishmentOption(id, data) {
    return api.put(`/scores/punishment-options/${id}`, data)
  },
  deletePunishmentOption(id) {
    return api.delete(`/scores/punishment-options/${id}`)
  }
}


