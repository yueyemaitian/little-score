import { defineStore } from 'pinia'
import { enumsApi } from '../api/enums'

export const useEnumsStore = defineStore('enums', {
  state: () => ({
    enums: null,
    loaded: false
  }),

  getters: {
    taskStatus: (state) => {
      if (!state.enums) return []
      return state.enums.task_status.map(item => ({
        text: item.label,
        value: item.value
      }))
    },
    taskRating: (state) => {
      if (!state.enums) return []
      return state.enums.task_rating.map(item => ({
        text: item.label,
        value: item.value
      }))
    },
    rewardType: (state) => {
      if (!state.enums) return []
      return state.enums.reward_type.map(item => ({
        text: item.label,
        value: item.value
      }))
    },
    rewardPoints: (state) => {
      if (!state.enums) return []
      return state.enums.reward_points.map(item => ({
        text: item.label,
        value: item.value
      }))
    },
    gender: (state) => {
      if (!state.enums) return []
      return state.enums.gender.map(item => ({
        text: item.label,
        value: item.value
      }))
    },
    educationStage: (state) => {
      if (!state.enums) return []
      return state.enums.education_stage.map(item => ({
        text: item.label,
        value: item.value
      }))
    },
    projectLevel: (state) => {
      if (!state.enums) return []
      return state.enums.project_level.map(item => ({
        text: item.label,
        value: item.value
      }))
    }
  },

  actions: {
    async fetchEnums() {
      if (this.loaded) return this.enums
      
      try {
        const enums = await enumsApi.getEnums()
        this.enums = enums
        this.loaded = true
        return enums
      } catch (error) {
        console.error('加载枚举值失败:', error)
        throw error
      }
    }
  }
})

