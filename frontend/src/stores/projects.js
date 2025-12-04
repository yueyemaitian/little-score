import { defineStore } from 'pinia'
import { projectsApi } from '../api/projects'

export const useProjectsStore = defineStore('projects', {
  state: () => ({
    projects: [],
    level1Projects: [],
    level2Projects: []
  }),

  actions: {
    async fetchProjects(level = null, parentId = null) {
      try {
        const params = {}
        if (level) params.level = level
        if (parentId) params.parent_id = parentId
        
        const projects = await projectsApi.getList(params)
        this.projects = projects
        
        if (level === 1) {
          this.level1Projects = projects
        } else if (level === 2) {
          this.level2Projects = projects
        }
        
        return projects
      } catch (error) {
        throw error
      }
    },

    async fetchLevel1Projects() {
      return this.fetchProjects(1)
    },

    async fetchLevel2Projects(parentId) {
      return this.fetchProjects(2, parentId)
    },

    async createProject(data) {
      try {
        const project = await projectsApi.create(data)
        this.projects.push(project)
        if (project.level === 1) {
          this.level1Projects.push(project)
        }
        return project
      } catch (error) {
        throw error
      }
    },

    async updateProject(id, data) {
      try {
        const project = await projectsApi.update(id, data)
        const index = this.projects.findIndex(p => p.id === id)
        if (index !== -1) {
          this.projects[index] = project
        }
        return project
      } catch (error) {
        throw error
      }
    },

    async deleteProject(id) {
      try {
        await projectsApi.delete(id)
        this.projects = this.projects.filter(p => p.id !== id)
        this.level1Projects = this.level1Projects.filter(p => p.id !== id)
        this.level2Projects = this.level2Projects.filter(p => p.id !== id)
      } catch (error) {
        throw error
      }
    }
  }
})


