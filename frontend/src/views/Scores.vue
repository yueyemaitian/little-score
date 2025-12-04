<template>
  <div class="page-container scores-container">
    <van-nav-bar title="积分管理" />
    
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

    <van-tabs v-model:active="activeTab">
      <van-tab title="积分汇总">
        <div v-if="summary" class="summary-section">
          <van-cell-group inset style="margin: 12px;">
            <van-cell title="可用积分" :value="`${summary.available_points} 分`" />
            <van-cell title="已兑换积分" :value="`${summary.exchanged_points} 分`" />
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
              :title="`+${item.points} 积分`"
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
              :title="`-${item.cost_points} 积分`"
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

    <!-- 学生选择器 -->
    <van-popup v-model:show="showStudentPicker" position="bottom">
      <van-picker
        :columns="studentColumns"
        @confirm="onStudentConfirm"
        @cancel="showStudentPicker = false"
      />
    </van-popup>

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

    <!-- 底部导航 -->
    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { showFailToast, showSuccessToast } from 'vant'
import { scoresApi } from '../api/scores'
import { useStudentsStore } from '../stores/students'
import BottomNav from '../components/BottomNav.vue'
import { extractErrorMessage } from '../utils/errorHandler'
import { formatLocalDateTime } from '../utils/date'

const studentsStore = useStudentsStore()

const currentStudentId = ref(null)
const selectedStudentName = ref('')
const showStudentPicker = ref(false)
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

const studentColumns = computed(() => {
  return studentsStore.students.map(s => ({ text: s.name, value: s.id }))
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

// 默认索引（用于设置初始选中项）
const studentDefaultIndex = computed(() => {
  if (!currentStudentId.value) return 0
  const index = studentsStore.students.findIndex(s => s.id === currentStudentId.value)
  return index >= 0 ? index : 0
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

const onStudentConfirm = ({ selectedOptions }) => {
  currentStudentId.value = selectedOptions[0].value
  selectedStudentName.value = selectedOptions[0].text
  studentsStore.setCurrentStudent(currentStudentId.value)
  showStudentPicker.value = false
  fetchSummary()
  fetchIncreases()
  fetchExchanges()
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

onMounted(async () => {
  await studentsStore.fetchStudents()
  if (studentsStore.students.length > 0) {
    currentStudentId.value = studentsStore.currentStudent.id
    selectedStudentName.value = studentsStore.currentStudent.name
  }
  await fetchRewardOptions()
  await fetchSummary()
  await fetchIncreases()
  await fetchExchanges()
})
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

