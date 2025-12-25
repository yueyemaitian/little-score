<template>
  <div class="voice-test-container">
    <van-nav-bar title="语音识别测试" left-arrow @click-left="$router.back()" />
    
    <div class="test-content">
      <!-- 环境信息 -->
      <van-cell-group inset style="margin: 16px 0;">
        <van-cell title="浏览器信息" :value="browserInfo" />
        <van-cell title="是否微信浏览器" :value="isWeChat ? '是' : '否'" />
        <van-cell title="Web Speech API" :value="speechApiSupported ? '支持' : '不支持'" />
        <van-cell title="MediaRecorder API" :value="mediaRecorderSupported ? '支持' : '不支持'" />
        <van-cell title="WebRTC (getUserMedia)" :value="webrtcSupported ? '支持' : '不支持'" />
        <van-cell title="微信 JS-SDK" :value="wechatJSSDKReady ? '已加载' : (isWeChat ? '未加载' : '非微信环境')" />
      </van-cell-group>

      <!-- 识别结果 -->
      <van-cell-group inset style="margin: 16px 0;">
        <van-cell title="识别结果" />
        <div class="result-area">
          <div v-if="recognizedText" class="result-text">{{ recognizedText }}</div>
          <div v-else class="result-placeholder">识别结果将显示在这里...</div>
        </div>
      </van-cell-group>

      <!-- Web Speech API 测试 -->
      <van-cell-group inset style="margin: 16px 0;" v-if="speechApiSupported">
        <van-cell title="方案1: Web Speech API" />
        <div class="button-area">
          <van-button
            :type="isListening ? 'danger' : 'primary'"
            size="large"
            round
            :icon="isListening ? 'pause-circle-o' : 'audio'"
            @click="toggleWebSpeech"
            :loading="isProcessing"
            :disabled="isProcessing"
          >
            {{ isListening ? '停止识别' : '开始识别（Web Speech API）' }}
          </van-button>
        </div>
        <div v-if="error" class="error-message">{{ error }}</div>
      </van-cell-group>

      <!-- MediaRecorder API 测试 -->
      <van-cell-group inset style="margin: 16px 0;" v-if="mediaRecorderSupported && !isWeChat">
        <van-cell title="方案2: MediaRecorder + 后端识别" />
        <div class="button-area">
          <van-button
            :type="isRecording ? 'danger' : 'primary'"
            size="large"
            round
            :icon="isRecording ? 'pause-circle-o' : 'audio'"
            @click="toggleMediaRecorder"
            :loading="isUploading"
            :disabled="isUploading"
          >
            {{ isRecording ? '停止录音' : '开始录音（MediaRecorder）' }}
          </van-button>
        </div>
        <div v-if="recordError" class="error-message">{{ recordError }}</div>
        <div v-if="recordingTime > 0" class="recording-time">
          录音时长: {{ formatTime(recordingTime) }}
        </div>
      </van-cell-group>

      <!-- 微信 JS-SDK 测试 -->
      <van-cell-group inset style="margin: 16px 0;" v-if="isWeChat">
        <van-cell title="方案3: 微信 JS-SDK 录音" />
        <div class="button-area">
          <van-button
            :type="isWeChatRecording ? 'danger' : 'primary'"
            size="large"
            round
            :icon="isWeChatRecording ? 'pause-circle-o' : 'audio'"
            @click="toggleWeChatRecord"
            :loading="isWeChatUploading"
            :disabled="isWeChatUploading || !wechatJSSDKReady"
          >
            {{ isWeChatRecording ? '停止录音' : '开始录音（微信 JS-SDK）' }}
          </van-button>
        </div>
        <div v-if="wechatError" class="error-message">{{ wechatError }}</div>
        <div v-if="wechatRecordingTime > 0" class="recording-time">
          录音时长: {{ formatTime(wechatRecordingTime) }}
        </div>
        <div v-if="!wechatJSSDKReady && isWeChat" class="error-message" style="color: #ff9800;">
          提示：需要配置微信 JS-SDK 才能使用此功能
        </div>
      </van-cell-group>

      <!-- WebRTC 录音测试 -->
      <van-cell-group inset style="margin: 16px 0;" v-if="webrtcSupported">
        <van-cell title="方案4: WebRTC 录音 + 后端识别" />
        <div class="button-area">
          <van-button
            :type="isWebRTCRecording ? 'danger' : 'primary'"
            size="large"
            round
            :icon="isWebRTCRecording ? 'pause-circle-o' : 'audio'"
            @click="toggleWebRTCRecord"
            :loading="isWebRTCUploading"
            :disabled="isWebRTCUploading"
          >
            {{ isWebRTCRecording ? '停止录音' : '开始录音（WebRTC）' }}
          </van-button>
        </div>
        <div v-if="webrtcError" class="error-message">{{ webrtcError }}</div>
        <div v-if="webrtcRecordingTime > 0" class="recording-time">
          录音时长: {{ formatTime(webrtcRecordingTime) }}
        </div>
      </van-cell-group>

      <!-- 音频上传测试 -->
      <van-cell-group inset style="margin: 16px 0;">
        <van-cell title="方案5: 上传音频文件" />
        <div class="button-area">
          <van-uploader
            v-model="fileList"
            :after-read="handleFileUpload"
            accept="audio/*"
            :max-count="1"
          >
            <van-button size="large" round icon="upload">
              选择音频文件上传
            </van-button>
          </van-uploader>
        </div>
      </van-cell-group>

      <!-- 清除按钮 -->
      <div class="button-area" style="margin-top: 20px;">
        <van-button size="large" round @click="clearResult">清除结果</van-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'
import { aiApi } from '../api/ai'

// 环境检测
const browserInfo = ref('')
const isWeChat = ref(false)
const speechApiSupported = ref(false)
const mediaRecorderSupported = ref(false)
const webrtcSupported = ref(false)
const wechatJSSDKReady = ref(false)

// Web Speech API 相关
let recognition = null
const isListening = ref(false)
const isProcessing = ref(false)
const recognizedText = ref('')
const error = ref('')

// MediaRecorder API 相关
let mediaRecorder = null
let audioChunks = []
let recordingTimer = null
const isRecording = ref(false)
const isUploading = ref(false)
const recordingTime = ref(0)
const recordError = ref('')

// 文件上传
const fileList = ref([])

// 微信 JS-SDK 相关
const isWeChatRecording = ref(false)
const isWeChatUploading = ref(false)
const wechatRecordingTime = ref(0)
const wechatError = ref('')
let wechatRecordingTimer = null
let wechatLocalId = null

// WebRTC 相关
let webrtcStream = null
let webrtcMediaRecorder = null
let webrtcAudioChunks = []
let webrtcRecordingTimer = null
const isWebRTCRecording = ref(false)
const isWebRTCUploading = ref(false)
const webrtcRecordingTime = ref(0)
const webrtcError = ref('')

// 检测环境
onMounted(() => {
  // 检测浏览器信息
  browserInfo.value = navigator.userAgent
  
  // 检测是否微信浏览器
  isWeChat.value = /MicroMessenger/i.test(navigator.userAgent)
  
  // 检测 Web Speech API
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (SpeechRecognition) {
    speechApiSupported.value = true
    try {
      recognition = new SpeechRecognition()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'zh-CN'
      
      recognition.onstart = () => {
        isListening.value = true
        error.value = ''
      }
      
      recognition.onresult = (event) => {
        let interimTranscript = ''
        let finalTranscript = ''
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            finalTranscript += transcript
          } else {
            interimTranscript += transcript
          }
        }
        
        recognizedText.value = finalTranscript || interimTranscript
      }
      
      recognition.onerror = (event) => {
        console.error('Web Speech API 错误:', event.error)
        isListening.value = false
        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
          error.value = '请允许麦克风权限或使用其他方案'
          showFailToast('请允许麦克风权限或使用其他方案')
        } else if (event.error !== 'aborted' && event.error !== 'no-speech') {
          error.value = `识别错误: ${event.error}`
          showFailToast(`识别错误: ${event.error}`)
        }
      }
      
      recognition.onend = () => {
        isListening.value = false
      }
    } catch (err) {
      console.error('初始化 Web Speech API 失败:', err)
      speechApiSupported.value = false
    }
  }
  
  // 检测 MediaRecorder API
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    mediaRecorderSupported.value = true
  }
  
  // 检测 WebRTC (getUserMedia)
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    webrtcSupported.value = true
  } else if (navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia) {
    webrtcSupported.value = true
  }
  
  // 检测并加载微信 JS-SDK
  if (isWeChat.value) {
    loadWeChatJSSDK()
  }
})

// 加载微信 JS-SDK
const loadWeChatJSSDK = () => {
  // 检查是否已经加载了微信 JS-SDK
  if (window.wx) {
    wechatJSSDKReady.value = true
    initWeChatJSSDK()
    return
  }
  
  // 动态加载微信 JS-SDK
  const script = document.createElement('script')
  script.src = 'https://res.wx.qq.com/open/js/jweixin-1.6.0.js'
  script.onload = () => {
    if (window.wx) {
      wechatJSSDKReady.value = true
      initWeChatJSSDK()
    } else {
      wechatError.value = '微信 JS-SDK 加载失败'
    }
  }
  script.onerror = () => {
    wechatError.value = '微信 JS-SDK 加载失败，请检查网络'
  }
  document.head.appendChild(script)
}

// 初始化微信 JS-SDK
const initWeChatJSSDK = async () => {
  if (!window.wx) {
    return
  }
  
  try {
    // 从后端获取微信 JS-SDK 配置
    const { authApi } = await import('../api/auth')
    // 获取当前页面的完整 URL（去除 hash，但保留 query 参数）
    const url = window.location.href.split('#')[0]
    const config = await authApi.getWechatJSSDKConfig(url)
    
    // 配置微信 JS-SDK
    window.wx.config({
      debug: false, // 生产环境设为 false
      appId: config.appId,
      timestamp: config.timestamp,
      nonceStr: config.nonceStr,
      signature: config.signature,
      jsApiList: ['startRecord', 'stopRecord', 'uploadVoice', 'onVoiceRecordEnd'] // 需要使用的 JS 接口列表
    })
    
    // 配置成功后的回调
    window.wx.ready(() => {
      console.log('微信 JS-SDK 配置成功')
      wechatError.value = ''
    })
    
    // 配置失败的回调
    window.wx.error((res) => {
      console.error('微信 JS-SDK 配置失败:', res)
      wechatError.value = `微信 JS-SDK 配置失败: ${res.errMsg || '未知错误'}`
    })
  } catch (error) {
    console.error('获取微信 JS-SDK 配置失败:', error)
    wechatError.value = `获取微信 JS-SDK 配置失败: ${error.message || '未知错误'}。请确保已配置微信 AppID 和 AppSecret`
  }
}

onUnmounted(() => {
  // 清理资源
  if (recognition && isListening.value) {
    recognition.stop()
  }
  if (mediaRecorder && isRecording.value) {
    mediaRecorder.stop()
    mediaRecorder.stream?.getTracks().forEach(track => track.stop())
  }
  if (recordingTimer) {
    clearInterval(recordingTimer)
  }
  if (wechatRecordingTimer) {
    clearInterval(wechatRecordingTimer)
  }
  if (webrtcRecordingTimer) {
    clearInterval(webrtcRecordingTimer)
  }
  if (webrtcStream) {
    webrtcStream.getTracks().forEach(track => track.stop())
  }
})

// Web Speech API 切换
const toggleWebSpeech = () => {
  if (!recognition) {
    showFailToast('Web Speech API 不支持')
    return
  }
  
  if (isListening.value) {
    recognition.stop()
  } else {
    recognizedText.value = ''
    error.value = ''
    try {
      recognition.start()
    } catch (err) {
      console.error('启动识别失败:', err)
      error.value = '启动识别失败，请重试'
      showFailToast('启动识别失败，请重试')
    }
  }
}

// MediaRecorder API 切换
const toggleMediaRecorder = async () => {
  if (isRecording.value) {
    // 停止录音
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
    }
    if (recordingTimer) {
      clearInterval(recordingTimer)
      recordingTimer = null
    }
    recordingTime.value = 0
  } else {
    // 开始录音
    try {
      recordError.value = ''
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      audioChunks = []
      
      mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus' || 'audio/webm' || 'audio/mp4'
      })
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunks.push(event.data)
        }
      }
      
      mediaRecorder.onstop = async () => {
        isRecording.value = false
        stream.getTracks().forEach(track => track.stop())
        
        if (audioChunks.length === 0) {
          recordError.value = '没有录制到音频数据'
          return
        }
        
        // 上传音频文件
        const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType })
        await uploadAudio(audioBlob)
      }
      
      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder 错误:', event.error)
        recordError.value = `录音错误: ${event.error}`
        isRecording.value = false
        stream.getTracks().forEach(track => track.stop())
      }
      
      mediaRecorder.start()
      isRecording.value = true
      
      // 开始计时
      recordingTime.value = 0
      recordingTimer = setInterval(() => {
        recordingTime.value++
      }, 1000)
      
    } catch (err) {
      console.error('启动录音失败:', err)
      recordError.value = err.message || '启动录音失败，请检查麦克风权限'
      showFailToast(recordError.value)
    }
  }
}

// 上传音频文件
const uploadAudio = async (audioBlob) => {
  isUploading.value = true
  recordError.value = ''
  
  try {
    const result = await aiApi.recognizeAudio(audioBlob)
    
    if (result.success && result.intent) {
      const text = result.intent.data?.corrected_text || result.intent.message || '识别成功'
      recognizedText.value = text
      showSuccessToast('识别成功')
    } else {
      recordError.value = result.error || '识别失败'
      showFailToast(recordError.value)
    }
  } catch (err) {
    console.error('上传音频失败:', err)
    recordError.value = err.response?.data?.detail || err.message || '上传失败'
    showFailToast(recordError.value)
  } finally {
    isUploading.value = false
  }
}

// 处理文件上传
const handleFileUpload = async (file) => {
  if (!file.file) {
    showFailToast('请选择音频文件')
    return
  }
  
  await uploadAudio(file.file)
}

// 格式化时间
const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 微信 JS-SDK 录音切换
const toggleWeChatRecord = () => {
  if (!window.wx) {
    wechatError.value = '微信 JS-SDK 未加载'
    showFailToast('微信 JS-SDK 未加载')
    return
  }
  
  if (isWeChatRecording.value) {
    // 停止录音
    window.wx.stopRecord({
      success: async (res) => {
        isWeChatRecording.value = false
        wechatLocalId = res.localId
        
        if (wechatRecordingTimer) {
          clearInterval(wechatRecordingTimer)
          wechatRecordingTimer = null
        }
        wechatRecordingTime.value = 0
        
        // 上传录音文件
        await uploadWeChatAudio(wechatLocalId)
      },
      fail: (err) => {
        console.error('停止录音失败:', err)
        wechatError.value = '停止录音失败'
        isWeChatRecording.value = false
        if (wechatRecordingTimer) {
          clearInterval(wechatRecordingTimer)
          wechatRecordingTimer = null
        }
        wechatRecordingTime.value = 0
      }
    })
  } else {
    // 开始录音
    wechatError.value = ''
    window.wx.startRecord({
      success: () => {
        isWeChatRecording.value = true
        wechatRecordingTime.value = 0
        wechatRecordingTimer = setInterval(() => {
          wechatRecordingTime.value++
        }, 1000)
      },
      cancel: () => {
        wechatError.value = '用户取消录音'
        isWeChatRecording.value = false
      },
      fail: (err) => {
        console.error('开始录音失败:', err)
        wechatError.value = err.errMsg || '开始录音失败'
        isWeChatRecording.value = false
        showFailToast(wechatError.value)
      }
    })
  }
}

// 上传微信录音
const uploadWeChatAudio = async (localId) => {
  if (!window.wx || !localId) {
    wechatError.value = '录音文件不存在'
    return
  }
  
  isWeChatUploading.value = true
  wechatError.value = ''
  
  try {
    // 先上传到微信服务器
    window.wx.uploadVoice({
      localId: localId,
      isShowProgressTips: 0,
      success: async (res) => {
        const serverId = res.serverId
        
        // 从微信服务器下载音频文件
        // 注意：实际使用时需要后端接口从微信服务器下载音频
        // 这里仅作为示例，实际需要调用后端接口
        wechatError.value = '提示：需要后端接口从微信服务器下载音频文件'
        showFailToast('需要后端接口支持')
        isWeChatUploading.value = false
        
        // 示例：如果有后端接口，可以这样调用
        // const result = await aiApi.downloadWeChatAudio(serverId)
        // if (result.success) {
        //   recognizedText.value = result.text
        //   showSuccessToast('识别成功')
        // }
      },
      fail: (err) => {
        console.error('上传录音失败:', err)
        wechatError.value = err.errMsg || '上传录音失败'
        showFailToast(wechatError.value)
        isWeChatUploading.value = false
      }
    })
  } catch (err) {
    console.error('处理录音失败:', err)
    wechatError.value = err.message || '处理录音失败'
    isWeChatUploading.value = false
  }
}

// WebRTC 录音切换
const toggleWebRTCRecord = async () => {
  if (isWebRTCRecording.value) {
    // 停止录音
    if (webrtcMediaRecorder && webrtcMediaRecorder.state !== 'inactive') {
      webrtcMediaRecorder.stop()
    }
    if (webrtcRecordingTimer) {
      clearInterval(webrtcRecordingTimer)
      webrtcRecordingTimer = null
    }
    webrtcRecordingTime.value = 0
    
    // 停止音频流
    if (webrtcStream) {
      webrtcStream.getTracks().forEach(track => track.stop())
      webrtcStream = null
    }
  } else {
    // 开始录音
    try {
      webrtcError.value = ''
      webrtcAudioChunks = []
      
      // 获取音频流
      const getUserMedia = navigator.mediaDevices?.getUserMedia ||
                          navigator.getUserMedia ||
                          navigator.webkitGetUserMedia ||
                          navigator.mozGetUserMedia
      
      if (!getUserMedia) {
        webrtcError.value = '浏览器不支持 getUserMedia'
        showFailToast('浏览器不支持 getUserMedia')
        return
      }
      
      const constraints = { audio: true }
      
      if (navigator.mediaDevices?.getUserMedia) {
        webrtcStream = await navigator.mediaDevices.getUserMedia(constraints)
      } else {
        // 兼容旧版 API
        webrtcStream = await new Promise((resolve, reject) => {
          getUserMedia.call(navigator, constraints, resolve, reject)
        })
      }
      
      // 创建 MediaRecorder
      const options = {
        mimeType: 'audio/webm;codecs=opus' || 'audio/webm' || 'audio/mp4'
      }
      
      webrtcMediaRecorder = new MediaRecorder(webrtcStream, options)
      
      webrtcMediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          webrtcAudioChunks.push(event.data)
        }
      }
      
      webrtcMediaRecorder.onstop = async () => {
        isWebRTCRecording.value = false
        
        if (webrtcAudioChunks.length === 0) {
          webrtcError.value = '没有录制到音频数据'
          return
        }
        
        // 上传音频文件
        const audioBlob = new Blob(webrtcAudioChunks, { type: webrtcMediaRecorder.mimeType })
        await uploadAudio(audioBlob)
      }
      
      webrtcMediaRecorder.onerror = (event) => {
        console.error('WebRTC MediaRecorder 错误:', event.error)
        webrtcError.value = `录音错误: ${event.error}`
        isWebRTCRecording.value = false
        if (webrtcStream) {
          webrtcStream.getTracks().forEach(track => track.stop())
          webrtcStream = null
        }
      }
      
      webrtcMediaRecorder.start()
      isWebRTCRecording.value = true
      
      // 开始计时
      webrtcRecordingTime.value = 0
      webrtcRecordingTimer = setInterval(() => {
        webrtcRecordingTime.value++
      }, 1000)
      
    } catch (err) {
      console.error('启动 WebRTC 录音失败:', err)
      webrtcError.value = err.message || '启动录音失败，请检查麦克风权限'
      showFailToast(webrtcError.value)
      isWebRTCRecording.value = false
    }
  }
}

// 清除结果
const clearResult = () => {
  recognizedText.value = ''
  error.value = ''
  recordError.value = ''
  wechatError.value = ''
  webrtcError.value = ''
  fileList.value = []
}
</script>

<style scoped>
.voice-test-container {
  min-height: 100vh;
  background: #f4f5f7;
}

.test-content {
  padding-bottom: 20px;
}

.result-area {
  padding: 16px;
  min-height: 100px;
  background: #ffffff;
}

.result-text {
  font-size: 16px;
  line-height: 1.6;
  color: #111827;
  word-break: break-word;
}

.result-placeholder {
  font-size: 14px;
  color: #9ca3af;
  text-align: center;
  padding: 20px 0;
}

.button-area {
  padding: 16px;
  display: flex;
  justify-content: center;
}

.error-message {
  padding: 8px 16px;
  color: #ef4444;
  font-size: 14px;
  text-align: center;
}

.recording-time {
  padding: 8px 16px;
  color: #6b7280;
  font-size: 14px;
  text-align: center;
}
</style>

