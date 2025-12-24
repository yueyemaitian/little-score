<template>
  <div class="tasks-container">
    <!-- 学生头部（含选择） -->
    <StudentHeader
      :student="currentStudent"
      :all-students="studentsStore.students"
      @switch="handleStudentSwitch"
      @add="handleAddStudent"
    >
      <template #right-icon>
        <div class="header-icon-wrapper-add" @click.stop="handleAddTask">
          <van-icon
            name="plus"
            class="header-icon-add"
          />
        </div>
      </template>
    </StudentHeader>

    <!-- 搜索框 -->
    <div class="search-section">
      <van-search
        v-model="searchKeyword"
        placeholder="搜索一级项目、二级项目、状态..."
        shape="round"
      />
    </div>

    <!-- 页签 -->
    <van-tabs v-model:active="activeTab" @change="handleTabChange" shrink>
      <van-tab title="全部" name="all" />
      <van-tab
        v-for="project in level1Projects"
        :key="project.id"
        :title="project.name"
        :name="String(project.id)"
      />
    </van-tabs>

    <!-- 内容区域 -->
    <div class="tasks-scroll">

    <!-- 任务列表 -->
      <div v-if="loading" class="loading-container">
        <van-loading vertical>加载中...</van-loading>
      </div>
      <div v-else-if="filteredTasks.length === 0" class="empty-container">
        <van-empty description="暂无任务" />
      </div>
      <div v-else class="tasks-list">
        <div
          v-for="task in filteredTasks"
          :key="task.id"
          class="task-card"
          @click="editTask(task)"
        >
          <!-- 左侧图标（显示emoji或形状+文字） -->
          <div 
            class="task-icon" 
            :class="getTaskIconShape(task)"
            :style="{ background: getTaskIconColor(task) }"
          >
            <span :class="hasProjectIcon(task) ? 'task-icon-emoji' : 'task-icon-text'">
              {{ getTaskIconText(task) }}
            </span>
          </div>
          
          <!-- 中间内容 -->
          <div class="task-content">
            <div class="task-title">{{ getTaskTitle(task) }}</div>
            <div class="task-meta">
              <span class="task-time">{{ getTaskTime(task) }}</span>
              <span v-if="getTaskRewardText(task)" :class="getTaskRewardClass(task)" class="task-reward">
                {{ getTaskRewardText(task) }}
              </span>
            </div>
          </div>
          
          <!-- 右侧状态按钮 -->
          <div class="task-action">
            <div
              class="task-status-btn"
              :class="getStatusButtonClass(task)"
              @click.stop="handleStatusClick(task)"
            >
              <van-icon v-if="isClaimed(task)" name="success" />
              <span>{{ getStatusButtonText(task) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>


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
import StudentHeader from '../components/StudentHeader.vue'
import { formatLocalDateTime } from '../utils/date'

const route = useRoute()
const router = useRouter()
const studentsStore = useStudentsStore()

// 预填表单数据（从语音助手传递）
const prefillData = ref(null)

const loading = ref(false)
const allTasks = ref([]) // 存储所有任务数据
const filteredTasks = ref([]) // 过滤后的任务列表
const currentStudentId = ref(null)
const showTaskForm = ref(false)
const editingTask = ref(null)

// 搜索关键词
const searchKeyword = ref('')

// 当前选中的页签（'all' 或一级项目ID）
const activeTab = ref('all')

const level1Projects = ref([])
const level2Projects = ref([])

const currentStudent = computed(() => {
  if (!studentsStore.students.length) return null
  return studentsStore.students.find(s => s.id === currentStudentId.value)
})

const enumsStore = useEnumsStore()

// 获取任务状态文本
const getStatusText = (statusValue) => {
  const option = enumsStore.taskStatus.find(s => s.value === statusValue)
  return option ? option.text : statusValue
}

// 获取一级项目名称
const getProject1Name = (task) => {
  return task.project_level1_name ||
    level1Projects.value.find(p => p.id === task.project_level1_id)?.name ||
    ''
}

// 获取二级项目名称
const getProject2Name = (task) => {
  return task.project_level2_name ||
    level2Projects.value.find(p => p.id === task.project_level2_id)?.name ||
    ''
}

// 过滤任务列表
const filterTasks = () => {
  let result = [...allTasks.value]
  
  // 页签过滤：如果选中了具体的一级项目，只显示该项目的任务
  if (activeTab.value !== 'all') {
    const project1Id = parseInt(activeTab.value)
    result = result.filter(task => task.project_level1_id === project1Id)
  }
  
  // 搜索关键词过滤
  if (searchKeyword.value && searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.trim().toLowerCase()
    result = result.filter(task => {
      // 搜索一级项目名称
      const project1Name = getProject1Name(task).toLowerCase()
      if (project1Name.includes(keyword)) return true
      
      // 搜索二级项目名称
      const project2Name = getProject2Name(task).toLowerCase()
      if (project2Name.includes(keyword)) return true
      
      // 搜索状态
      const statusText = getStatusText(task.status).toLowerCase()
      if (statusText.includes(keyword)) return true
      
      return false
    })
  }
  
  filteredTasks.value = result
}

// 页签切换处理
const handleTabChange = () => {
  filterTasks()
}

// 监听搜索关键词变化
watch(searchKeyword, () => {
  filterTasks()
})

const fetchTasks = async () => {
  if (!currentStudentId.value) return
  
  loading.value = true
  try {
    // 默认逻辑：查询最近一个月完成的任务 + 未开始和进行中的任务
    const oneMonthAgo = new Date()
    oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1)
    
    // 查询1：最近一个月完成的任务
    const completedParams = {
      student_id: currentStudentId.value,
      completed_after: oneMonthAgo.toISOString(),
      include_all_status: true
    }
    const completedTasks = await tasksApi.getList(completedParams)
    
    // 查询2：未开始和进行中的任务
    const inProgressParams = {
      student_id: currentStudentId.value,
      include_all_status: false
    }
    const inProgressTasks = await tasksApi.getList(inProgressParams)
    
    // 合并结果，去重（按ID）
    const taskMap = new Map()
    ;[...completedTasks, ...inProgressTasks].forEach(task => {
      if (!taskMap.has(task.id)) {
        taskMap.set(task.id, task)
      }
    })
    
    // 按创建时间倒序排序，限制最多100条
    const tasksArray = Array.from(taskMap.values())
    tasksArray.sort((a, b) => {
      const timeA = new Date(a.created_at).getTime()
      const timeB = new Date(b.created_at).getTime()
      return timeB - timeA
    })
    
    allTasks.value = tasksArray.slice(0, 100)
    filterTasks() // 应用过滤
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
      projectsApi.getList({ level: 2 })
    ])
    level1Projects.value = level1
    level2Projects.value = level2
  } catch (error) {
    showFailToast('加载项目失败')
  }
}

const handleStudentSwitch = (studentId) => {
  currentStudentId.value = studentId
  studentsStore.setCurrentStudent(studentId)
  fetchTasks()
}

const handleAddStudent = () => {
  router.push({ path: '/profile', query: { action: 'add-student' } })
}

const getTaskTitle = (task) => {
  const primaryName =
    task.project_level1_name ||
    level1Projects.value.find(p => p.id === task.project_level1_id)?.name ||
    `项目${task.project_level1_id}`

    const secondaryName =
      task.project_level2_name ||
      level2Projects.value.find(p => p.id === task.project_level2_id)?.name ||
    ''
  
  let title = primaryName
  if (secondaryName) {
    title = `${primaryName} - ${secondaryName}`
  }
  
  // 如果已完成且有评分，添加评分
  if (task.status === 'completed' && task.rating) {
    title = `${title} （${task.rating}）`
  }
  
  return title
}

// 获取任务时间（完成时间或更新时间）
const getTaskTime = (task) => {
  // 如果已完成，显示完成时间（updated_at），否则显示最后更新时间
  const timeStr = task.updated_at || task.created_at
  if (!timeStr) return ''
  
  // 格式化为 yyyy-MM-dd hh:MM
  const date = new Date(timeStr)
  if (Number.isNaN(date.getTime())) return ''
  
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

// 获取奖励/惩罚文本
const getTaskRewardText = (task) => {
  if (task.status !== 'completed') {
    return null
  }
  
  if (task.reward_type === 'reward' && task.reward_points) {
    return `奖励 +${task.reward_points}`
  }
  
  if (task.reward_type === 'punish' && task.punishment_option_id) {
    // 这里可以显示惩罚选项名称，暂时显示"惩罚"
    return '惩罚'
  }
  
  return null
}

// 获取奖励/惩罚样式类
const getTaskRewardClass = (task) => {
  if (task.reward_type === 'reward') {
    return 'task-reward-reward'
  }
  if (task.reward_type === 'punish') {
    return 'task-reward-punish'
  }
  return ''
}

// 从文本中提取关键字（1-2个字）
const extractKeyword = (text) => {
  if (!text) return '任'
  
  // 移除常见后缀词
  const cleaned = text.replace(/[管理|设置|选项|任务|项目]$/g, '')
  
  // 如果是2个字，直接返回
  if (cleaned.length === 2) {
    return cleaned
  }
  
  // 如果是1个字，直接返回
  if (cleaned.length === 1) {
    return cleaned
  }
  
  // 如果超过2个字，尝试提取关键字
  // 优先提取前2个字
  if (cleaned.length >= 2) {
    return cleaned.substring(0, 2)
  }
  
  // 如果包含常见关键词，提取关键词
  const keywords = ['学习', '阅读', '数学', '英语', '家务', '音乐', '运动', '艺术', '兴趣', '钢琴', '作业', '练习', '整理', '打扫', '跑步', '跳绳', '画画', '绘画']
  for (const keyword of keywords) {
    if (cleaned.includes(keyword)) {
      return keyword.length <= 2 ? keyword : keyword.substring(0, 2)
    }
  }
  
  // 默认返回前2个字
  return cleaned.substring(0, 2) || '任'
}

// 项目名称到emoji的映射表（关键字匹配）
const projectIconMap = {
  // 学习类
  '作业': '📝',
  '考试': '📋',
  '形评': '📋',
  '评测': '📋',
  '测验': '📋',
  '测试': '📋',
  '验收': '📋',
  '发言': '🗣️',
  '阅读': '📚',
  '课作': '✏️',
  '语文': '📝',
  '英语': '🔤',
  '数学': '🔢',
  
  // 生活类
  '作息': '⏰',
  '整理': '📦',
  '卫生': '🧼',
  '运动': '🏃',
  '体育': '🏃',
  '武术': '🥋',
  '跆拳道': '🥋',
  '羽毛球': '🏸',
  '乒乓球': '🏓',
  '足球': '⚽',
  '游泳': '🏊',
  '跑步': '🏃',
  '跳绳': '🦘',
  '家务': '🏠',
  '收纳': '📦',
  
  // 品德类
  '自律': '✨',
  '进步': '📈',
  
  // 兴趣类
  '钢琴': '🎹',
  '兴趣': '⭐',
}

// 一级项目ID到背景色的映射表（按项目分配颜色）
// 颜色方案：为每个一级项目分配不同的颜色
const projectIdColorMap = new Map()

// 预定义的颜色列表（浅色系，避免蓝色和青色，确保颜色区分度）
const colorPalette = [
  'linear-gradient(135deg, #c5cae9, #b0bec5)', // 浅靛蓝色
  'linear-gradient(135deg, #c8e6c9, #a5d6a7)', // 浅绿色
  'linear-gradient(135deg, #ffe0b2, #ffcc80)', // 浅橙色
  'linear-gradient(135deg, #e1bee7, #ce93d8)', // 浅紫色
  'linear-gradient(135deg, #fce4ec, #f8bbd0)', // 浅粉色
  'linear-gradient(135deg, #ffccbc, #ffab91)', // 浅橙红色
  'linear-gradient(135deg, #e0f2f1, #b2dfdb)', // 浅青绿色
  'linear-gradient(135deg, #e8eaf6, #c5cae9)', // 浅靛蓝色（更浅）
  'linear-gradient(135deg, #fff9c4, #fff59d)', // 浅黄色
  'linear-gradient(135deg, #ffe0b2, #ffccbc)', // 浅桃色
]

// 根据一级项目ID获取背景色
const getProjectIdColor = (projectId) => {
  if (!projectId) {
    return colorPalette[0] // 默认浅靛蓝色
  }
  
  // 如果已经为该项目分配过颜色，直接返回
  if (projectIdColorMap.has(projectId)) {
    return projectIdColorMap.get(projectId)
  }
  
  // 根据项目ID取模，分配到颜色列表中的颜色
  const colorIndex = (projectId - 1) % colorPalette.length
  const color = colorPalette[colorIndex]
  
  // 缓存该项目的颜色
  projectIdColorMap.set(projectId, color)
  
  return color
}

// 根据项目名称获取对应的emoji图标，如果匹配不到返回null
const getProjectIcon = (projectName) => {
  if (!projectName) return null
  
  const name = projectName.trim()
  
  // 精确匹配
  if (projectIconMap[name]) {
    return projectIconMap[name]
  }
  
  // 模糊匹配：检查项目名称是否包含关键词（优先匹配较长的关键词）
  const sortedKeywords = Object.keys(projectIconMap).sort((a, b) => b.length - a.length)
  for (const keyword of sortedKeywords) {
    if (name.includes(keyword)) {
      return projectIconMap[keyword]
    }
  }
  
  // 匹配不到返回null
  return null
}

// 根据任务获取对应的emoji图标（优先匹配二级项目）
const getTaskProjectIcon = (task) => {
  // 先尝试匹配二级项目名称
  const secondaryName = getProject2Name(task)
  if (secondaryName) {
    const icon = getProjectIcon(secondaryName)
    if (icon) {
      return icon
    }
  }
  
  // 如果二级项目匹配不到，再匹配一级项目名称
  const primaryName = getProject1Name(task)
  return getProjectIcon(primaryName)
}

// 根据任务获取对应的背景色
// 如果有预设图标，按一级项目ID分配颜色；如果没有匹配到图标，使用浅蓝色
const getTaskProjectColor = (task) => {
  // 如果没有匹配到预设图标，使用浅蓝色
  if (!hasProjectIcon(task)) {
    return 'linear-gradient(135deg, #90caf9, #81d4fa)' // 浅蓝色
  }
  
  // 如果有预设图标，按一级项目ID分配颜色
  const project1Id = task.project_level1_id
  return getProjectIdColor(project1Id)
}

// 获取任务图标文本（返回emoji或文字）
const getTaskIconText = (task) => {
  // 优先尝试从二级项目获取emoji图标
  const icon = getTaskProjectIcon(task)
  if (icon) {
    return icon
  }
  
  // 如果匹配不到emoji，返回一级项目的第一个字
  const primaryName = getProject1Name(task)
  if (primaryName && primaryName.length > 0) {
    return primaryName[0]
  }
  
  return '任'
}

// 判断任务是否有预设的emoji图标
const hasProjectIcon = (task) => {
  return getTaskProjectIcon(task) !== null
}

// 获取任务图标的背景色（按一级项目ID分配）
const getTaskIconColor = (task) => {
  return getTaskProjectColor(task)
}

// 根据一级项目ID返回不同的形状样式
// 如果没有匹配到预设图标，返回空字符串使用默认圆形
const getTaskIconShape = (task) => {
  // 如果没有匹配到预设的emoji图标，返回空字符串，使用默认圆形
  if (!hasProjectIcon(task)) {
    return ''
  }
  
  // 如果有预设图标，也不使用形状（保持圆形）
  return ''
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

const isClaimed = (task) => {
  // 判断任务是否已领取奖励（已完成且有奖励积分）
  return task.status === 'completed' && task.reward_type === 'reward' && task.reward_points
}

const getStatusButtonText = (task) => {
  if (isClaimed(task)) {
    return '已领'
  }
  const statusText = getStatusText(task.status)
  // 将状态文本转换为按钮文本
  if (statusText === '已完成') {
    return '完成'
  }
  return statusText
}

const getStatusButtonClass = (task) => {
  if (isClaimed(task)) {
    return 'status-claimed'
  }
  if (task.status === 'completed') {
    return 'status-completed'
  }
  return 'status-default'
}

const handleStatusClick = (task) => {
  // 如果任务已完成，点击状态按钮不执行任何操作
  if (task.status === 'completed') {
    return
  }
  // 否则编辑任务
  editTask(task)
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
    }
  }
  
  // 不设置默认的 completed_after，让 fetchTasks 使用默认逻辑
  // （显示最近一个月完成的任务 + 未开始和进行中的任务）
  
  await fetchProjects()
  await fetchTasks()
  
  // 处理预填数据
  await handlePrefillData()
})
</script>

<style scoped>
.tasks-container {
  width: 100%;
  background: #f4f5f7;
  min-height: 100%;
}

.tasks-scroll {
  padding: 8px 8px 8px;
  box-sizing: border-box;
}

.loading-container,
.empty-container {
  padding: 40px 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
  cursor: pointer;
  transition: transform 0.12s ease-out, box-shadow 0.12s ease-out;
}

.task-card:active {
  transform: translateY(1px) scale(0.99);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
}

.task-icon {
  width: 38.4px;
  height: 38.4px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #ffffff;
  /* 默认颜色（会被内联样式或各形状的颜色覆盖） */
  background: linear-gradient(135deg, #9fa8da, #7986cb);
}

.task-icon-emoji {
  font-size: 20px;
  line-height: 1;
  user-select: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.task-icon-text {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.2;
  text-align: center;
  letter-spacing: 0.5px;
  user-select: none;
  display: block;
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 0 2px;
}

/* 10种不同的图标形状 - 用于没有预设emoji的项目 */
/* 正方形和菱形放在最后两位（shape-9和shape-10） */

/* 形状1: 圆角矩形（中等圆角） */
.task-icon.shape-1 {
  border-radius: 12px;
  /* 背景色通过内联样式动态设置 */
}

/* 形状2: 六边形 */
.task-icon.shape-2 {
  border-radius: 0;
  clip-path: polygon(30% 0%, 70% 0%, 100% 50%, 70% 100%, 30% 100%, 0% 50%);
  /* 背景色通过内联样式动态设置 */
}

/* 形状3: 五边形 */
.task-icon.shape-3 {
  border-radius: 0;
  clip-path: polygon(50% 0%, 100% 38%, 82% 100%, 18% 100%, 0% 38%);
  /* 背景色通过内联样式动态设置 */
}

/* 形状4: 圆角矩形（大圆角） */
.task-icon.shape-4 {
  border-radius: 18px;
  /* 背景色通过内联样式动态设置 */
}

/* 形状5: 横向矩形（宽高比不同） */
.task-icon.shape-5 {
  border-radius: 8px;
  width: 45px;
  height: 30px;
  /* 背景色通过内联样式动态设置 */
}

/* 形状6: 纵向矩形（宽高比不同） */
.task-icon.shape-6 {
  border-radius: 8px;
  width: 30px;
  height: 45px;
  /* 背景色通过内联样式动态设置 */
}

/* 形状7: 八边形 */
.task-icon.shape-7 {
  border-radius: 0;
  clip-path: polygon(30% 0%, 70% 0%, 100% 30%, 100% 70%, 70% 100%, 30% 100%, 0% 70%, 0% 30%);
  /* 背景色通过内联样式动态设置 */
}

/* 形状8: 圆角矩形（小圆角） */
.task-icon.shape-8 {
  border-radius: 6px;
  /* 背景色通过内联样式动态设置 */
}

/* 形状9: 直角方形 */
.task-icon.shape-9 {
  border-radius: 0;
  /* 背景色通过内联样式动态设置 */
}

/* 形状10: 菱形 */
.task-icon.shape-10 {
  border-radius: 0;
  transform: rotate(45deg);
  /* 背景色通过内联样式动态设置 */
}

.task-icon.shape-10 .task-icon-text {
  transform: rotate(-45deg);
}


.task-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.task-title {
  font-size: 14px;
  font-weight: 500;
  color: #111827;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: #6b7280;
  flex-wrap: wrap;
}

.task-time {
  color: #6b7280;
}

.task-reward {
  font-weight: 500;
}

.task-reward-reward {
  color: #4a90e2;
}

.task-reward-punish {
  color: #ef5350;
}

.task-action {
  flex-shrink: 0;
}

.task-status-btn {
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
  transition: all 0.2s;
}

.task-status-btn.status-default {
  background: #f3f4f6;
  color: #6b7280;
}

.task-status-btn.status-completed {
  background: #f3f4f6;
  color: #6b7280;
}

.task-status-btn.status-claimed {
  background: #10b981;
  color: #ffffff;
}

.task-status-btn.status-claimed :deep(.van-icon) {
  font-size: 14px;
}

/* 搜索框区域 */
.search-section {
  background: #ffffff;
  padding: 8px 12px;
}

/* 页签样式 */
:deep(.van-tabs) {
  background: #ffffff;
}

:deep(.van-tabs__wrap) {
  border-bottom: 1px solid #f0f0f0;
}

/* 新增图标样式（与首页记一笔图标背景色一致） */
.header-icon-wrapper-add {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #42a5f5, #1e88e5);
  cursor: pointer;
  transition: transform 0.12s ease-out, box-shadow 0.12s ease-out;
}

.header-icon-wrapper-add:active {
  transform: translateY(1px) scale(0.95);
}

.header-icon-add {
  font-size: 16px;
  color: #ffffff;
}

/* 确保任务页的所有弹窗都在底部导航之上 */
.tasks-container :deep(.van-popup) {
  z-index: 2000 !important;
}

.tasks-container :deep(.van-overlay) {
  z-index: 1999 !important;
}
</style>

