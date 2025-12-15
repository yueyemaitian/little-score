<template>
  <div class="home-container">
    <!-- 顶部 App 头部（点击可选择/新增孩子） -->
    <div class="home-header" @click="openStudentPicker">
      <div class="header-left">
        <div class="header-avatar">
          <span v-if="currentStudent" class="header-avatar-text">
            {{ (currentStudent.student.name || '').charAt(0) || '学' }}
          </span>
        </div>
        <div class="header-info" v-if="currentStudent">
          <div class="header-name">{{ currentStudent.student.name }}</div>
          <div class="header-meta">
            {{ currentStudent.student.school || '年级未设置' }} · Lv.1
          </div>
        </div>
        <van-icon name="arrow-down" class="header-arrow" />
      </div>
      <div class="header-right">
        <van-icon name="bell" class="header-icon" />
      </div>
    </div>

    <!-- 孩子下拉选择 / 新增 -->
    <van-popup v-model:show="showStudentPicker" position="bottom" round>
      <van-picker
        title="选择孩子"
        :columns="studentColumns"
        @confirm="onStudentConfirm"
        @cancel="showStudentPicker = false"
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
            <div
              class="points-exchanged"
              @click.stop="handleExchangedPointsClick(currentStudent.student.id)"
            >
              累计兑换：{{ currentStudent.score_summary.exchanged_points }}
            </div>
          </div>
          <div class="points-action">
            <div class="points-icon"></div>
            <van-button
              type="primary"
              size="small"
              round
              class="points-button"
              @click="handleAvailablePointsClick(currentStudent.student.id)"
            >
              去兑换 &gt;
            </van-button>
          </div>
        </div>

        <!-- 快捷操作 -->
        <div class="quick-actions">
          <div
            class="quick-card"
            @click="handleQuickAddTask(currentStudent.student.id)"
          >
            <div class="quick-icon pen"></div>
            <div class="quick-text">记一笔</div>
          </div>
          <div
            class="quick-card"
            @click="handleAvailablePointsClick(currentStudent.student.id)"
          >
            <div class="quick-icon gift"></div>
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
              v-for="item in activities"
              :key="item.key"
              class="activity-item"
            >
              <div class="activity-left">
                <span
                  class="activity-dot"
                  :class="item.type === 'increase' ? 'activity-dot-increase' : 'activity-dot-exchange'"
                />
                <div class="activity-text">
                  <div class="activity-title">{{ item.title }}</div>
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

// 孩子选择下拉选项：所有孩子 + “＋ 添加孩子”
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
      const firstId = data.students[0].student.id
      studentsStore.setCurrentStudent(firstId)
      activeStudentId.value = firstId
      await fetchRecentActivities(firstId)
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

// 首页快捷入口：记一笔 -> 跳转任务页
const handleQuickAddTask = (studentId) => {
  studentsStore.setCurrentStudent(studentId)
  router.push({ path: '/tasks' })
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
  min-height: 100vh;
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
  background: linear-gradient(135deg, #ffcc80, #ffb74d);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 18px;
  font-weight: 600;
}

.header-avatar-text {
  transform: translateY(1px);
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
  color: #9ca3af;
}

.header-right {
  display: flex;
  align-items: center;
}

.header-icon {
  font-size: 20px;
  color: #9ca3af;
}

.home-scroll {
  padding: 8px 8px 72px; /* 收紧左右边距，为底部 TabBar 预留空间 */
  box-sizing: border-box;
}

.scroll-loading {
  padding-top: 40px;
}

.points-card {
  margin-top: 4px;
  border-radius: 20px;
  padding: 18px 18px 16px;
  background: linear-gradient(135deg, #ffb74d, #ffa726);
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  box-shadow: 0 10px 30px rgba(255, 167, 38, 0.4);
}

.points-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.points-label {
  font-size: 13px;
  opacity: 0.9;
}

.points-value {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: 1px;
}

.points-exchanged {
  margin-top: 4px;
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
  font-size: 12px;
  cursor: pointer;
}

.points-exchanged:active {
  background: rgba(255, 255, 255, 0.3);
}

.points-action {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-end;
}

.points-icon {
  width: 54px;
  height: 54px;
  border-radius: 999px;
  background: radial-gradient(circle at 30% 30%, #fff3e0, #ffb74d);
  opacity: 0.9;
}

.points-button {
  margin-top: 12px;
  border: none;
  background: #ffffff;
  color: #ff9800;
  font-weight: 500;
  padding: 0 14px;
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
  background: linear-gradient(135deg, #ffca28, #ffb300);
}

.quick-text {
  font-size: 14px;
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
  font-size: 14px;
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
  gap: 12px;
}

.activity-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.activity-left {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  margin-top: 6px;
}

.activity-dot-increase {
  background: #4a90e2;
}

.activity-dot-exchange {
  background: #c4c4c4;
}

.activity-text {
  display: flex;
  flex-direction: column;
}

.activity-title {
  font-size: 14px;
  font-weight: 500;
  color: #111827;
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
  color: #ffb300;
}

.activity-amount-minus {
  color: #f43f5e;
}

.empty-state {
  padding: 12px 0;
}

.empty-state.compact :deep(.van-empty) {
  padding: 0;
}
</style>


