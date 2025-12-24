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
      <van-tab title="兑换奖励">
        <!-- 可用积分显示 -->
        <div v-if="summary" class="points-summary">
          <div class="points-summary-content">
            <span class="points-label">可用积分：</span>
            <span class="points-value">{{ summary.available_points }}</span>
          </div>
        </div>
        
        <!-- 奖励卡片列表 -->
        <div class="rewards-scroll">
          <van-loading v-if="loadingRewards" vertical>加载中...</van-loading>
          <div v-else-if="rewardOptions.length === 0" class="empty-container">
            <van-empty description="暂无奖励选项" />
          </div>
          <div v-else class="rewards-grid">
            <div
              v-for="reward in rewardOptions"
              :key="reward.id"
              class="reward-card"
            >
              <div class="reward-icon">{{ getRewardIcon(reward.name) }}</div>
              <div class="reward-content">
                <div class="reward-name">{{ reward.name }}</div>
                <div class="reward-footer">
                  <div class="reward-cost">{{ reward.cost_points }} 积分</div>
                  <van-button
                    round
                    type="primary"
                    size="mini"
                    :disabled="!canExchange(reward.cost_points)"
                    @click="handleExchangeClick(reward)"
                    class="reward-button"
                  >
                    兑换
                  </van-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </van-tab>
      
      <van-tab title="兑换记录">
        <div class="exchanges-scroll">
          <van-loading v-if="loadingExchanges" vertical>加载中...</van-loading>
          <div v-else-if="exchanges.length === 0" class="empty-container">
            <van-empty description="暂无记录" />
          </div>
          <div v-else class="exchanges-list">
            <div
              v-for="item in exchanges"
              :key="item.id"
              class="exchange-card"
            >
              <!-- 左侧图标 -->
              <div 
                class="exchange-icon" 
                :style="{ background: 'linear-gradient(135deg, #f3e5f5, #e1bee7)' }"
              >
                <span class="exchange-icon-emoji">
                  {{ getRewardIcon(item.reward_name || '') }}
                </span>
              </div>
              
              <!-- 中间内容 -->
              <div class="exchange-content">
                <div class="exchange-title">{{ item.reward_name || '未知奖励' }}</div>
                <div class="exchange-meta">
                  <span class="exchange-time">{{ formatLocalDateTime(item.created_at) }}</span>
                </div>
              </div>
              
              <!-- 右侧积分 -->
              <div class="exchange-action">
                <div class="exchange-points">
                  -{{ item.cost_points }} 积分
                </div>
              </div>
            </div>
          </div>
        </div>
      </van-tab>
    </van-tabs>

    <!-- 确认兑换对话框 -->
    <van-dialog
      v-model:show="showExchangeDialog"
      title="确认兑换"
      show-cancel-button
      @confirm="onExchangeConfirm"
      @cancel="showExchangeDialog = false"
    >
      <div class="exchange-dialog-content">
        <div class="dialog-reward-info">
          <div class="dialog-reward-icon">{{ getRewardIcon(selectedRewardForExchange?.name || '') }}</div>
          <div class="dialog-reward-details">
            <div class="dialog-reward-name">{{ selectedRewardForExchange?.name }}</div>
            <div class="dialog-reward-cost">消耗积分：{{ selectedRewardForExchange?.cost_points }}</div>
            <div class="dialog-available-points">可用积分：{{ summary?.available_points || 0 }}</div>
          </div>
        </div>
      </div>
    </van-dialog>

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
const loadingRewards = ref(false)
const loadingExchanges = ref(false)
const exchanging = ref(false)

const summary = ref(null)
const exchanges = ref([])
const rewardOptions = ref([])

const showExchangeDialog = ref(false)
const selectedRewardForExchange = ref(null)

const currentStudent = computed(() => {
  if (!studentsStore.students.length) return null
  return studentsStore.students.find(s => s.id === currentStudentId.value)
})

// 判断是否可以兑换（积分是否足够）
const canExchange = (costPoints) => {
  if (!summary.value) return false
  return summary.value.available_points >= costPoints
}

// 奖励名称关键词到图标的映射表（按优先级排序，优先匹配较长的关键词）
const rewardIconKeywords = [
  // 娱乐类（优先匹配较长的）
  { keywords: ['看电视', '看动画', '看动画片', '看视频'], icon: '📺' },
  { keywords: ['看电影', '电影票'], icon: '🎬' },
  { keywords: ['玩游戏', '游戏时间', '游戏'], icon: '🎮' },
  { keywords: ['电脑', '玩电脑', '用电脑', '电脑时间'], icon: '💻' },
  { keywords: ['听音乐', '音乐'], icon: '🎵' },
  { keywords: ['听故事', '故事'], icon: '📻' },
  
  // 零食/食物类
  { keywords: ['购买零食', '零食', '买零食'], icon: '🍦' },
  { keywords: ['冰淇淋', '雪糕'], icon: '🍦' },
  { keywords: ['甜品', '蛋糕', '甜点'], icon: '🍰' },
  { keywords: ['选择菜单', '选择晚餐', '晚餐', '吃饭'], icon: '🍽️' },
  { keywords: ['餐厅', '去餐厅'], icon: '🍽️' },
  
  // 特权类
  { keywords: ['免做家务', '免做一次家务'], icon: '🎟️' },
  { keywords: ['晚睡', '晚睡30分钟', '晚起'], icon: '🌙' },
  { keywords: ['选择活动', '选择周末活动'], icon: '🎯' },
  { keywords: ['邀请朋友', '朋友来玩', '朋友'], icon: '👫' },
  
  // 实物类
  { keywords: ['积木', '乐高', '拼装积木'], icon: '🧱' },
  { keywords: ['玩具枪', '枪', '水枪', '玩具手枪'], icon: '🔫' },
  { keywords: ['玩具', '买玩具'], icon: '🧸' },
  { keywords: ['故事书', '绘本', '书籍', '书', '买书'], icon: '📚' },
  { keywords: ['学习用品', '文具', '买文具'], icon: '✏️' },
  { keywords: ['衣服', '买衣服'], icon: '👕' },
  { keywords: ['配饰'], icon: '💍' },
  
  // 现金类
  { keywords: ['现金', '零花钱', '钱', '人民币'], icon: '💰' },
  
  // 体验类
  { keywords: ['游乐园', '游乐园门票', '乐园'], icon: '🎡' },
  { keywords: ['动物园', '动物园门票'], icon: '🦁' },
  { keywords: ['科技馆', '科技馆门票'], icon: '🔬' },
  { keywords: ['游泳', '去游泳'], icon: '🏊' },
  { keywords: ['滑冰', '去滑冰'], icon: '⛸️' },
  { keywords: ['兴趣班', '体验课', '兴趣活动'], icon: '🎨' },
  
  // 学习激励类
  { keywords: ['选择下一本书', '选择书'], icon: '📚' },
  { keywords: ['活动', '参加活动'], icon: '🎯' },
]

// 获取奖励图标（根据名称匹配）
const getRewardIcon = (rewardName) => {
  if (!rewardName) return '🎁'
  
  let name = rewardName.trim().toLowerCase()
  
  // 先检查是否包含金额单位（元、块等），如果包含则优先匹配现金
  if (/\d+\s*(元|块|角|分|毛|人民币)/.test(name)) {
    // 检查是否包含其他更具体的奖励关键词（如"零食"、"玩具"等）
    // 如果包含其他关键词，则按正常流程匹配
    const hasOtherKeywords = rewardIconKeywords.some(item => 
      item.keywords.some(keyword => {
        const lowerKeyword = keyword.toLowerCase()
        // 排除现金相关的关键词，检查其他关键词
        return lowerKeyword !== '现金' && 
               lowerKeyword !== '零花钱' && 
               lowerKeyword !== '钱' && 
               lowerKeyword !== '人民币' &&
               name.includes(lowerKeyword)
      })
    )
    
    // 如果没有其他关键词，则匹配现金
    if (!hasOtherKeywords) {
      return '💰'
    }
  }
  
  // 移除常见的时间单位（分钟、小时等）和金额单位（元、块等）
  name = name.replace(/\d+\s*(分钟|小时|小时|分|时|秒)/g, '')
  name = name.replace(/\d+\s*(元|块|角|分|毛)/g, '')
  name = name.replace(/\d+/g, '') // 移除剩余的数字
  name = name.trim()
  
  // 按优先级遍历关键词列表（已经按长度和优先级排序）
  for (const item of rewardIconKeywords) {
    for (const keyword of item.keywords) {
      if (name.includes(keyword.toLowerCase())) {
        return item.icon
      }
    }
  }
  
  // 如果都匹配不到，返回默认图标
  return '🎁'
}

// 点击兑换按钮
const handleExchangeClick = (reward) => {
  if (!canExchange(reward.cost_points)) {
    showFailToast('积分不足')
    return
  }
  selectedRewardForExchange.value = reward
  showExchangeDialog.value = true
}

// 确认兑换
const onExchangeConfirm = async () => {
  if (!selectedRewardForExchange.value) return
  
  exchanging.value = true
  try {
    await scoresApi.createExchange({
      student_id: currentStudentId.value,
      reward_option_id: selectedRewardForExchange.value.id
    })
    showSuccessToast('兑换成功')
    showExchangeDialog.value = false
    selectedRewardForExchange.value = null
    await Promise.all([fetchSummary(), fetchExchanges()])
  } catch (error) {
    const message = extractErrorMessage(error)
    showFailToast(message || '兑换失败')
  } finally {
    exchanging.value = false
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
  loadingRewards.value = true
  try {
    rewardOptions.value = await scoresApi.getRewardOptions()
  } catch (error) {
    showFailToast('加载奖励选项失败')
  } finally {
    loadingRewards.value = false
  }
}

const handleStudentSwitch = (studentId) => {
  currentStudentId.value = studentId
  studentsStore.setCurrentStudent(studentId)
  fetchSummary()
  fetchExchanges()
}

const handleAddStudent = () => {
  router.push({ path: '/profile', query: { action: 'add-student' } })
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
      
      // 切换到兑换奖励标签页
      activeTab.value = 0
      
      // 如果匹配到奖励选项，自动选中并弹出确认对话框
      if (prefillData.reward_option_id) {
        const reward = rewardOptions.value.find(r => r.id === prefillData.reward_option_id)
        if (reward) {
          selectedRewardForExchange.value = reward
          showExchangeDialog.value = true
          showToast({
            message: '已从语音助手预填兑换选项，请确认',
            position: 'top',
            duration: 3000
          })
        }
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
    // 从首页点击可用积分跳转过来，切换到兑换奖励标签页
    activeTab.value = 0
    // 清除 URL 参数
    const newQuery = { ...route.query }
    delete newQuery.action
    delete newQuery._t
    router.replace({ path: '/scores', query: newQuery })
  } else if (route.query.tab === 'exchanges') {
    // 从首页点击已兑换积分跳转过来，切换到兑换记录标签页
    activeTab.value = 1
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
  await fetchExchanges()
  
  // 处理预填数据
  await handlePrefillData()
})

// 监听路由变化，处理预填数据（当用户在商城页面时，路由参数变化也能响应）
watch(() => route.query, async (newQuery) => {
  if (newQuery.action === 'exchange' || newQuery.tab === 'exchanges') {
    await handlePrefillData()
  }
}, { deep: true })
</script>

<style scoped>
.scores-container {
  width: 100%;
  background: #f4f5f7;
  min-height: 100%;
}

/* 可用积分显示 */
.points-summary {
  background: #ffffff;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.points-summary-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.points-label {
  font-size: 14px;
  color: #6b7280;
}

.points-value {
  font-size: 20px;
  font-weight: 600;
  color: #ff9800;
}

/* 奖励卡片区域 */
.rewards-scroll {
  padding: 8px;
  box-sizing: border-box;
}

.empty-container {
  padding: 40px 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.rewards-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.reward-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
  transition: transform 0.12s ease-out, box-shadow 0.12s ease-out;
}

.reward-card:active {
  transform: translateY(1px) scale(0.99);
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
}

.reward-icon {
  font-size: 32px;
  line-height: 1;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f9fafb;
  border-radius: 12px;
  flex-shrink: 0;
}

.reward-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 100%;
  min-height: 0;
}

.reward-name {
  font-size: 13px;
  font-weight: 500;
  color: #111827;
  text-align: center;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
  min-height: 34px;
}

.reward-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 8px;
}

.reward-cost {
  font-size: 15px;
  font-weight: 600;
  color: #ff9800;
  white-space: nowrap;
  flex: 1;
}

.reward-button {
  flex-shrink: 0;
  padding: 4px 12px;
  font-size: 12px;
  height: 28px;
  min-width: 60px;
}

.reward-button:disabled {
  opacity: 0.5;
}

/* 兑换确认对话框 */
.exchange-dialog-content {
  padding: 20px;
}

.dialog-reward-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.dialog-reward-icon {
  font-size: 48px;
  line-height: 1;
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f9fafb;
  border-radius: 12px;
  flex-shrink: 0;
}

.dialog-reward-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dialog-reward-name {
  font-size: 16px;
  font-weight: 500;
  color: #111827;
}

.dialog-reward-cost {
  font-size: 14px;
  color: #ff9800;
  font-weight: 500;
}

.dialog-available-points {
  font-size: 14px;
  color: #6b7280;
}

/* 兑换记录区域 */
.exchanges-scroll {
  padding: 8px 8px 8px;
  box-sizing: border-box;
}

.exchanges-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.exchange-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
  transition: transform 0.12s ease-out, box-shadow 0.12s ease-out;
}

.exchange-card:active {
  transform: translateY(1px) scale(0.99);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
}

.exchange-icon {
  width: 38.4px;
  height: 38.4px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #ffffff;
}

.exchange-icon-emoji {
  font-size: 20px;
  line-height: 1;
  user-select: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.exchange-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.exchange-title {
  font-size: 15px;
  font-weight: 500;
  color: #111827;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.exchange-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
}

.exchange-time {
  font-size: 13px;
  color: #6b7280;
}

.exchange-action {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.exchange-points {
  font-size: 15px;
  font-weight: 600;
  color: #ba68c8;
  white-space: nowrap;
}
</style>

