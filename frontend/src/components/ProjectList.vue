<template>
  <div class="project-list">
    <div style="padding: 12px;">
      <van-button round block type="primary" icon="plus" @click="handleAddProject">
        新增{{ level === '1' ? '一级' : '二级' }}项目
      </van-button>
    </div>

    <van-loading v-if="loading" vertical>加载中...</van-loading>
    <div v-else class="list-content">
      <van-empty v-if="projects.length === 0" description="暂无项目" />
      <van-cell-group v-else inset style="margin: 12px;">
        <van-cell
          v-for="project in projects"
          :key="project.id"
          :title="project.name"
          :label="project.description"
          is-link
          @click="editProject(project)"
        >
          <template #right-icon>
            <van-icon name="delete-o" @click.stop="handleDelete(project)" />
          </template>
        </van-cell>
      </van-cell-group>
    </div>

    <!-- 项目表单弹窗 -->
    <van-popup v-model:show="showProjectForm" position="bottom" :style="{ height: '60%' }">
      <van-nav-bar
        :title="editingProject ? '编辑项目' : '新增项目'"
        left-arrow
        @click-left="showProjectForm = false"
      />
      <ProjectForm
        v-if="showProjectForm"
        :project="editingProject"
        :level="level"
        @success="handleProjectSuccess"
        @cancel="showProjectForm = false"
      />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { showConfirmDialog, showSuccessToast, showFailToast } from 'vant'
import { projectsApi } from '../api/projects'
import { extractErrorMessage } from '../utils/errorHandler'
import ProjectForm from './ProjectForm.vue'

const props = defineProps({
  level: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close'])

const loading = ref(false)
const projects = ref([])
const showProjectForm = ref(false)
const editingProject = ref(null)

const fetchProjects = async () => {
  loading.value = true
  try {
    const params = { level: parseInt(props.level) }
    projects.value = await projectsApi.getList(params)
  } catch (error) {
    console.error('加载项目失败:', error)
    showFailToast('加载项目失败')
  } finally {
    loading.value = false
  }
}

const handleAddProject = () => {
  editingProject.value = null
  showProjectForm.value = true
}

const editProject = (project) => {
  editingProject.value = project
  showProjectForm.value = true
}

const handleDelete = async (project) => {
  try {
    await showConfirmDialog({
      title: '删除项目',
      message: `确定要删除项目 "${project.name}" 吗？`
    })
    await projectsApi.delete(project.id)
    showSuccessToast('删除成功')
    fetchProjects()
  } catch (error) {
    if (error !== 'cancel') {
      const message = extractErrorMessage(error)
      showFailToast(message)
    }
  }
}

const handleProjectSuccess = () => {
  showProjectForm.value = false
  editingProject.value = null
  fetchProjects()
}

watch(() => props.level, () => {
  fetchProjects()
})

onMounted(() => {
  fetchProjects()
})
</script>

<style scoped>
.project-list {
  min-height: 100%;
  background: #f7f8fa;
  padding-bottom: 20px;
  width: 100%;
}

@media (min-width: 1024px) {
  .project-list {
    max-width: 1000px;
    margin: 0 auto;
  }
}

.list-content {
  padding: 12px;
}

@media (min-width: 768px) {
  .list-content {
    padding: 16px;
  }
}

@media (min-width: 1024px) {
  .list-content {
    padding: 24px;
  }
}
</style>

