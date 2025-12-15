<template>
  <div class="scores-container">
    <!-- 学生头部（含选择） -->
    <StudentHeader
      :student="currentStudent"
      :all-students="studentsStore.students"
      @switch="handleStudentSwitch"
      @add="handleAddStudent"
    />

    <van-tabs v-model:active="activeTab">
      <van-tab title="积分汇总">
        <div v-if="summary" class="summary-section">
          <van-cell-group inset style="margin: 12px;">
            <van-cell 
              title="可用积分" 
              :value="`${summary.available_points} 分`"
              is-link
              @click="handleAvailablePointsClick"
            />
            <van-cell 
              title="已兑换积分" 
              :value="`${summary.exchanged_points} 分`"
              is-link
              @click="handleExchangedPointsClick"
            />
          </van-cell-group>
        </div>
      </van-tab>
      
      <van-tab title="增加记录">
        <van-loading v-if="loadingIncreases" vertical>加载中...</van-loading>
        <div v-else>
          <van-empty v-if="increases.length === 0" description="暂无记录" />
          <van-cell-group v-else inset style="margin: 12px;">
            <van-cell
              v-for="item in increases"
              :key="item.id"
              :title="getIncreaseTitle(item)"
              :value="`+${item.points} 积分`"
              :label="formatLocalDateTime(item.created_at)"
            />
          </van-cell-group>
        </div>
      </van-tab>
      
      <van-tab title="兑换记录">
        <div style="padding: 12px;">
          <van-button round block type="primary" icon="plus" @click="showExchangeForm = true">
            新增兑换
          </van-button>
        </div>
        <van-loading v-if="loadingExchanges" vertical>加载中...</van-loading>
        <div v-else>
          <van-empty v-if="exchanges.length === 0" description="暂无记录" />
          <van-cell-group v-else inset style="margin: 12px;">
            <van-cell
              v-for="item in exchanges"
              :key="item.id"
              :title="item.reward_name || '未知奖励'"
              :value="`-${item.cost_points} 积分`"
              :label="formatLocalDateTime(item.created_at)"
            />
          </van-cell-group>
        </div>
        <van-floating-bubble
          axis="xy"
          icon="plus"
          @click="showExchangeForm = true"
        />
      </van-tab>
    </van-tabs>

    <!-- 兑换弹窗 -->
    <van-popup v-model:show="showExchangeForm" position="bottom" :style="{ height: '50%' }">
      <van-nav-bar
        title="积分兑换"
        left-arrow
        @click-left="showExchangeForm = false"
      />
      <div class="exchange-form">
        <van-form @submit="onExchangeSubmit">
          <van-cell-group inset>
            <van-field
              :model-value="rewardOptionDisplayText"
              readonly
              label="兑换奖励"
              placeholder="选择奖励"
              is-link
              required
              @click="showRewardPicker = true"
            />
            <van-field
              v-if="selectedRewardCost !== null"
              :model-value="`${selectedRewardCost} 积分`"
              readonly
              label="消耗积分"
            />
          </van-cell-group>
          <div style="margin: 16px;">
            <van-button round block type="primary" native-type="submit" :loading="exchanging">
              确认兑换
            </van-button>
          </div>
        </van-form>
      </div>
    </van-popup>

    <!-- 奖励选择器 -->
    <van-popup v-model:show="showRewardPicker" position="bottom">
      <van-picker
        :columns="rewardColumns"
        :default-index="rewardDefaultIndex"
        @confirm="onRewardConfirm"
        @cancel="showRewardPicker = false"
        @click-option="(params) => handlePickerDoubleClick(params, onRewardConfirm)"
      />
    </van-popup>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showFailToast, showSuccessToast, showToast } from 'vant'
import { scoresApi } from '../api/scores'
import { useStudentsStore } from '../stores/students'
import { extractErrorMessage } from '../utils/errorHandler'
import { formatLocalDateTime } from '../utils/date'
import StudentHeader from '../components/StudentHeader.vue'

const route = useRoute()
const router = useRouter()
const studentsStore = useStudentsStore()

const currentStudentId = ref(null)
const activeTab = ref(0)
const loadingIncreases = ref(false)
const loadingExchanges = ref(false)
const exchanging = ref(false)

const summary = ref(null)
const increases = ref([])
const exchanges = ref([])
const rewardOptions = ref([])

const showExchangeForm = ref(false)
const showRewardPicker = ref(false)
const exchangeForm = ref({
  reward_option_id: null
})

const currentStudent = computed(() => {
  if (!studentsStore.students.length) return null
  return studentsStore.students.find(s => s.id === currentStudentId.value)
})

const rewardColumns = computed(() => {
  return rewardOptions.value.map(r => ({ text: `${r.name} (${r.cost_points}积分)`, value: r.id }))
})

const selectedRewardOption = computed(() => {
  if (!exchangeForm.value.reward_option_id) return null
  return rewardOptions.value.find(r => r.id === exchangeForm.value.reward_option_id) || null
})

const rewardOptionDisplayText = computed(() => {
  if (!selectedRewardOption.value) return ''
  return `${selectedRewardOption.value.name} (${selectedRewardOption.value.cost_points}积分)`
})

const selectedRewardCost = computed(() => {
  return selectedRewardOption.value ? selectedRewardOption.value.cost_points : null
})

const rewardDefaultIndex = computed(() => {
  if (!exchangeForm.value.reward_option_id) return 0
  const index = rewardOptions.value.findIndex(r => r.id === exchangeForm.value.reward_option_id)
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

const fetchSummary = async () => {
  if (!currentStudentId.value) return
  try {
    summary.value = await scoresApi.getSummary(currentStudentId.value)
  } catch (error) {
    showToast.fail('加载汇总失败')
  }
}

const fetchIncreases = async () => {
  if (!currentStudentId.value) return
  loadingIncreases.value = true
  try {
    increases.value = await scoresApi.getIncreases(currentStudentId.value)
  } catch (error) {
    showFailToast('加载记录失败')
  } finally {
    loadingIncreases.value = false
  }
}

const fetchExchanges = async () => {
  if (!currentStudentId.value) return
  loadingExchanges.value = true
  try {
    exchanges.value = await scoresApi.getExchanges(currentStudentId.value)
  } catch (error) {
    showFailToast('加载记录失败')
  } finally {
    loadingExchanges.value = false
  }
}

const fetchRewardOptions = async () => {
  try {
    rewardOptions.value = await scoresApi.getRewardOptions()
  } catch (error) {
    showFailToast('加载奖励选项失败')
  }
}

const handleStudentSwitch = (studentId) => {
  currentStudentId.value = studentId
  studentsStore.setCurrentStudent(studentId)
  fetchSummary()
  fetchIncreases()
  fetchExchanges()
}

const handleAddStudent = () => {
  router.push({ path: '/profile', query: { action: 'add-student' } })
}

const onRewardConfirm = ({ selectedOptions }) => {
  exchangeForm.value.reward_option_id = selectedOptions[0].value
  showRewardPicker.value = false
}

const onExchangeSubmit = async () => {
  if (!exchangeForm.value.reward_option_id) {
    showFailToast('请选择兑换奖励')
    return
  }

  exchanging.value = true
  try {
    await scoresApi.createExchange({
      student_id: currentStudentId.value,
      reward_option_id: exchangeForm.value.reward_option_id
    })
    showSuccessToast('兑换成功')
    showExchangeForm.value = false
    exchangeForm.value.reward_option_id = null
    await Promise.all([fetchSummary(), fetchExchanges()])
  } catch (error) {
    const message = extractErrorMessage(error)
    showFailToast(message || '兑换失败')
  } finally {
    exchanging.value = false
  }
}

// 点击可用积分 - 打开新增兑换表单
const handleAvailablePointsClick = () => {
  activeTab.value = 2  // 切换到兑换记录标签页
  showExchangeForm.value = true
}

// 点击已兑换积分 - 跳转到兑换记录列表页
const handleExchangedPointsClick = () => {
  activeTab.value = 2  // 切换到兑换记录标签页
  // 如果表单打开，先关闭
  if (showExchangeForm.value) {
    showExchangeForm.value = false
  }
}

// 获取积分增加记录的标题（项目名称 + 评分等级）
const getIncreaseTitle = (item) => {
  const parts = []
  
  // 项目名称
  if (item.project_level1_name) {
    if (item.project_level2_name) {
      parts.push(`${item.project_level1_name} > ${item.project_level2_name}`)
    } else {
      parts.push(item.project_level1_name)
    }
  }
  
  // 评分等级
  if (item.rating) {
    parts.push(`评分: ${item.rating}`)
  }
  
  return parts.length > 0 ? parts.join(' | ') : '任务奖励'
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
  
  // 确保已加载奖励选项
  if (rewardOptions.value.length === 0) {
    await fetchRewardOptions()
  }
  
  // 检查是否有预填数据（从语音助手跳转）
  if (route.query.action === 'exchange' && route.query.prefill) {
    try {
      const prefillData = JSON.parse(decodeURIComponent(route.query.prefill))
      
      // 切换到兑换记录标签页
      activeTab.value = 2
      
      // 打开兑换表单并预填数据
      if (prefillData.reward_option_id) {
        exchangeForm.value.reward_option_id = prefillData.reward_option_id
        showExchangeForm.value = true
        showToast({
          message: '已从语音助手预填兑换选项，请确认',
          position: 'top',
          duration: 3000
        })
      } else {
        // 没有匹配到选项，仍打开表单让用户手动选择
        showExchangeForm.value = true
        showToast({
          message: '请手动选择兑换奖励',
          position: 'top',
          duration: 3000
        })
      }
      
      // 清除 URL 参数，避免刷新页面重复打开
      const newQuery = { ...route.query }
      delete newQuery.action
      delete newQuery.prefill
      delete newQuery._t
      router.replace({ path: '/scores', query: newQuery })
    } catch (e) {
      console.error('解析预填数据失败:', e)
    }
  } else if (route.query.action === 'exchange') {
    // 从首页点击可用积分跳转过来，直接打开兑换表单
    activeTab.value = 2
    showExchangeForm.value = true
    // 清除 URL 参数
    const newQuery = { ...route.query }
    delete newQuery.action
    delete newQuery._t
    router.replace({ path: '/scores', query: newQuery })
  } else if (route.query.tab === 'exchanges') {
    // 从首页点击已兑换积分跳转过来，切换到兑换记录标签页
    activeTab.value = 2
    // 清除 URL 参数
    const newQuery = { ...route.query }
    delete newQuery.tab
    router.replace({ path: '/scores', query: newQuery })
  }
}

onMounted(async () => {
  await studentsStore.fetchStudents()
  
  // 处理 URL 参数中的 student_id（从首页跳转过来）
  if (route.query.student_id) {
    const studentId = parseInt(route.query.student_id)
    const student = studentsStore.students.find(s => s.id === studentId)
    if (student) {
      currentStudentId.value = studentId
      studentsStore.setCurrentStudent(studentId)
    }
  } else if (studentsStore.students.length > 0) {
    currentStudentId.value = studentsStore.currentStudent.id
  }
  
  await fetchRewardOptions()
  await fetchSummary()
  await fetchIncreases()
  await fetchExchanges()
  
  // 处理预填数据
  await handlePrefillData()
})

// 监听路由变化，处理预填数据（当用户在积分页面时，路由参数变化也能响应）
watch(() => route.query, async (newQuery) => {
  if (newQuery.action === 'exchange' || newQuery.tab === 'exchanges') {
    await handlePrefillData()
  }
}, { deep: true })
</script>

<style scoped>
.scores-container {
  width: 100%;
}

.summary-section {
  padding: 12px;
}

@media (min-width: 768px) {
  .summary-section {
    padding: 16px;
  }
}

@media (min-width: 1024px) {
  .summary-section {
    padding: 24px;
    max-width: 1000px;
    margin: 0 auto;
  }
}

.exchange-form {
  padding: 12px;
}

@media (min-width: 768px) {
  .exchange-form {
    padding: 16px;
  }
}

@media (min-width: 1024px) {
  .exchange-form {
    padding: 24px;
    max-width: 600px;
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

