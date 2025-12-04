import { defineStore } from 'pinia'
import { studentsApi } from '../api/students'

export const useStudentsStore = defineStore('students', {
  state: () => ({
    students: [],
    currentStudentId: null
  }),

  getters: {
    currentStudent: (state) => {
      return state.students.find(s => s.id === state.currentStudentId) || state.students[0]
    }
  },

  actions: {
    async fetchStudents() {
      try {
        const students = await studentsApi.getList()
        this.students = students
        if (students.length > 0 && !this.currentStudentId) {
          this.currentStudentId = students[0].id
        }
        return students
      } catch (error) {
        throw error
      }
    },

    async createStudent(data) {
      try {
        const student = await studentsApi.create(data)
        this.students.push(student)
        if (!this.currentStudentId) {
          this.currentStudentId = student.id
        }
        return student
      } catch (error) {
        throw error
      }
    },

    async updateStudent(id, data) {
      try {
        const student = await studentsApi.update(id, data)
        const index = this.students.findIndex(s => s.id === id)
        if (index !== -1) {
          this.students[index] = student
        }
        return student
      } catch (error) {
        throw error
      }
    },

    setCurrentStudent(id) {
      this.currentStudentId = id
    }
  }
})


