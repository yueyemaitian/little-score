<template>
  <div class="voice-assistant">
    <!-- 语音助手按钮 -->
    <van-floating-bubble
      v-model:offset="position"
      axis="xy"
      magnetic="x"
      icon="service-o"
      @click="togglePanel"
      class="voice-bubble"
    />

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
            
            <template v-else-if="parseResult.error">
              <div class="error-message">{{ parseResult.error }}</div>
              <van-button plain round block @click="resetState" style="margin-top: 10px;">
                重试
              </van-button>
            </template>
          </div>

          <!-- 手动输入 -->
          <div class="manual-input">
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

          <!-- 录音按钮 -->
          <div class="record-button-area">
            <van-button
              :type="isListening ? 'danger' : 'primary'"
              round
              size="large"
              :icon="isListening ? 'pause-circle-o' : 'audio'"
              @click="toggleListening"
              :disabled="isProcessing || isWeChat"
              :loading="isProcessing"
            >
              {{ isListening ? '停止录音' : '开始语音输入' }}
            </van-button>
            <div v-if="isWeChat" class="wechat-tip">
              <van-icon name="info-o" />
              <span>微信浏览器暂不支持语音识别，请使用上方文字输入</span>
            </div>
          </div>

          <!-- 使用提示 -->
          <div class="usage-tips">
            <div class="tip-title">💡 试试这样说：</div>
            <div class="tip-item">"语文单元形评获得A*，奖励10积分"</div>
            <div class="tip-item">"积分兑换10元"</div>
          </div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { showFailToast, showSuccessToast } from 'vant'
import { aiApi } from '../api/ai'
import { useStudentsStore } from '../stores/students'

const router = useRouter()
const studentsStore = useStudentsStore()
const emit = defineEmits(['navigate-with-data'])

// 状态
const showPanel = ref(false)
const isListening = ref(false)
const isProcessing = ref(false)
const recognizedText = ref('')
const manualText = ref('')
const parseResult = ref(null)
const position = ref({ x: window.innerWidth - 70, y: window.innerHeight - 200 })

// 检测是否在微信浏览器中
const isWeChat = computed(() => {
  return /MicroMessenger/i.test(navigator.userAgent)
})

// 语音识别相关
let recognition = null
let speechSupported = false
let debounceTimer = null  // 防抖定时器
let accumulatedText = ''   // 累积的文本

onMounted(() => {
  // 检查浏览器是否支持语音识别
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  
  // 微信浏览器虽然可能检测到 SpeechRecognition，但实际上不支持
  if (SpeechRecognition && !isWeChat.value) {
    speechSupported = true
    recognition = new SpeechRecognition()
    recognition.continuous = true  // 改为连续模式，以便检测停顿
    recognition.interimResults = true
    recognition.lang = 'zh-CN'

    recognition.onstart = () => {
      isListening.value = true
      accumulatedText = ''  // 重置累积文本
      // 清除之前的定时器
      if (debounceTimer) {
        clearTimeout(debounceTimer)
        debounceTimer = null
      }
    }

    recognition.onresult = (event) => {
      let finalTranscript = ''
      let interimTranscript = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript
        } else {
          interimTranscript += transcript
        }
      }

      // 累积最终结果
      if (finalTranscript) {
        accumulatedText += finalTranscript
      }

      // 显示当前识别的文本（最终结果 + 临时结果）
      recognizedText.value = accumulatedText + interimTranscript
      
      // 清除之前的定时器
      if (debounceTimer) {
        clearTimeout(debounceTimer)
        debounceTimer = null
      }
      
      // 如果有临时结果，等待1秒没有新的输入才处理
      if (interimTranscript) {
        // 设置1秒防抖，如果1秒内没有新的结果，则处理累积的文本
        debounceTimer = setTimeout(() => {
          const textToProcess = accumulatedText + interimTranscript
          if (textToProcess.trim()) {
            processVoiceInput(textToProcess.trim())
          }
          debounceTimer = null
        }, 1000)
      } else if (finalTranscript && !interimTranscript) {
        // 如果只有最终结果且没有临时结果，说明识别结束，立即处理
        const textToProcess = accumulatedText.trim()
        if (textToProcess) {
          processVoiceInput(textToProcess)
        }
      }
    }

    recognition.onerror = (event) => {
      console.error('语音识别错误:', event.error, event)
      isListening.value = false
      
      // 清除定时器
      if (debounceTimer) {
        clearTimeout(debounceTimer)
        debounceTimer = null
      }
      
      if (event.error === 'not-allowed') {
        showFailToast('请允许麦克风权限')
      } else if (event.error === 'no-speech') {
        // 如果没有检测到语音，不显示错误，可能是正常的停顿
        // 如果累积了文本，处理它
        if (accumulatedText.trim()) {
          processVoiceInput(accumulatedText.trim())
        }
      } else if (event.error === 'service-not-allowed') {
        // 服务不允许（可能是浏览器不支持或未启用）
        if (isWeChat.value) {
          showFailToast('微信浏览器暂不支持语音识别，请使用文字输入')
        } else {
          showFailToast('浏览器不支持语音识别功能，请使用文字输入')
        }
      } else if (event.error === 'aborted') {
        // 用户中止或系统中止，不显示错误
        console.log('语音识别已中止')
      } else if (event.error === 'network') {
        showFailToast('网络错误，请检查网络连接')
      } else if (event.error === 'audio-capture') {
        showFailToast('无法访问麦克风，请检查设备设置')
      } else {
        // 其他错误，显示详细错误信息（开发环境）或通用提示（生产环境）
        const errorMsg = import.meta.env.DEV 
          ? `语音识别出错: ${event.error}` 
          : (isWeChat.value ? '微信浏览器暂不支持语音识别，请使用文字输入' : '语音识别出错，请使用文字输入')
        showFailToast(errorMsg)
      }
    }

    recognition.onend = () => {
      isListening.value = false
      
      // 清除定时器
      if (debounceTimer) {
        clearTimeout(debounceTimer)
        debounceTimer = null
      }
      
      // 如果识别结束且有累积的文本，处理它
      if (accumulatedText.trim() && !isProcessing.value) {
        processVoiceInput(accumulatedText.trim())
      }
    }
  }
})

onUnmounted(() => {
  // 清除定时器
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
  
  if (recognition) {
    recognition.abort()
  }
})

const togglePanel = () => {
  showPanel.value = !showPanel.value
}

const toggleListening = () => {
  if (!speechSupported) {
    // 检测是否在微信浏览器中
    const isWeChat = /MicroMessenger/i.test(navigator.userAgent)
    const errorMsg = isWeChat 
      ? '微信浏览器暂不支持语音识别，请使用文字输入'
      : '您的浏览器不支持语音识别，请使用文字输入'
    showFailToast(errorMsg)
    return
  }

  if (isListening.value) {
    // 停止录音时，清除定时器并处理累积的文本
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    
    // 如果有累积的文本，先处理它
    if (accumulatedText.trim() && !isProcessing.value) {
      processVoiceInput(accumulatedText.trim())
    }
    
    try {
      recognition.stop()
    } catch (e) {
      console.warn('停止语音识别失败:', e)
      isListening.value = false
    }
  } else {
    resetState()
    accumulatedText = ''  // 重置累积文本
    try {
      recognition.start()
    } catch (e) {
      console.error('启动语音识别失败:', e)
      isListening.value = false
      const errorMsg = isWeChat.value
        ? '微信浏览器暂不支持语音识别，请使用文字输入'
        : '启动语音识别失败，请使用文字输入'
      showFailToast(errorMsg)
    }
  }
}

const resetState = () => {
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
  // 停止语音识别，避免继续监听
  if (recognition && isListening.value) {
    try {
      recognition.stop()
    } catch (e) {
      console.warn('停止语音识别失败:', e)
    }
  }
  
  // 清除防抖定时器
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
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

const confirmAction = () => {
  if (!parseResult.value?.success || !parseResult.value?.intent) return

  // 确保停止语音识别
  if (recognition && isListening.value) {
    try {
      recognition.stop()
    } catch (e) {
      console.warn('停止语音识别失败:', e)
    }
  }

  const intent = parseResult.value.intent
  const data = intent.data || {}
  
  // 获取当前学生ID（从 store 中获取）
  const currentStudentId = studentsStore.currentStudent?.id

  if (intent.action === 'add_task') {
    // 跳转到任务页面并传递预填数据
    const query = {
      action: 'add',
      prefill: encodeURIComponent(JSON.stringify({
        project_level1_id: data.project_level1_id,
        project_level2_id: data.project_level2_id,
        rating: data.rating,
        reward_points: data.reward_points,
        status: 'completed',
        reward_type: data.reward_points ? 'reward' : 'none'
      })),
      _t: Date.now()  // 添加时间戳，确保路由变化能被检测到
    }
    
    // 如果当前有选中的学生，传递学生ID
    if (currentStudentId) {
      query.student_id = currentStudentId
    }
    
    // 如果当前已经在任务页面，使用 replace 确保触发路由变化
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
    showFailToast('无法识别的操作类型')
  }

  resetState()
}
</script>

<style scoped>
.voice-assistant {
  position: relative;
  z-index: 1000;
}

.voice-bubble {
  --van-floating-bubble-size: 52px;
  --van-floating-bubble-background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

.wechat-tip {
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

.wechat-tip .van-icon {
  font-size: 16px;
  flex-shrink: 0;
}
</style>

