<template>
  <div class="page-container tasks-container">
    <!-- 学生选择 -->
    <van-cell-group inset style="margin: 12px;">
      <van-field
        v-model="selectedStudentName"
        readonly
        label="选择学生"
        placeholder="选择学生"
        is-link
        @click="showStudentPicker = true"
      />
    </van-cell-group>

    <!-- 筛选条件 -->
    <van-cell-group inset style="margin: 0 12px 12px;">
      <van-field
        :model-value="project1FilterDisplayText"
        readonly
        label="一级项目"
        placeholder="选择一级项目"
        is-link
        @click="showProject1Picker = true"
      >
        <template #right-icon v-if="filters.project_level1_id">
          <van-icon name="clear" @click.stop="clearProject1Filter" />
        </template>
      </van-field>
      <van-field
        :model-value="project2FilterDisplayText"
        readonly
        label="二级项目"
        placeholder="选择二级项目"
        is-link
        @click="showProject2Picker = true"
      >
        <template #right-icon v-if="filters.project_level2_id">
          <van-icon name="clear" @click.stop="clearProject2Filter" />
        </template>
      </van-field>
      <van-field
        :model-value="statusFilterDisplayText"
        readonly
        label="状态"
        placeholder="选择状态"
        is-link
        @click="showStatusPicker = true"
      >
        <template #right-icon v-if="filters.status">
          <van-icon name="clear" @click.stop="clearStatusFilter" />
        </template>
      </van-field>
    </van-cell-group>

    <!-- 新增任务按钮 -->
    <div style="padding: 0 12px 12px;">
      <van-button round block type="primary" icon="plus" @click="handleAddTask">
        新增任务
      </van-button>
    </div>

    <!-- 任务列表 -->
    <van-loading v-if="loading" vertical>加载中...</van-loading>
    <div v-else>
      <van-empty v-if="tasks.length === 0" description="暂无任务" />
      <van-cell-group v-else inset style="margin: 0 12px;">
        <van-cell
          v-for="task in tasks"
          :key="task.id"
          :title="getTaskTitle(task)"
          :label="getTaskLabel(task)"
          is-link
          @click="editTask(task)"
        >
          <template #value>
            <van-tag :type="getStatusType(task.status)">{{ getStatusText(task.status) }}</van-tag>
          </template>
        </van-cell>
      </van-cell-group>
    </div>

    <!-- 添加按钮 -->
    <van-floating-bubble
      axis="xy"
      icon="plus"
      @click="handleAddTask"
    />

    <!-- 学生选择器 -->
    <van-popup v-model:show="showStudentPicker" position="bottom">
      <van-picker
        :columns="studentColumns"
        :default-index="studentDefaultIndex"
        @confirm="onStudentConfirm"
        @cancel="showStudentPicker = false"
        @click-option="(params) => handlePickerDoubleClick(params, onStudentConfirm)"
      />
    </van-popup>

    <!-- 一级项目选择器 -->
    <van-popup v-model:show="showProject1Picker" position="bottom">
      <van-picker
        :columns="project1Columns"
        :default-index="project1DefaultIndex"
        @confirm="onProject1Confirm"
        @cancel="showProject1Picker = false"
        @click-option="(params) => handlePickerDoubleClick(params, onProject1Confirm)"
      />
    </van-popup>

    <!-- 二级项目选择器 -->
    <van-popup v-model:show="showProject2Picker" position="bottom">
      <van-picker
        :columns="project2Columns"
        :default-index="project2DefaultIndex"
        @confirm="onProject2Confirm"
        @cancel="showProject2Picker = false"
        @click-option="(params) => handlePickerDoubleClick(params, onProject2Confirm)"
      />
    </van-popup>

    <!-- 状态选择器 -->
    <van-popup v-model:show="showStatusPicker" position="bottom">
      <van-picker
        :columns="statusColumns"
        :default-index="statusDefaultIndex"
        @confirm="onStatusConfirm"
        @cancel="showStatusPicker = false"
        @click-option="(params) => handlePickerDoubleClick(params, onStatusConfirm)"
      />
    </van-popup>

    <!-- 任务表单弹窗 -->
    <van-popup v-model:show="showTaskForm" position="bottom" :style="{ height: '80%' }">
      <van-nav-bar
        :title="editingTask ? '编辑任务' : '新增任务'"
        left-arrow
        @click-left="handleCloseTaskForm"
      />
      <TaskForm
        v-if="showTaskForm"
        :task="editingTask"
        :student-id="currentStudentId"
        :prefill="prefillData"
        @success="handleTaskSuccess"
        @cancel="handleCloseTaskForm"
      />
    </van-popup>

    <!-- 底部导航 -->
    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showFailToast, showSuccessToast, showToast } from 'vant'
import { tasksApi } from '../api/tasks'
import { projectsApi } from '../api/projects'
import { useStudentsStore } from '../stores/students'
import { useEnumsStore } from '../stores/enums'
import TaskForm from '../components/TaskForm.vue'
import BottomNav from '../components/BottomNav.vue'

const route = useRoute()
const router = useRouter()
const studentsStore = useStudentsStore()

// 预填表单数据（从语音助手传递）
const prefillData = ref(null)

const loading = ref(false)
const tasks = ref([])
const currentStudentId = ref(null)
const selectedStudentName = ref('')
const showStudentPicker = ref(false)
const showProject1Picker = ref(false)
const showProject2Picker = ref(false)
const showStatusPicker = ref(false)
const showTaskForm = ref(false)
const editingTask = ref(null)

const filters = ref({
  project_level1_id: null,
  project_level2_id: null,
  status: null
})

const level1Projects = ref([])
const level2Projects = ref([])

const studentColumns = computed(() => {
  return studentsStore.students.map(s => ({ text: s.name, value: s.id }))
})

const project1Columns = computed(() => {
  return level1Projects.value.map(p => ({ text: p.name, value: p.id }))
})

const project2Columns = computed(() => {
  return level2Projects.value.map(p => ({ text: p.name, value: p.id }))
})

const enumsStore = useEnumsStore()

const statusColumns = computed(() => {
  return enumsStore.taskStatus
})

// 筛选条件显示文本（中文标签）
const project1FilterDisplayText = computed(() => {
  if (!filters.value.project_level1_id) return ''
  const option = level1Projects.value.find(p => p.id === filters.value.project_level1_id)
  return option ? option.name : ''
})

const project2FilterDisplayText = computed(() => {
  if (!filters.value.project_level2_id) return ''
  const option = level2Projects.value.find(p => p.id === filters.value.project_level2_id)
  return option ? option.name : ''
})

const statusFilterDisplayText = computed(() => {
  if (!filters.value.status) return ''
  const option = enumsStore.taskStatus.find(s => s.value === filters.value.status)
  return option ? option.text : filters.value.status
})

// 默认索引（用于设置初始选中项）
const studentDefaultIndex = computed(() => {
  if (!currentStudentId.value) return 0
  const index = studentsStore.students.findIndex(s => s.id === currentStudentId.value)
  return index >= 0 ? index : 0
})

const project1DefaultIndex = computed(() => {
  if (!filters.value.project_level1_id) return 0
  const index = level1Projects.value.findIndex(p => p.id === filters.value.project_level1_id)
  return index >= 0 ? index : 0
})

const project2DefaultIndex = computed(() => {
  if (!filters.value.project_level2_id) return 0
  const index = level2Projects.value.findIndex(p => p.id === filters.value.project_level2_id)
  return index >= 0 ? index : 0
})

const statusDefaultIndex = computed(() => {
  if (!filters.value.status) return 0
  const index = enumsStore.taskStatus.findIndex(s => s.value === filters.value.status)
  return index >= 0 ? index : 0
})

// 双击确认处理（Vant picker 默认支持双击，这里添加额外处理）
let lastClickTime = 0
let lastClickIndex = -1
const DOUBLE_CLICK_DELAY = 300 // 300ms 内的两次点击视为双击

const handlePickerDoubleClick = ({ currentOption, selectedIndex: idx }, confirmCallback) => {
  const now = Date.now()
  if (now - lastClickTime < DOUBLE_CLICK_DELAY && idx === lastClickIndex) {
    // 双击确认
    if (confirmCallback) {
      confirmCallback({ selectedOptions: [currentOption] })
    }
    lastClickTime = 0
    lastClickIndex = -1
  } else {
    lastClickTime = now
    lastClickIndex = idx
  }
}

const fetchTasks = async () => {
  if (!currentStudentId.value) return
  
  loading.value = true
  try {
    const hasFilter =
      Boolean(filters.value.project_level1_id) ||
      Boolean(filters.value.project_level2_id) ||
      Boolean(filters.value.status)

    const params = {
      student_id: currentStudentId.value,
      include_all_status: !hasFilter
    }

    if (filters.value.project_level1_id) {
      params.project_level1_id = filters.value.project_level1_id
    }
    if (filters.value.project_level2_id) {
      params.project_level2_id = filters.value.project_level2_id
    }
    if (filters.value.status) {
      params.status = filters.value.status
    }
    const data = await tasksApi.getList(params)
    tasks.value = data
  } catch (error) {
    showFailToast('加载任务失败')
  } finally {
    loading.value = false
  }
}

const fetchProjects = async () => {
  try {
    const [level1, level2] = await Promise.all([
      projectsApi.getList({ level: 1 }),
      filters.value.project_level1_id
        ? projectsApi.getList({ level: 2, parent_id: filters.value.project_level1_id })
        : Promise.resolve([])
    ])
    level1Projects.value = level1
    level2Projects.value = level2
  } catch (error) {
    showFailToast('加载项目失败')
  }
}

const onStudentConfirm = ({ selectedOptions }) => {
  currentStudentId.value = selectedOptions[0].value
  selectedStudentName.value = selectedOptions[0].text
  studentsStore.setCurrentStudent(currentStudentId.value)
  showStudentPicker.value = false
  fetchTasks()
}

const onProject1Confirm = ({ selectedOptions }) => {
  if (selectedOptions && selectedOptions.length > 0) {
    filters.value.project_level1_id = selectedOptions[0].value
    filters.value.project_level2_id = null
  }
  showProject1Picker.value = false
  fetchProjects()
  fetchTasks()
}

const onProject2Confirm = ({ selectedOptions }) => {
  if (selectedOptions && selectedOptions.length > 0) {
    filters.value.project_level2_id = selectedOptions[0].value
  }
  showProject2Picker.value = false
  fetchTasks()
}

const onStatusConfirm = ({ selectedOptions }) => {
  if (selectedOptions && selectedOptions.length > 0) {
    filters.value.status = selectedOptions[0].value
  }
  showStatusPicker.value = false
  fetchTasks()
}

// 清除筛选条件的方法
const clearProject1Filter = () => {
  filters.value.project_level1_id = null
  filters.value.project_level2_id = null
  fetchTasks()
}

const clearProject2Filter = () => {
  filters.value.project_level2_id = null
  fetchTasks()
}

const clearStatusFilter = () => {
  filters.value.status = null
  fetchTasks()
}

const getTaskTitle = (task) => {
  const primaryName =
    task.project_level1_name ||
    level1Projects.value.find(p => p.id === task.project_level1_id)?.name ||
    `项目${task.project_level1_id}`
  let title = primaryName

  if (task.project_level2_id) {
    const secondaryName =
      task.project_level2_name ||
      level2Projects.value.find(p => p.id === task.project_level2_id)?.name ||
      `项目${task.project_level2_id}`
    title += ` - ${secondaryName}`
  }
  return title
}

const getTaskLabel = (task) => {
  const parts = []
  if (task.rating) parts.push(`评分: ${task.rating}`)
  if (task.reward_points) parts.push(`奖励: ${task.reward_points}积分`)
  return parts.join(' | ')
}

const getStatusText = (status) => {
  const option = enumsStore.taskStatus.find(s => s.value === status)
  return option ? option.text : status
}

const getStatusType = (status) => {
  // 根据状态值返回对应的标签类型
  const statusOption = enumsStore.taskStatus.find(s => s.value === status)
  if (!statusOption) return 'default'
  
  // 根据状态值映射到标签类型
  const typeMap = {
    'not_started': 'default',
    'in_progress': 'primary',
    'completed': 'success',
    'canceled': 'danger'
  }
  return typeMap[status] || 'default'
}

const editTask = (task) => {
  editingTask.value = task
  showTaskForm.value = true
}

const handleTaskSuccess = () => {
  showTaskForm.value = false
  editingTask.value = null
  prefillData.value = null
  fetchTasks()
}

const handleCloseTaskForm = () => {
  showTaskForm.value = false
  editingTask.value = null
  prefillData.value = null
}

const handleAddTask = () => {
  if (!currentStudentId.value) {
    showFailToast('请先选择学生')
    return
  }
  editingTask.value = null
  showTaskForm.value = true
}

// 处理预填数据和打开表单的函数
const handlePrefillData = async () => {
  // 处理 URL 参数中的 student_id（从语音助手跳转过来）
  if (route.query.student_id) {
    const studentId = parseInt(route.query.student_id)
    const student = studentsStore.students.find(s => s.id === studentId)
    if (student) {
      currentStudentId.value = studentId
      selectedStudentName.value = student.name
      studentsStore.setCurrentStudent(studentId)
    }
  }
  
  // 检查是否有预填数据（从语音助手跳转）
  if (route.query.action === 'add' && route.query.prefill) {
    try {
      prefillData.value = JSON.parse(decodeURIComponent(route.query.prefill))
      // 确保已选择学生后再打开表单
      if (currentStudentId.value) {
        showTaskForm.value = true
        showToast({
          message: '已从语音助手预填表单，请确认信息',
          position: 'top',
          duration: 3000
        })
      } else {
        showFailToast('请先选择学生')
      }
      // 清除 URL 参数，避免刷新页面重复打开
      router.replace({ path: '/tasks' })
    } catch (e) {
      console.error('解析预填数据失败:', e)
    }
  }
}

watch(() => filters.value.project_level1_id, async (newVal) => {
  if (newVal) {
    const projects = await projectsApi.getList({ level: 2, parent_id: newVal })
    level2Projects.value = projects
  } else {
    level2Projects.value = []
  }
})

// 监听路由变化，处理预填数据（当用户在任务页面时，路由参数变化也能响应）
watch(() => route.query, async (newQuery) => {
  if (newQuery.action === 'add' && newQuery.prefill) {
    await handlePrefillData()
  }
}, { deep: true })

onMounted(async () => {
  await studentsStore.fetchStudents()
  
  // 初始化学生选择
  if (studentsStore.students.length > 0) {
    if (!currentStudentId.value) {
      currentStudentId.value = studentsStore.currentStudent.id
      selectedStudentName.value = studentsStore.currentStudent.name
    }
  }
  
  await fetchProjects()
  await fetchTasks()
  
  // 处理预填数据
  await handlePrefillData()
})
</script>

<style scoped>
.tasks-container {
  width: 100%;
}

.tasks-content {
  width: 100%;
  padding: 12px;
}

@media (min-width: 768px) {
  .tasks-content {
    padding: 16px;
  }
}

@media (min-width: 1024px) {
  .tasks-content {
    padding: 24px;
    max-width: 1000px;
    margin: 0 auto;
  }
}

/* 确保 picker 支持鼠标滚轮滚动和双击确认 */
:deep(.van-picker-column) {
  cursor: pointer;
}

/* 支持双击确认 */
:deep(.van-picker-column__item) {
  cursor: pointer;
  user-select: none;
}
</style>

