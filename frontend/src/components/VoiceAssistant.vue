<template>
  <div class="voice-assistant" v-if="isSupported">
    <!-- 语音助手按钮 -->
    <div
      class="voice-bubble-fixed"
      @click="togglePanel"
    >
      <van-icon name="service-o" class="voice-bubble-icon" />
    </div>

    <!-- 语音助手面板 -->
    <van-popup
      v-model:show="showPanel"
      position="bottom"
      :style="{ height: 'auto', maxHeight: '70%' }"
      round
    >
      <div class="assistant-panel">
        <div class="panel-header">
          <span class="panel-title">🎤 AI 语音助手</span>
          <van-icon name="cross" class="close-icon" @click="showPanel = false" />
        </div>

        <div class="panel-content">
          <!-- 状态提示 -->
          <div class="status-area">
            <div v-if="isListening" class="listening-indicator">
              <div class="pulse-ring"></div>
              <van-icon name="volume-o" class="mic-icon listening" />
              <span>正在聆听...</span>
            </div>
            <div v-else-if="isProcessing" class="processing-indicator">
              <van-loading type="spinner" size="24" />
              <span>AI 正在理解您的意图...</span>
            </div>
            <div v-else class="idle-indicator">
              <van-icon name="service-o" class="mic-icon" />
              <span>点击下方按钮开始语音输入</span>
            </div>
          </div>

          <!-- 语音识别结果 -->
          <div v-if="recognizedText" class="recognized-text">
            <div class="text-label">您说的是：</div>
            <div class="text-content">{{ recognizedText }}</div>
          </div>

          <!-- AI 解析结果 -->
          <div v-if="parseResult" class="parse-result">
            <div class="result-header">
              <van-icon :name="parseResult.success ? 'passed' : 'warning-o'" 
                :class="parseResult.success ? 'success' : 'warning'" />
              <span>{{ parseResult.success ? '解析成功' : '解析失败' }}</span>
            </div>
            
            <template v-if="parseResult.success && parseResult.intent">
              <!-- AI 纠错后的理解 -->
              <div v-if="parseResult.intent.data?.corrected_text" class="corrected-text">
                <div class="corrected-label">🤖 AI 理解为：</div>
                <div class="corrected-content">{{ parseResult.intent.data.corrected_text }}</div>
              </div>

              <div class="intent-info">
                <div class="intent-action">
                  {{ getActionText(parseResult.intent.action) }}
                </div>
                <!-- 解析出的数据详情 -->
                <div v-if="parseResult.intent.action === 'add_task'" class="intent-details">
                  <div v-if="parseResult.intent.data.project_level1_name" class="detail-item">
                    <span class="detail-label">科目：</span>
                    <span class="detail-value">{{ parseResult.intent.data.project_level1_name_matched || parseResult.intent.data.project_level1_name }}</span>
                  </div>
                  <div v-if="parseResult.intent.data.project_level2_name" class="detail-item">
                    <span class="detail-label">项目：</span>
                    <span class="detail-value">{{ parseResult.intent.data.project_level2_name_matched || parseResult.intent.data.project_level2_name }}</span>
                  </div>
                  <div v-if="parseResult.intent.data.rating" class="detail-item">
                    <span class="detail-label">评分：</span>
                    <span class="detail-value highlight">{{ parseResult.intent.data.rating }}</span>
                  </div>
                  <div v-if="parseResult.intent.data.reward_points" class="detail-item">
                    <span class="detail-label">积分：</span>
                    <span class="detail-value highlight">+{{ parseResult.intent.data.reward_points }}</span>
                  </div>
                  <div v-if="parseResult.intent.data.punishment_option_name" class="detail-item">
                    <span class="detail-label">惩罚选项：</span>
                    <span class="detail-value highlight">{{ parseResult.intent.data.punishment_option_name_matched || parseResult.intent.data.punishment_option_name }}</span>
                  </div>
                </div>
                <div v-else-if="parseResult.intent.action === 'exchange_points'" class="intent-details">
                  <div v-if="parseResult.intent.data.reward_option_name" class="detail-item">
                    <span class="detail-label">兑换：</span>
                    <span class="detail-value">{{ parseResult.intent.data.reward_option_name }}</span>
                  </div>
                  <div v-if="parseResult.intent.data.cost_points" class="detail-item">
                    <span class="detail-label">消耗：</span>
                    <span class="detail-value highlight">-{{ parseResult.intent.data.cost_points }} 积分</span>
                  </div>
                </div>
                <div v-if="parseResult.intent.message" class="intent-message">
                  {{ parseResult.intent.message }}
                </div>
                <!-- 警告信息 -->
                <div v-if="parseResult.intent.warnings?.length" class="warnings">
                  <div v-for="(warning, idx) in parseResult.intent.warnings" :key="idx" class="warning-item">
                    <van-icon name="warning-o" /> {{ warning }}
                  </div>
                </div>
              </div>

              <!-- 确认按钮 -->
              <div class="action-buttons">
                <van-button type="primary" round block @click="confirmAction">
                  确认并跳转
                </van-button>
                <van-button plain round block @click="resetState" style="margin-top: 10px;">
                  重新输入
                </van-button>
              </div>
            </template>
            
            <template v-else-if="parseResult.error || (parseResult.intent && parseResult.intent.action === 'unknown')">
              <div class="error-message">
                {{ parseResult.error || '抱歉，我没有理解您的指令。' }}
              </div>
              <div class="action-buttons">
                <van-button type="primary" round block @click="confirmAction">
                  仍然跳转到新增任务
                </van-button>
                <van-button plain round block @click="resetState" style="margin-top: 10px;">
                  重新输入
                </van-button>
              </div>
            </template>
          </div>

          <!-- 手动输入（仅在未解析出结果时显示） -->
          <div v-if="!parseResult" class="manual-input">
            <van-field
              v-model="manualText"
              type="textarea"
              rows="2"
              placeholder="您也可以直接输入指令，如：语文单元形评获得A*，奖励10积分"
              :disabled="isListening || isProcessing"
            />
            <van-button 
              type="primary" 
              size="small" 
              round 
              @click="processManualInput"
              :disabled="!manualText.trim() || isProcessing"
              style="margin-top: 10px;"
            >
              发送
            </van-button>
          </div>

          <!-- 录音按钮（仅在未解析出结果时显示） -->
          <div v-if="!parseResult" class="record-button-area">
            <VoiceRecorder
              ref="voiceRecorderRef"
              :auto-process="false"
              :debounce-delay="2000"
              @result="handleVoiceResult"
              @text="handleVoiceText"
              @error="handleVoiceError"
            >
              <template #default="{ isListening: listening, isProcessing: processing, start, stop, supported }">
                <van-button
                  :type="listening ? 'danger' : 'primary'"
                  round
                  size="large"
                  :icon="listening ? 'pause-circle-o' : 'audio'"
                  @click="listening ? stop() : start()"
                  :disabled="processing || !supported"
                  :loading="processing"
                >
                  {{ listening ? '停止录音' : '开始语音输入' }}
                </van-button>
                <div v-if="!supported" class="unsupported-tip">
                  <van-icon name="info-o" />
                  <span>您的浏览器不支持语音识别，请使用上方文字输入</span>
                </div>
              </template>
            </VoiceRecorder>
          </div>

          <!-- 使用提示（仅在未解析出结果时显示） -->
          <div v-if="!parseResult" class="usage-tips">
            <div class="tip-title">💡 试试这样说：</div>
            <div class="tip-item">"语文单元形评获得A*，奖励10积分"</div>
            <div class="tip-item">"积分兑换10元"</div>
          </div>
        </div>
      </div>
    </van-popup>

    <!-- 引导新增一级项目弹窗 -->
    <van-popup 
      v-model:show="showProject1Form" 
      position="bottom" 
      :style="{ height: '60%' }" 
      closeable
      @close="handleProject1Cancel"
    >
      <van-nav-bar
        title="新增一级项目"
        left-arrow
        @click-left="handleProject1Cancel"
      />
      <ProjectForm
        v-if="showProject1Form && pendingPrefillData"
        :project="null"
        level="1"
        :prefilled-name="pendingPrefillData.project_level1_name"
        @success="handleProject1Success"
        @cancel="handleProject1Cancel"
      />
    </van-popup>

    <!-- 引导新增二级项目弹窗 -->
    <van-popup 
      v-model:show="showProject2Form" 
      position="bottom" 
      :style="{ height: '60%' }" 
      closeable
      @close="handleProject2Cancel"
    >
      <van-nav-bar
        title="新增二级项目"
        left-arrow
        @click-left="handleProject2Cancel"
      />
      <ProjectForm
        v-if="showProject2Form && pendingPrefillData"
        :project="null"
        level="2"
        :parent-id="createdProject1Id || pendingPrefillData.project_level1_id"
        :prefilled-name="pendingPrefillData.project_level2_name"
        @success="handleProject2Success"
        @cancel="handleProject2Cancel"
      />
    </van-popup>

    <!-- 引导新增惩罚选项弹窗 -->
    <van-popup 
      v-model:show="showPunishmentForm" 
      position="bottom" 
      :style="{ height: '60%' }" 
      closeable
      @close="handlePunishmentCancel"
    >
      <van-nav-bar
        title="新增惩罚选项"
        left-arrow
        @click-left="handlePunishmentCancel"
      />
      <PunishmentOptionForm
        v-if="showPunishmentForm && pendingPrefillData"
        :option="null"
        :prefilled-name="pendingPrefillData.punishment_option_name"
        @success="handlePunishmentSuccess"
        @cancel="handlePunishmentCancel"
      />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { showFailToast, showSuccessToast } from 'vant'
import { aiApi } from '../api/ai'
import { useStudentsStore } from '../stores/students'
import VoiceRecorder from './VoiceRecorder.vue'
import ProjectForm from './ProjectForm.vue'
import PunishmentOptionForm from './PunishmentOptionForm.vue'
import { projectsApi } from '../api/projects'
import { scoresApi } from '../api/scores'

const router = useRouter()
const studentsStore = useStudentsStore()
const emit = defineEmits(['navigate-with-data'])

// 状态
const showPanel = ref(false)
const isProcessing = ref(false)
const recognizedText = ref('')
const manualText = ref('')
const parseResult = ref(null)
const voiceRecorderRef = ref(null)

// 引导新增流程状态
const guideStep = ref(null) // 'project1' | 'project2' | 'punishment' | 'task' | null
const pendingPrefillData = ref(null) // 待创建任务的数据
const createdProject1Id = ref(null) // 已创建的一级项目ID
const createdProject2Id = ref(null) // 已创建的二级项目ID
const createdPunishmentId = ref(null) // 已创建的惩罚选项ID

// 引导弹窗显示状态
const showProject1Form = ref(false)
const showProject2Form = ref(false)
const showPunishmentForm = ref(false)

// 检测是否支持语音识别
const isSupported = ref(false)
onMounted(() => {
  // 检查 Web Speech API 支持
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  isSupported.value = !!SpeechRecognition
})

// 从 VoiceRecorder 组件获取状态
const isListening = computed(() => voiceRecorderRef.value?.isListening || false)

// 处理语音识别文本
let textProcessTimer = null
let lastTextTime = 0 // 最后一次收到文本的时间
const VOICE_INPUT_DELAY = 2000 // 用户停止输入2秒后再开始AI解析

const handleVoiceText = (text) => {
  recognizedText.value = text
  lastTextTime = Date.now() // 更新最后文本时间
  
  // 清除之前的定时器
  if (textProcessTimer) {
    clearTimeout(textProcessTimer)
    textProcessTimer = null
  }
  
  // 如果有文本且不在处理中，设置延迟处理
  if (text && text.trim() && !isProcessing.value) {
    // 等待用户停止输入2秒后再处理
    textProcessTimer = setTimeout(() => {
      // 检查：距离最后一次收到文本是否已经过了2秒
      const timeSinceLastText = Date.now() - lastTextTime
      if (timeSinceLastText >= VOICE_INPUT_DELAY && 
          !isProcessing.value && 
          recognizedText.value === text && 
          text.trim()) {
        // 如果还在识别中，等待识别结束
        if (isListening.value) {
          // 如果还在识别，再等待一小段时间
          setTimeout(() => {
            const timeSinceLastText2 = Date.now() - lastTextTime
            if (timeSinceLastText2 >= VOICE_INPUT_DELAY &&
                !isProcessing.value && 
                !isListening.value && 
                recognizedText.value === text) {
              processVoiceInput(text.trim())
            }
          }, 500)
        } else {
          // 识别已结束，且已经过了2秒，直接处理
          processVoiceInput(text.trim())
        }
      }
      textProcessTimer = null
    }, VOICE_INPUT_DELAY)
  }
}

// 处理语音识别结果
const handleVoiceResult = async (result) => {
  // 直接使用解析结果
  parseResult.value = result
  
  if (result.success && result.intent) {
    showSuccessToast('解析成功')
  }
}

// 处理语音识别错误
const handleVoiceError = (error) => {
  console.error('语音识别错误:', error)
  if (error && error !== 'aborted' && error !== 'no-speech') {
    showFailToast(error.message || error || '语音识别出错')
  }
}

const togglePanel = () => {
  showPanel.value = !showPanel.value
}

const resetState = () => {
  // 清除文本处理定时器
  if (textProcessTimer) {
    clearTimeout(textProcessTimer)
    textProcessTimer = null
  }
  lastTextTime = 0
  recognizedText.value = ''
  parseResult.value = null
  manualText.value = ''
}

const processManualInput = () => {
  if (manualText.value.trim()) {
    recognizedText.value = manualText.value.trim()
    processVoiceInput(manualText.value.trim())
  }
}

const processVoiceInput = async (text) => {
  // 清除文本处理定时器
  if (textProcessTimer) {
    clearTimeout(textProcessTimer)
    textProcessTimer = null
  }
  
  // 停止语音识别，避免继续监听
  if (voiceRecorderRef.value && isListening.value) {
    voiceRecorderRef.value.stop()
  }
  
  // 如果已经在处理中，忽略
  if (isProcessing.value) {
    return
  }
  
  isProcessing.value = true
  parseResult.value = null

  try {
    const result = await aiApi.parseVoiceCommand(text)
    parseResult.value = result
    
    if (result.success && result.intent) {
      showSuccessToast('解析成功')
    }
  } catch (error) {
    console.error('AI 解析失败:', error)
    parseResult.value = {
      success: false,
      error: error.response?.data?.detail || '解析失败，请重试'
    }
  } finally {
    isProcessing.value = false
  }
}

const getActionText = (action) => {
  const actionMap = {
    'add_task': '📝 新增任务',
    'exchange_points': '🎁 积分兑换',
    'unknown': '❓ 未识别的操作'
  }
  return actionMap[action] || '❓ 未知操作'
}

// 检测缺失的项目/选项，启动引导流程
const checkAndStartGuide = (prefillData) => {
  // 检测缺失的项目/选项
  const needsProject1 = prefillData.project_level1_name && !prefillData.project_level1_id
  const needsProject2 = prefillData.project_level2_name && !prefillData.project_level2_id
  const needsPunishment = prefillData.punishment_option_name && !prefillData.punishment_option_id && prefillData.reward_type === 'punish'
  
  // 如果有缺失的项目/选项，启动引导流程
  if (needsProject1 || needsProject2 || needsPunishment) {
    pendingPrefillData.value = prefillData
    createdProject1Id.value = null
    createdProject2Id.value = null
    createdPunishmentId.value = null
    
    // 按顺序启动引导：一级项目 -> 二级项目 -> 惩罚选项
    if (needsProject1) {
      guideStep.value = 'project1'
      showProject1Form.value = true
    } else if (needsProject2) {
      guideStep.value = 'project2'
      showProject2Form.value = true
    } else if (needsPunishment) {
      guideStep.value = 'punishment'
      showPunishmentForm.value = true
    }
    return true
  }
  return false
}

// 继续引导流程（创建成功后调用）
const continueGuide = () => {
  if (!pendingPrefillData.value) {
    return
  }
  
  const prefillData = pendingPrefillData.value
  const needsProject2 = prefillData.project_level2_name && !prefillData.project_level2_id && !createdProject2Id.value
  const needsPunishment = prefillData.punishment_option_name && !prefillData.punishment_option_id && !createdPunishmentId.value && prefillData.reward_type === 'punish'
  
  // 继续下一步引导
  if (needsProject2) {
    guideStep.value = 'project2'
    showProject2Form.value = true
  } else if (needsPunishment) {
    guideStep.value = 'punishment'
    showPunishmentForm.value = true
  } else {
    // 所有引导完成，跳转到新增任务页面
    navigateToTaskForm()
  }
}

// 跳转到新增任务页面
const navigateToTaskForm = () => {
  if (!pendingPrefillData.value) {
    return
  }
  
  const currentStudentId = studentsStore.currentStudent?.id
  const prefillData = { ...pendingPrefillData.value }
  
  // 使用已创建的项目/选项ID
  if (createdProject1Id.value) {
    prefillData.project_level1_id = createdProject1Id.value
  }
  if (createdProject2Id.value) {
    prefillData.project_level2_id = createdProject2Id.value
  }
  if (createdPunishmentId.value) {
    prefillData.punishment_option_id = createdPunishmentId.value
  }
  
  const query = {
    action: 'add',
    prefill: encodeURIComponent(JSON.stringify(prefillData)),
    _t: Date.now()
  }
  
  if (currentStudentId) {
    query.student_id = currentStudentId
  }
  
  if (router.currentRoute.value.path === '/tasks') {
    router.replace({
      path: '/tasks',
      query
    })
  } else {
    router.push({
      path: '/tasks',
      query
    })
  }
  
  // 清理引导状态
  guideStep.value = null
  pendingPrefillData.value = null
  createdProject1Id.value = null
  createdProject2Id.value = null
  createdPunishmentId.value = null
  showPanel.value = false
}

// 处理一级项目创建成功
const handleProject1Success = async (newProject) => {
  createdProject1Id.value = newProject.id
  showProject1Form.value = false
  showSuccessToast('一级项目创建成功')
  // 继续引导流程
  continueGuide()
}

// 处理二级项目创建成功
const handleProject2Success = async (newProject) => {
  createdProject2Id.value = newProject.id
  showProject2Form.value = false
  showSuccessToast('二级项目创建成功')
  // 继续引导流程
  continueGuide()
}

// 处理惩罚选项创建成功
const handlePunishmentSuccess = async (newOption) => {
  createdPunishmentId.value = newOption.id
  showPunishmentForm.value = false
  showSuccessToast('惩罚选项创建成功')
  // 继续引导流程
  continueGuide()
}

// 处理一级项目取消
const handleProject1Cancel = () => {
  showProject1Form.value = false
  guideStep.value = null
  // 清除一级项目的需求，标记为已跳过
  if (pendingPrefillData.value) {
    pendingPrefillData.value.project_level1_name = null
  }
  // 延迟执行，确保弹窗关闭后再继续
  setTimeout(() => {
    continueGuide()
  }, 200)
}

// 处理二级项目取消
const handleProject2Cancel = () => {
  showProject2Form.value = false
  guideStep.value = null
  // 清除二级项目的需求，标记为已跳过
  if (pendingPrefillData.value) {
    pendingPrefillData.value.project_level2_name = null
  }
  // 延迟执行，确保弹窗关闭后再继续
  setTimeout(() => {
    continueGuide()
  }, 200)
}

// 处理惩罚选项取消
const handlePunishmentCancel = () => {
  showPunishmentForm.value = false
  guideStep.value = null
  // 清除惩罚选项的需求，标记为已跳过
  if (pendingPrefillData.value) {
    pendingPrefillData.value.punishment_option_name = null
  }
  // 延迟执行，确保弹窗关闭后再继续
  setTimeout(() => {
    continueGuide()
  }, 200)
}

// 处理引导流程取消（跳过当前步骤，继续下一个）- 保留作为备用
const handleGuideCancel = () => {
  // 根据当前显示的弹窗判断
  if (showProject1Form.value) {
    handleProject1Cancel()
  } else if (showProject2Form.value) {
    handleProject2Cancel()
  } else if (showPunishmentForm.value) {
    handlePunishmentCancel()
  }
}

const confirmAction = () => {
  // 确保停止语音识别
  if (voiceRecorderRef.value && isListening.value) {
    voiceRecorderRef.value.stop()
  }

  // 获取当前学生ID（从 store 中获取）
  const currentStudentId = studentsStore.currentStudent?.id

  // 即使解析失败或 action 是 unknown，也允许跳转到新增任务页面
  const intent = parseResult.value?.intent
  const data = intent?.data || {}
  
  // 构建预填数据，包含所有可用的信息（包括未匹配的名称）
  const prefillData = {
    project_level1_id: data.project_level1_id || null,
    project_level2_id: data.project_level2_id || null,
    rating: data.rating || null,
    reward_points: data.reward_points || null,
    status: data.status || 'completed',
    reward_type: data.reward_type || (data.reward_points ? 'reward' : 'none'),
    // 传递未匹配的名称，用于创建新项目
    project_level1_name: data.project_level1_name || null,
    project_level2_name: data.project_level2_name || null,
    punishment_option_name: data.punishment_option_name || null,
    punishment_option_id: data.punishment_option_id || null,
    // 传递警告信息
    warnings: intent?.warnings || []
  }

  // 如果是新增任务或未知操作
  if (!intent || intent.action === 'add_task' || intent.action === 'unknown') {
    // 检测是否需要引导新增项目/选项
    if (checkAndStartGuide(prefillData)) {
      // 已启动引导流程，等待用户完成
      return
    }
    
    // 没有缺失的项目/选项，直接跳转
    navigateToTaskFormDirectly(prefillData, currentStudentId)
  } else if (intent.action === 'exchange_points') {
    // 跳转到积分页面并传递预填数据
    const query = {
      action: 'exchange',
      _t: Date.now()  // 添加时间戳，确保路由变化能被检测到
    }
    
    // 如果当前有选中的学生，传递学生ID
    if (currentStudentId) {
      query.student_id = currentStudentId
    }
    
    // 如果有预填数据，添加 prefill 参数
    if (data.reward_option_id) {
      query.prefill = encodeURIComponent(JSON.stringify({
        reward_option_id: data.reward_option_id
      }))
    }
    
    // 如果当前已经在积分页面，使用 replace 确保触发路由变化
    if (router.currentRoute.value.path === '/scores') {
      router.replace({
        path: '/scores',
        query
      })
    } else {
      router.push({
        path: '/scores',
        query
      })
    }
    showPanel.value = false
  } else {
    // 其他情况，默认跳转到新增任务页面
    navigateToTaskFormDirectly(prefillData, currentStudentId)
  }

  resetState()
}

// 直接跳转到新增任务页面（不经过引导流程）
const navigateToTaskFormDirectly = (prefillData, currentStudentId) => {
  const query = {
    action: 'add',
    prefill: encodeURIComponent(JSON.stringify(prefillData)),
    _t: Date.now()
  }
  
  if (currentStudentId) {
    query.student_id = currentStudentId
  }
  
  if (router.currentRoute.value.path === '/tasks') {
    router.replace({
      path: '/tasks',
      query
    })
  } else {
    router.push({
      path: '/tasks',
      query
    })
  }
  showPanel.value = false
}
</script>

<style scoped>
.voice-assistant {
  position: relative;
  z-index: 1000;
}

.voice-bubble-fixed {
  position: absolute;
  right: 16px;
  bottom: 80px;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  z-index: 1001;
  transition: transform 0.2s, box-shadow 0.2s;
}

.voice-bubble-fixed:active {
  transform: scale(0.95);
}

.voice-bubble-icon {
  font-size: 24px;
  color: #fff;
}

.assistant-panel {
  padding: 16px;
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16px;
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.close-icon {
  font-size: 20px;
  color: #999;
  cursor: pointer;
}

.status-area {
  text-align: center;
  padding: 20px 0;
}

.listening-indicator,
.processing-indicator,
.idle-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.mic-icon {
  font-size: 40px;
  color: #1989fa;
}

.mic-icon.listening {
  color: #ee0a24;
  animation: pulse 1s infinite;
}

.listening-indicator {
  position: relative;
}

.pulse-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: rgba(238, 10, 36, 0.2);
  animation: pulse-ring 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@keyframes pulse-ring {
  0% {
    transform: translate(-50%, -50%) scale(0.8);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%) scale(1.5);
    opacity: 0;
  }
}

.recognized-text {
  background: #f7f8fa;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
}

.text-label {
  font-size: 12px;
  color: #969799;
  margin-bottom: 6px;
}

.text-content {
  font-size: 15px;
  color: #323233;
  line-height: 1.5;
}

.parse-result {
  background: #fff;
  border: 1px solid #ebedf0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 12px;
}

.result-header .success {
  color: #07c160;
}

.result-header .warning {
  color: #ff976a;
}

.corrected-text {
  background: linear-gradient(135deg, #e8f4fd 0%, #d4ecfb 100%);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 12px;
  border-left: 3px solid #1989fa;
}

.corrected-label {
  font-size: 12px;
  color: #1989fa;
  margin-bottom: 4px;
}

.corrected-content {
  font-size: 15px;
  color: #323233;
  font-weight: 500;
}

.intent-info {
  margin-bottom: 16px;
}

.intent-action {
  font-size: 18px;
  font-weight: 600;
  color: #1989fa;
  margin-bottom: 8px;
}

.intent-details {
  background: #f7f8fa;
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 8px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 14px;
}

.detail-label {
  color: #969799;
}

.detail-value {
  color: #323233;
  font-weight: 500;
}

.detail-value.highlight {
  color: #07c160;
}

.intent-message {
  font-size: 14px;
  color: #646566;
  margin-bottom: 8px;
}

.warnings {
  background: #fffbe8;
  border-radius: 4px;
  padding: 8px 12px;
}

.warning-item {
  font-size: 13px;
  color: #ed6a0c;
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 4px 0;
}

.error-message {
  color: #ee0a24;
  font-size: 14px;
  text-align: center;
  padding: 12px;
}

.manual-input {
  margin-bottom: 16px;
}

.record-button-area {
  margin-bottom: 20px;
}

.usage-tips {
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7eb 100%);
  border-radius: 8px;
  padding: 12px;
}

.tip-title {
  font-size: 14px;
  font-weight: 500;
  color: #323233;
  margin-bottom: 8px;
}

.tip-item {
  font-size: 13px;
  color: #646566;
  padding: 4px 0;
  padding-left: 16px;
  position: relative;
}

.tip-item::before {
  content: "•";
  position: absolute;
  left: 4px;
  color: #1989fa;
}

.unsupported-tip {
  margin-top: 12px;
  padding: 10px;
  background: #fffbe8;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #ed6a0c;
}

.unsupported-tip .van-icon {
  font-size: 16px;
  flex-shrink: 0;
}
</style>

