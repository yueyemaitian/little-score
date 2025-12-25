<template>
  <div class="home-container">
    <!-- 顶部 App 头部（点击可选择/新增孩子） -->
    <div class="home-header" @click="openStudentPicker">
      <div class="header-left">
        <div class="header-avatar" :style="{ backgroundImage: `url(${getAvatarUrl()})` }">
        </div>
        <div class="header-info" v-if="currentStudent">
          <div class="header-name">{{ currentStudent.student.name }}</div>
          <div class="header-meta">
            {{ getGradeDisplay(currentStudent.student) }}
          </div>
        </div>
        <van-icon name="arrow-down" class="header-arrow" />
      </div>
    </div>

    <!-- 孩子下拉选择 / 新增 -->
    <van-popup v-model:show="showStudentPicker" position="bottom" round>
      <van-picker
        title="选择孩子"
        :columns="studentColumns"
        @confirm="onStudentConfirm"
        @cancel="showStudentPicker = false"
        @click-option="handlePickerOptionClick"
      />
    </van-popup>

    <!-- 内容区：原生 App 风格滚动区域 -->
    <div class="home-scroll">
      <div v-if="loading" class="scroll-loading">
        <van-loading vertical>加载中...</van-loading>
      </div>
      <van-empty
        v-else-if="students.length === 0"
        description="暂无学生数据，请先添加孩子"
      />

      <div v-else-if="currentStudent">
        <!-- 积分大卡片 -->
        <div class="points-card">
          <div class="points-main">
            <div class="points-label">当前可用积分</div>
            <div class="points-value">
              {{ currentStudent.score_summary.available_points }}
            </div>
            <div class="points-exchanged">
              累计兑换：{{ currentStudent.score_summary.exchanged_points }}
            </div>
          </div>
          <div class="points-action">
            <div class="points-icon">￥</div>
          </div>
        </div>

        <!-- 快捷操作 -->
        <div class="quick-actions">
          <div
            class="quick-card"
            @click="handleQuickAddTask(currentStudent.student.id)"
          >
            <div class="quick-icon pen">
              <van-icon name="edit" />
              </div>
            <div class="quick-text">记一笔</div>
              </div>
          <div
            class="quick-card"
            @click="handleAvailablePointsClick(currentStudent.student.id)"
          >
            <div class="quick-icon gift">
              <van-icon name="gift-o" />
            </div>
            <div class="quick-text">换奖励</div>
            </div>
          </div>

        <!-- 最近一周动态 -->
          <div class="student-section">
          <div class="section-title-row">
            <div class="section-title">最近一周动态</div>
          </div>
          <div v-if="activities.length === 0" class="empty-state compact">
            <van-empty description="最近一周暂无积分变动" />
          </div>
          <div v-else class="activity-list">
            <div
              v-for="(item, index) in activities"
              :key="item.key"
              class="activity-item"
              :class="{ 'activity-item-latest': index === 0 }"
            >
              <div class="activity-left">
                <span
                  class="activity-dot"
                  :class="[
                    item.type === 'increase' ? 'activity-dot-increase' : 'activity-dot-exchange',
                    { 'activity-dot-latest': index === 0 }
                  ]"
                >
                  <van-icon v-if="index === 0" name="success" class="activity-dot-check" />
                </span>
                <div class="activity-text">
                  <div 
                    class="activity-title"
                    :class="index === 0 ? (item.type === 'increase' ? 'activity-title-latest-increase' : 'activity-title-latest-exchange') : ''"
                  >
                    {{ item.title }}
                  </div>
                  <div class="activity-time">
                    {{ formatTime(item.created_at) }}
                  </div>
                </div>
            </div>
              <div
                class="activity-amount"
                :class="item.type === 'increase' ? 'activity-amount-plus' : 'activity-amount-minus'"
              >
                {{ item.type === 'increase' ? '+' : '-' }}{{ item.points }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showFailToast } from 'vant'
import { dashboardApi } from '../api/dashboard'
import { useStudentsStore } from '../stores/students'
import { scoresApi } from '../api/scores'
import { formatLocalDateTime } from '../utils/date'
const router = useRouter()
const studentsStore = useStudentsStore()

const loading = ref(true)
const dashboardData = ref(null)
const activeStudentId = ref(null)
const showStudentPicker = ref(false)
const activities = ref([])

const students = computed(() => dashboardData.value?.students || [])

const currentStudent = computed(() => {
  if (!students.value.length) return null
  const found = students.value.find(
    (item) => item.student.id === activeStudentId.value
  )
  return found || students.value[0]
})

// 根据性别返回头像文件路径
const getAvatarUrl = () => {
  if (!currentStudent.value || !currentStudent.value.student.gender) {
    return '/avatar-default-40x40.png' // 默认头像
  }
  
  if (currentStudent.value.student.gender === 'male') {
    return '/avatar-boy-40x40.png' // 男孩头像
  }
  
  if (currentStudent.value.student.gender === 'female') {
    return '/avatar-girl-40x40.png' // 女孩头像
  }
  
  return '/avatar-default-40x40.png'
}

// 计算并显示年级
const getGradeDisplay = (student) => {
  if (!student) return '年级未设置'
  
  // 获取学校名称
  const school = student.school
  
  // 如果没有入学日期或教育阶段
  if (!student.enroll_date || !student.stage) {
    // 如果学校为空，返回默认文本
    return school || '年级未设置'
  }
  
  try {
    // 解析入学日期
    const enrollDate = new Date(student.enroll_date)
    const enrollYear = enrollDate.getFullYear()
    
    // 获取当前日期
    const now = new Date()
    const currentYear = now.getFullYear()
    const currentMonth = now.getMonth() + 1 // getMonth() 返回 0-11
    
    // 计算年级：当前年份 - 入学年份
    let grade = currentYear - enrollYear
    
    // 如果当前月份在9月及以后，年级+1
    if (currentMonth >= 9) {
      grade += 1
    }
    
    // 确保年级至少为1
    if (grade < 1) {
      grade = 1
    }
    
    // 根据教育阶段显示
    let gradeText = ''
    if (student.stage === 'primary') {
      // 小学最多6年级
      if (grade > 6) {
        grade = 6
      }
      // 小学：小一、小二、小三、小四、小五、小六
      const gradeMap = ['', '一', '二', '三', '四', '五', '六']
      gradeText = `小${gradeMap[grade] || grade}`
    } else if (student.stage === 'junior_high') {
      // 初中最多3年级
      if (grade > 3) {
        grade = 3
      }
      // 初中：初一、初二、初三
      const gradeMap = ['', '一', '二', '三']
      gradeText = `初${gradeMap[grade] || grade}`
    } else {
      // 未知教育阶段
      const gradeDisplay = `第${grade}年级`
      // 如果学校为空，只显示年级
      return school ? `${school} · ${gradeDisplay}` : gradeDisplay
    }
    
    // 如果学校为空，只显示年级
    return school ? `${school} · ${gradeText}` : gradeText
  } catch (error) {
    console.error('计算年级失败:', error)
    return school || '年级未设置'
  }
}

// 孩子选择下拉选项：所有孩子 + "＋ 添加孩子"
const studentColumns = computed(() => {
  const base = students.value.map((item) => ({
    text: item.student.name,
    value: item.student.id
  }))
  return [
    ...base,
    {
      text: '＋ 添加孩子',
      value: 'add'
    }
  ]
})

const fetchDashboard = async () => {
  loading.value = true
  try {
    const data = await dashboardApi.getDashboard()
    dashboardData.value = data
    if (data.students.length > 0) {
      // 优先使用 store 中已选中的学生，如果没有则使用第一个
      let selectedId = studentsStore.currentStudentId
      
      // 验证选中的学生是否在返回的数据中
      const studentExists = data.students.some(item => item.student.id === selectedId)
      if (!studentExists || !selectedId) {
        // 如果选中的学生不存在或没有选中，使用第一个
        selectedId = data.students[0].student.id
        studentsStore.setCurrentStudent(selectedId)
      }
      
      activeStudentId.value = selectedId
      await fetchRecentActivities(selectedId)
    }
  } catch (error) {
    showFailToast('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 获取最近一周的积分变动（增加 + 兑换），最多 20 条
const fetchRecentActivities = async (studentId) => {
  if (!studentId) {
    activities.value = []
    return
  }
  try {
    const [increases, exchanges] = await Promise.all([
      scoresApi.getIncreases(studentId, 100),
      scoresApi.getExchanges(studentId, 100)
    ])

    const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)

    const incItems = (increases || []).map((it) => {
      // 奖励标题：项目名称 + 评分（如：语文 作业 (A*)）
      let title = it.project_level1_name || '积分奖励'
      if (it.project_level1_name && it.project_level2_name) {
        title = `${it.project_level1_name} ${it.project_level2_name}`
      }
      if (it.rating) {
        title = `${title} (${it.rating})`
      }
      return {
        key: `inc-${it.id}`,
        type: 'increase',
        title,
        points: it.points,
        created_at: it.created_at
      }
    })

    const excItems = (exchanges || []).map((it) => ({
      key: `exc-${it.id}`,
      type: 'exchange',
      title: `兑换 ${it.reward_name || '积分奖励'}`,
      points: it.cost_points,
      created_at: it.created_at
    }))

    const merged = [...incItems, ...excItems].filter((item) => {
      const d = new Date(item.created_at)
      return !Number.isNaN(d.getTime()) && d >= weekAgo
    })

    merged.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )

    activities.value = merged.slice(0, 20)
  } catch (error) {
    console.error('加载最近一周动态失败:', error)
  }
}

const formatTime = (value) => {
  return formatLocalDateTime(value, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}

// 打开孩子选择下拉
const openStudentPicker = () => {
  if (!students.value.length) {
    router.push({ path: '/profile', query: { action: 'add-student' } })
    return
  }
  showStudentPicker.value = true
}

// 处理 picker 选项点击（支持双击快速选择）
let lastClickTime = 0
let lastClickIndex = -1
const DOUBLE_CLICK_DELAY = 300 // 300ms 内的两次点击视为双击

const handlePickerOptionClick = ({ currentOption, selectedIndex }) => {
  const now = Date.now()
  const option = currentOption
  
  // 如果是"添加孩子"，立即处理
  if (option && option.value === 'add') {
    showStudentPicker.value = false
    router.push({ path: '/profile', query: { action: 'add-student' } })
    return
  }
  
  // 双击快速选择（300ms 内的两次点击）
  if (now - lastClickTime < DOUBLE_CLICK_DELAY && selectedIndex === lastClickIndex) {
    // 双击确认
    onStudentConfirm({ selectedOptions: [option] })
    lastClickTime = 0
    lastClickIndex = -1
  } else {
    lastClickTime = now
    lastClickIndex = selectedIndex
  }
}

// 下拉确认选择
const onStudentConfirm = ({ selectedOptions }) => {
  const option = selectedOptions?.[0]
  if (!option) {
    showStudentPicker.value = false
    return
  }
  if (option.value === 'add') {
    showStudentPicker.value = false
    router.push({ path: '/profile', query: { action: 'add-student' } })
    return
  }
  switchStudent(option.value)
  showStudentPicker.value = false
}

// 首页快捷入口：记一笔 -> 跳转任务页并打开新增表单
const handleQuickAddTask = (studentId) => {
  studentsStore.setCurrentStudent(studentId)
  router.push({
    path: '/tasks',
    query: {
      action: 'add',
      student_id: studentId
    }
  })
}

// 切换学生
const switchStudent = (studentId) => {
  activeStudentId.value = studentId
  studentsStore.setCurrentStudent(studentId)
  fetchRecentActivities(studentId)
}

// 点击可用积分 - 跳转到新增兑换页面
const handleAvailablePointsClick = (studentId) => {
  studentsStore.setCurrentStudent(studentId)
  router.push({
    path: '/scores',
    query: {
      action: 'exchange',
      student_id: studentId
    }
  })
}

// 点击已兑换积分 - 跳转到兑换记录列表页
const handleExchangedPointsClick = (studentId) => {
  studentsStore.setCurrentStudent(studentId)
  router.push({
    path: '/scores',
    query: {
      tab: 'exchanges',
      student_id: studentId
    }
  })
}

onMounted(() => {
  fetchDashboard()
})
</script>

<style scoped>
.home-container {
  width: 100%;
  min-height: 60vh;
  background: #f4f5f7;
}

.home-header {
  padding: 10px 12px 6px;
  padding-top: calc(12px + env(safe-area-inset-top));
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-avatar {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.header-info {
  display: flex;
  flex-direction: column;
}

.header-arrow {
  font-size: 14px;
  color: #9ca3af;
  margin-left: 4px;
}

.header-name {
  font-size: 17px;
  font-weight: 600;
  color: #111827;
}

.header-meta {
  margin-top: 2px;
  font-size: 12px;
  color: #6b7280;
}

.home-scroll {
  padding: 8px 8px 8px; /* 收紧左右边距，为底部 TabBar 预留空间 */
  box-sizing: border-box;
}

.scroll-loading {
  padding-top: 40px;
}

.points-card {
  margin-top: 4px;
  border-radius: 20px;
  padding: 14px 16px;
  height: 150px;
  background: linear-gradient(135deg, #ffb74d 0%, #ffa726 25%, #ff9800 50%, #fb8c00 75%, #f57c00 100%);
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  box-shadow: 0 10px 30px rgba(255, 167, 38, 0.4),
              0 4px 15px rgba(255, 152, 0, 0.3);
  position: relative;
  overflow: hidden;
}

.points-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.points-label {
  font-size: 13px;
  opacity: 0.9;
  font-weight: 500;
}

.points-value {
  font-size: 60px;
  font-weight: 700;
  height: 64px;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.points-exchanged {
  margin-top: 2px;
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  font-weight: 500;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
  font-size: 13px;
}

.points-action {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: flex-end;
}

.points-icon {
  position: absolute;
  right: -20px;
  bottom: -20px;
  width: 120px;
  height: 120px;
  border-radius: 999px;
  background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.4), rgba(255, 183, 77, 0.3));
  opacity: 0.6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 72px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  transform: rotate(15deg);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 0;
}

.points-button {
  margin-top: 0;
  border: none;
  background: #ffffff;
  color: #ff9800;
  font-weight: 500;
  padding: 0 14px;
  position: relative;
  z-index: 1;
}

.points-button :deep(.van-button__text) {
  font-size: 13px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 16px;
}

.quick-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
  cursor: pointer;
  transition: transform 0.12s ease-out, box-shadow 0.12s ease-out;
}

.quick-card:active {
  transform: translateY(1px) scale(0.99);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
}

.quick-icon {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 16px;
}

.quick-icon.pen {
  background: linear-gradient(135deg, #42a5f5, #1e88e5);
}

.quick-icon.gift {
  background: linear-gradient(135deg, #ab47bc, #8e24aa);
}

.quick-text {
  font-size: 16px;
  font-weight: 500;
  color: #111827;
}

.student-section {
  margin-top: 18px;
  padding: 14px 14px 10px;
  border-radius: 18px;
  background: #ffffff;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}
.section-subtitle {
  font-size: 12px;
  color: #9ca3af;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-left: 16px;
  margin-right: 16px;
}

.activity-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  position: relative;
  padding-bottom: 8px;
}

.activity-item:last-child {
  padding-bottom: 0;
}

.activity-item:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 16px; /* activity-dot(8px) + gap(8px) = activity-text 开始位置 */
  right: 0;
  bottom: 0;
  height: 1px;
  background: #e5e7eb;
  margin-right: 0;
}

.activity-left {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  position: relative;
}

.activity-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  margin-top: 6px;
  position: relative;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.activity-dot-latest {
  width: 10px;
  height: 10px;
  margin-top: 4px;
  margin-left: -2px; /* 向左偏移 2px，使中心与普通 dot 对齐 (10px/2 - 6px/2 = 2px) */
}

.activity-dot-check {
  font-size: 6px;
  color: #ffffff;
}

.activity-item:not(:last-child) .activity-left::after {
  content: '';
  position: absolute;
  left: 2.5px; /* activity-dot 的中心位置 (6px / 2 - 0.5px) */
  top: 12px; /* activity-dot 的底部 (6px margin-top + 6px height) */
  width: 1px;
  bottom: -26px; /* 延伸到下一个 item 的 dot 顶部: padding-bottom(8px) + margin-top(8px) + dot margin-top(6px) = 22px */
  background: #e5e7eb;
  z-index: 0;
}

.activity-item-latest .activity-left::after {
  left: 2.5px; /* 与普通 dot 中心对齐 */
  top: 14px; /* 最新 dot 的底部 (4px margin-top + 10px height) */
  bottom: -22px; /* 延伸到下一个 item 的 dot 顶部 */
}

.activity-dot-increase {
  background: #4a90e2;
}

.activity-dot-exchange {
  background: #ba68c8;
}

.activity-text {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.activity-title {
  font-size: 15px;
  font-weight: 500;
  color: #46494f;
}

.activity-title-latest-increase {
  color: #4a90e2;
}

.activity-title-latest-exchange {
  color: #ba68c8;
}

.activity-time {
  margin-top: 2px;
  font-size: 12px;
  color: #9ca3af;
}

.activity-amount {
  font-size: 16px;
  font-weight: 700;
}

.activity-amount-plus {
  color: #4a90e2;
}

.activity-amount-minus {
  color: #ba68c8;
}

.empty-state {
  padding: 12px 0;
}

.empty-state.compact :deep(.van-empty) {
  padding: 0;
}
</style>


