<template>
  <div class="voice-recorder">
    <slot
      :isListening="isListening"
      :isProcessing="isProcessing"
      :recognizedText="recognizedText"
      :error="error"
      :start="startRecording"
      :stop="stopRecording"
      :reset="reset"
      :supported="supported"
    >
      <!-- 默认 UI -->
      <van-button
        :type="isListening ? 'danger' : 'primary'"
        round
        size="large"
        :icon="isListening ? 'pause-circle-o' : 'audio'"
        @click="toggleRecording"
        :disabled="isProcessing || !supported"
        :loading="isProcessing"
      >
        {{ isListening ? '停止录音' : '开始录音' }}
      </van-button>
      <div v-if="!supported" class="unsupported-tip">
        <van-icon name="info-o" />
        <span>您的浏览器不支持语音识别，请使用文字输入</span>
      </div>
    </slot>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { showFailToast } from 'vant'
import { aiApi } from '../api/ai'

const props = defineProps({
  /**
   * 是否自动处理识别结果
   */
  autoProcess: {
    type: Boolean,
    default: true
  },
  /**
   * 实时识别时的语言设置
   */
  lang: {
    type: String,
    default: 'zh-CN'
  },
  /**
   * 实时识别时的连续模式
   */
  continuous: {
    type: Boolean,
    default: true
  },
  /**
   * 实时识别时的防抖延迟（毫秒）
   */
  debounceDelay: {
    type: Number,
    default: 1000
  }
})

const emit = defineEmits([
  'start',      // 开始录音
  'stop',       // 停止录音
  'result',     // 识别结果
  'error',      // 错误
  'text'        // 识别出的文本
])

// 状态
const isListening = ref(false)
const isProcessing = ref(false)
const recognizedText = ref('')
const error = ref(null)

// Web Speech API
let recognition = null
const speechSupported = ref(false)
let debounceTimer = null
let autoStopTimer = null // 自动停止定时器
let accumulatedText = ''
let lastResultTime = 0 // 最后一次收到结果的时间

// 是否支持语音识别
const supported = computed(() => {
  return speechSupported.value
})

onMounted(() => {
  // 检查 Web Speech API 支持
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (SpeechRecognition) {
    speechSupported.value = true
    recognition = new SpeechRecognition()
    recognition.continuous = props.continuous
    recognition.interimResults = true
    recognition.lang = props.lang

    recognition.onstart = () => {
      isListening.value = true
      accumulatedText = ''
      error.value = null
      lastResultTime = Date.now()
      // 清除之前的自动停止定时器
      if (autoStopTimer) {
        clearTimeout(autoStopTimer)
        autoStopTimer = null
      }
      emit('start')
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

      if (finalTranscript) {
        accumulatedText += finalTranscript
      }

      recognizedText.value = accumulatedText + interimTranscript
      emit('text', recognizedText.value)

      // 更新最后结果时间
      lastResultTime = Date.now()

      // 清除之前的定时器
      if (debounceTimer) {
        clearTimeout(debounceTimer)
        debounceTimer = null
      }
      if (autoStopTimer) {
        clearTimeout(autoStopTimer)
        autoStopTimer = null
      }

      // 如果有最终结果，立即处理（不需要等待防抖）
      if (finalTranscript) {
        const textToProcess = accumulatedText.trim()
        if (textToProcess) {
          // 停止识别
          if (recognition && isListening.value) {
            try {
              recognition.stop()
            } catch (err) {
              console.warn('停止识别失败:', err)
            }
          }
          if (props.autoProcess) {
            handleResult(textToProcess)
          } else {
            // 不自动处理时，发送最终文本
            emit('text', textToProcess)
          }
        }
      } else if (interimTranscript) {
        // 只有临时结果时，设置1秒自动停止定时器
        autoStopTimer = setTimeout(() => {
          // 检查是否在1秒内没有新的结果
          const timeSinceLastResult = Date.now() - lastResultTime
          if (timeSinceLastResult >= props.debounceDelay && isListening.value) {
            // 停止识别
            if (recognition && isListening.value) {
              try {
                recognition.stop()
              } catch (err) {
                console.warn('自动停止识别失败:', err)
              }
            }
            // 处理累积的文本
            const textToProcess = (accumulatedText + interimTranscript).trim()
            if (textToProcess) {
              if (props.autoProcess) {
                handleResult(textToProcess)
              } else {
                emit('text', textToProcess)
              }
            }
          }
          autoStopTimer = null
        }, props.debounceDelay)
      }
    }

    recognition.onerror = (event) => {
      console.error('语音识别错误:', event.error)
      isListening.value = false
      error.value = event.error

      if (debounceTimer) {
        clearTimeout(debounceTimer)
        debounceTimer = null
      }
      if (autoStopTimer) {
        clearTimeout(autoStopTimer)
        autoStopTimer = null
      }

      if (event.error === 'not-allowed') {
        error.value = '请允许麦克风权限'
        showFailToast('请允许麦克风权限')
      } else if (event.error === 'no-speech') {
        if (accumulatedText.trim() && props.autoProcess) {
          handleResult(accumulatedText.trim())
        }
      } else if (event.error !== 'aborted') {
        error.value = '语音识别出错，请重试'
        if (event.error !== 'network') {
          showFailToast('语音识别出错，请重试')
        }
      }
      
      emit('error', event.error)
    }

    recognition.onend = () => {
      isListening.value = false
      if (debounceTimer) {
        clearTimeout(debounceTimer)
        debounceTimer = null
      }
      if (autoStopTimer) {
        clearTimeout(autoStopTimer)
        autoStopTimer = null
      }
      // 识别结束时，处理累积的文本
      if (accumulatedText.trim() && !isProcessing.value) {
        if (props.autoProcess) {
          handleResult(accumulatedText.trim())
        } else {
          // 即使不自动处理，也要发送最终文本给父组件
          emit('text', accumulatedText.trim())
        }
      }
    }
  }
})

onUnmounted(() => {
  // 清理 Web Speech API
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
  if (autoStopTimer) {
    clearTimeout(autoStopTimer)
    autoStopTimer = null
  }
  if (recognition) {
    recognition.abort()
  }
})

// 处理识别结果
const handleResult = async (text) => {
  if (!text.trim()) return
  
  isProcessing.value = true
  recognizedText.value = text
  emit('text', text)
  
  if (props.autoProcess) {
    try {
      const result = await aiApi.parseVoiceCommand(text)
      emit('result', result)
    } catch (err) {
      console.error('解析失败:', err)
      error.value = err.response?.data?.detail || '解析失败，请重试'
      emit('error', err)
    } finally {
      isProcessing.value = false
    }
  } else {
    // 如果不自动处理，只发送文本，让父组件处理
    isProcessing.value = false
  }
}

// 开始录音
const startRecording = () => {
  if (recognition) {
    try {
      recognition.start()
    } catch (err) {
      console.error('启动语音识别失败:', err)
      error.value = '启动语音识别失败'
      emit('error', err)
    }
  } else {
    error.value = '您的浏览器不支持语音识别，请使用文字输入'
    showFailToast('您的浏览器不支持语音识别，请使用文字输入')
    emit('error', new Error('Speech Recognition API 不支持'))
  }
}

// 停止录音
const stopRecording = () => {
  if (recognition && isListening.value) {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    if (autoStopTimer) {
      clearTimeout(autoStopTimer)
      autoStopTimer = null
    }
    try {
      recognition.stop()
    } catch (err) {
      console.warn('停止语音识别失败:', err)
    }
  }
}

// 切换录音状态
const toggleRecording = () => {
  if (isListening.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

// 重置状态
const reset = () => {
  recognizedText.value = ''
  error.value = null
  accumulatedText = ''
  lastResultTime = 0
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
  if (autoStopTimer) {
    clearTimeout(autoStopTimer)
    autoStopTimer = null
  }
}

// 暴露方法
defineExpose({
  start: startRecording,
  stop: stopRecording,
  reset,
  isListening,
  isProcessing,
  recognizedText,
  error,
  supported
})
</script>

<style scoped>
.voice-recorder {
  width: 100%;
}

.unsupported-tip {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 10px;
  padding: 8px 12px;
  background-color: #fffbe8;
  border-left: 3px solid #ffe100;
  border-radius: 4px;
  font-size: 13px;
  color: #666;
}
</style>
