<template>
  <div class="login-container">
    <div class="login-content">
      <div class="app-description">
        <div class="app-title">积分管理</div>
        <div class="app-slogan">完成任务获得积分，用积分兑换奖励，培养良好习惯</div>
      </div>
      <div class="form-wrapper">
        <van-form @submit="onSubmit">
        <van-cell-group inset>
          <van-field
            v-model="form.email"
            name="email"
            label="邮箱"
            placeholder="请输入邮箱"
            :rules="[{ required: true, message: '请填写邮箱' }]"
            type="email"
          />
          <van-field
            v-model="form.password"
            type="password"
            name="password"
            label="密码"
            placeholder="请输入密码（6-20位）"
            :rules="passwordRules"
          />
        </van-cell-group>
        <div style="margin: 16px;">
          <!-- 邮箱登录 - 所有浏览器都显示 -->
          <div class="email-login-section">
            <van-button round block type="primary" native-type="submit" :loading="loading">
              邮箱登录
            </van-button>
          </div>
          
          <div style="margin-top: 16px; text-align: center;">
            <van-button type="primary" plain size="small" @click="$router.push('/register')">
              还没有账号？去注册
            </van-button>
          </div>
        </div>
      </van-form>
      </div>
      
      <!-- 圆形第三方登录按钮 - 在登录内容底部 -->
      <div class="third-party-login-wrapper">
        <div class="divider">
          <span>其他登录方式</span>
        </div>
        <div class="circular-login-buttons">
          <!-- 微信登录按钮 -->
          <button
            class="circular-login-btn circular-login-btn-wechat"
            :class="{ 'loading': wechatLoading }"
            :disabled="wechatLoading"
            @click="handleWechatLogin"
          >
            <van-icon name="wechat" />
          </button>
          
          <!-- 钉钉登录按钮 -->
          <button
            class="circular-login-btn circular-login-btn-dingtalk"
            :class="{ 'loading': dingtalkLoading }"
            :disabled="dingtalkLoading"
            @click="handleDingtalkLogin"
          >
          </button>
        </div>
      </div>
    </div>

    <!-- 微信登录弹窗（通用浏览器） -->
    <van-popup
      v-model:show="showWechatLoginDialog"
      position="center"
      round
      :style="{ width: '90%', maxWidth: '400px', padding: '20px' }"
      closeable
    >
      <div class="wechat-login-dialog">
        <div class="dialog-title">微信登录</div>
        <div class="dialog-tips">请使用微信扫码或打开链接完成登录</div>
        
        <!-- 二维码 -->
        <div class="qr-code-container" v-if="wechatAuthUrl">
          <canvas ref="qrCodeCanvas" class="qr-code-canvas"></canvas>
        </div>
        
        <!-- 操作按钮 -->
        <div class="dialog-actions">
          <van-button
            type="primary"
            block
            round
            @click="openWechatClient"
            style="margin-bottom: 10px;"
          >
            打开微信客户端
          </van-button>
          <van-button
            plain
            block
            round
            @click="copyAuthUrl"
          >
            复制链接
          </van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showSuccessToast, showFailToast } from 'vant'
import { useAuthStore } from '../stores/auth'
import { extractErrorMessage } from '../utils/errorHandler'
import { getBrowserType, getRecommendedLoginMethods } from '../utils/browser'
import { authApi } from '../api/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = ref({
  email: '',
  password: ''
})

const loading = ref(false)
const wechatLoading = ref(false)
const dingtalkLoading = ref(false)
const showWechatLoginDialog = ref(false)
const wechatAuthUrl = ref('')
const qrCodeCanvas = ref(null)

const browserType = ref(getBrowserType())
const recommendedMethods = computed(() => getRecommendedLoginMethods())

// 检查是否是推荐的登录方式
const isRecommended = (method) => {
  return recommendedMethods.value.includes(method) && recommendedMethods.value.indexOf(method) === 0
}

// 密码长度验证器
const validatePasswordLength = (val) => {
  if (!val) {
    return true // 空值由 required 规则处理
  }
  if (val.length < 6) {
    return '密码长度至少为6位'
  }
  if (val.length > 20) {
    return '密码长度不能超过20位'
  }
  return true
}

// 密码验证规则
const passwordRules = [
  { required: true, message: '请填写密码' },
  { validator: validatePasswordLength }
]

const onSubmit = async () => {
  // 前端验证密码长度
  if (form.value.password.length < 6) {
    showFailToast('密码长度至少为6位')
    return
  }
  if (form.value.password.length > 20) {
    showFailToast('密码长度不能超过20位')
    return
  }
  
  loading.value = true
  try {
    console.log('开始登录，邮箱:', form.value.email)
    await authStore.login(form.value.email, form.value.password)
    console.log('登录成功，准备跳转')
    showSuccessToast('登录成功')
    
    // 检查是否有学生，如果没有则跳转到添加学生页面
    try {
      const { studentsApi } = await import('../api/students')
      const students = await studentsApi.getList()
      console.log('学生列表:', students)
      
      if (students.length === 0) {
        console.log('没有学生，跳转到添加学生页面')
        router.push('/profile?action=add-student')
      } else {
        console.log('有学生，跳转到首页')
        router.push('/')
      }
    } catch (studentError) {
      console.error('获取学生列表失败:', studentError)
      // 即使获取学生列表失败，也跳转到首页
      router.push('/')
    }
  } catch (error) {
    // 详细的错误日志（开发环境）
    if (import.meta.env.DEV) {
      console.error('登录错误完整信息:', {
        error,
        errorType: typeof error,
        response: error.response,
        responseData: error.response?.data,
        responseDataType: typeof error.response?.data,
        responseStatus: error.response?.status,
        request: error.request,
        message: error.message
      })
    }
    
    const message = extractErrorMessage(error)
    
    // 确保显示错误提示
    try {
      showFailToast(message)
    } catch (toastError) {
      console.error('showFailToast 调用失败:', toastError)
      // 如果 showFailToast 失败，使用 alert 作为后备方案
      alert(message)
    }
  } finally {
    loading.value = false
  }
}

// 处理微信登录
const handleWechatLogin = async () => {
  wechatLoading.value = true
  try {
    // 检查URL参数中是否有code（从微信授权回调）
    const code = route.query.code
    if (code) {
      // 有code，说明是从微信授权回调回来的，直接登录
      const response = await authApi.loginWithWechat(code, route.query.state)
      await handleLoginSuccess(response)
    } else {
      // 没有code，需要重定向到微信授权页面
      if (browserType.value === 'wechat') {
        // 在微信浏览器中，使用网页授权
        try {
          // 从后端获取 AppID 和授权回调基础URL
          const appIdResponse = await authApi.getWechatAppId()
          const appId = appIdResponse.appId
          
          if (!appId) {
            showFailToast('微信登录功能需要配置微信AppID，请联系管理员')
            return
          }
          
          // 构建授权回调 URL
          // 如果后端配置了 redirectBaseUrl，使用配置的；否则使用当前访问的域名
          const baseUrl = appIdResponse.redirectBaseUrl || window.location.origin
          const redirectUri = encodeURIComponent(baseUrl + '/login/wechat')
          const state = 'wechat_login_' + Date.now() // 简单的 state，实际可以使用更复杂的随机字符串
          
          console.log('微信授权跳转:', { appId, baseUrl, redirectUri })
          
          // 跳转到微信授权页面
          const authUrl = `https://open.weixin.qq.com/connect/oauth2/authorize?appid=${appId}&redirect_uri=${redirectUri}&response_type=code&scope=snsapi_userinfo&state=${state}#wechat_redirect`
          window.location.href = authUrl
        } catch (error) {
          console.error('获取微信 AppID 失败:', error)
          const message = extractErrorMessage(error)
          showFailToast(message || '微信登录功能需要配置微信AppID，请联系管理员')
        }
      } else {
        // 在通用浏览器中，显示二维码和操作选项
        try {
          // 从后端获取 AppID 和授权回调基础URL
          const appIdResponse = await authApi.getWechatAppId()
          const appId = appIdResponse.appId
          
          if (!appId) {
            showFailToast('微信登录功能需要配置微信AppID，请联系管理员')
            return
          }
          
          // 构建授权回调 URL
          // 如果后端配置了 redirectBaseUrl，使用配置的；否则使用当前访问的域名
          const baseUrl = appIdResponse.redirectBaseUrl || window.location.origin
          const redirectUri = encodeURIComponent(baseUrl + '/login/wechat')
          const state = 'wechat_login_' + Date.now()
          
          // 构建授权URL
          wechatAuthUrl.value = `https://open.weixin.qq.com/connect/oauth2/authorize?appid=${appId}&redirect_uri=${redirectUri}&response_type=code&scope=snsapi_userinfo&state=${state}#wechat_redirect`
          
          // 显示弹窗
          showWechatLoginDialog.value = true
          
          // 生成二维码
          nextTick(() => {
            generateQRCode(wechatAuthUrl.value)
          })
        } catch (error) {
          console.error('获取微信 AppID 失败:', error)
          const message = extractErrorMessage(error)
          showFailToast(message || '微信登录功能需要配置微信AppID，请联系管理员')
        }
      }
    }
  } catch (error) {
    const message = extractErrorMessage(error)
    showFailToast(message)
  } finally {
    wechatLoading.value = false
  }
}

// 处理钉钉登录
const handleDingtalkLogin = async () => {
  dingtalkLoading.value = true
  try {
    // 检查URL参数中是否有code（从钉钉授权回调）
    const code = route.query.code
    if (code) {
      // 有code，说明是从钉钉授权回调回来的，直接登录
      const response = await authApi.loginWithDingtalk(code, route.query.state)
      await handleLoginSuccess(response)
    } else {
      // 没有code，需要重定向到钉钉授权页面
      if (browserType.value === 'dingtalk') {
        // 在钉钉浏览器中，使用钉钉JS-SDK
        // 注意：实际应用中，corpId应该从后端获取或配置
        showFailToast('钉钉登录功能需要配置钉钉AppKey，请联系管理员')
        // 实际实现示例（使用钉钉JS-SDK）：
        // if (typeof window.dd !== 'undefined') {
        //   window.dd.ready(() => {
        //     window.dd.runtime.permission.requestAuthCode({
        //       corpId: 'YOUR_DINGTALK_CORP_ID',
        //       onSuccess: async (result) => {
        //         const code = result.code
        //         const response = await authApi.loginWithDingtalk(code)
        //         await handleLoginSuccess(response)
        //       },
        //       onFail: (err) => {
        //         showFailToast('钉钉授权失败：' + err.errorMessage)
        //       }
        //     })
        //   })
        // }
      } else {
        // 在通用浏览器中，提示用户扫码登录
        // 实际应用中，应该显示二维码或跳转到扫码页面
        showFailToast('请在钉钉中打开，或使用钉钉扫码登录')
        // 实际实现示例：可以跳转到钉钉开放平台的扫码登录页面
        // 或者显示一个二维码供用户扫描
      }
    }
  } catch (error) {
    const message = extractErrorMessage(error)
    showFailToast(message)
  } finally {
    dingtalkLoading.value = false
  }
}

// 处理登录成功
const handleLoginSuccess = async (response) => {
  authStore.token = response.access_token
  localStorage.setItem('token', authStore.token)
  await authStore.fetchUser()
  showSuccessToast('登录成功')
  
  // 检查是否有学生，如果没有则跳转到添加学生页面
  try {
    const { studentsApi } = await import('../api/students')
    const students = await studentsApi.getList()
    
    if (students.length === 0) {
      router.push('/profile?action=add-student')
    } else {
      router.push('/')
    }
  } catch (studentError) {
    console.error('获取学生列表失败:', studentError)
    router.push('/')
  }
}

// 生成二维码
const generateQRCode = (url) => {
  if (!qrCodeCanvas.value) return
  
  // 使用在线API生成二维码（不需要安装额外库）
  const size = 200
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(url)}`
  
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    const canvas = qrCodeCanvas.value
    if (!canvas) return
    
    canvas.width = size
    canvas.height = size
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, size, size)
    ctx.drawImage(img, 0, 0, size, size)
  }
  img.onerror = () => {
    console.error('二维码生成失败')
    showFailToast('二维码生成失败，请使用复制链接功能')
  }
  img.src = qrUrl
}

// 打开微信客户端
const openWechatClient = () => {
  if (!wechatAuthUrl.value) {
    showFailToast('链接未生成')
    return
  }
  
  // 检测操作系统
  const userAgent = navigator.userAgent.toLowerCase()
  const isWindows = userAgent.indexOf('win') > -1
  const isMac = userAgent.indexOf('mac') > -1
  
  try {
    if (isWindows || isMac) {
      // Windows/Mac 系统：尝试使用 weixin:// 协议打开微信客户端
      // 注意：这个协议可能不总是有效，取决于微信客户端的安装和系统配置
      const weixinScheme = `weixin://dl/business/?t=${encodeURIComponent(wechatAuthUrl.value)}`
      
      // 先尝试打开微信客户端
      try {
        window.location.href = weixinScheme
        // 如果3秒后还在当前页面，说明可能没有安装微信客户端或协议无效
        setTimeout(() => {
          // 降级方案：在新窗口打开授权链接
          window.open(wechatAuthUrl.value, '_blank')
          showSuccessToast('请在微信中打开链接完成授权')
        }, 2000)
      } catch (error) {
        // 如果协议打开失败，直接在新窗口打开授权链接
        window.open(wechatAuthUrl.value, '_blank')
        showSuccessToast('已在新窗口打开，请在微信中完成授权')
      }
    } else {
      // 其他系统：直接在新窗口打开授权链接
      window.open(wechatAuthUrl.value, '_blank')
      showSuccessToast('已在新窗口打开，请在微信中完成授权')
    }
  } catch (error) {
    console.error('打开微信客户端失败:', error)
    // 降级方案：复制链接
    copyAuthUrl()
  }
}

// 复制授权链接
const copyAuthUrl = async () => {
  if (!wechatAuthUrl.value) {
    showFailToast('链接未生成')
    return
  }
  
  try {
    await navigator.clipboard.writeText(wechatAuthUrl.value)
    showSuccessToast('链接已复制，请在微信中打开')
  } catch (error) {
    // 降级方案：使用传统方法
    const textArea = document.createElement('textarea')
    textArea.value = wechatAuthUrl.value
    textArea.style.position = 'fixed'
    textArea.style.opacity = '0'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      showSuccessToast('链接已复制，请在微信中打开')
    } catch (err) {
      showFailToast('复制失败，请手动复制链接')
    }
    document.body.removeChild(textArea)
  }
}

// 检查URL参数中的授权码（从第三方授权回调）
onMounted(() => {
  const code = route.query.code
  const state = route.query.state
  
  if (code) {
    // 根据浏览器类型自动处理登录
    if (browserType.value === 'wechat') {
      handleWechatLogin()
    } else if (browserType.value === 'dingtalk') {
      handleDingtalkLogin()
    }
  }
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  min-height: 100dvh;
  background: #f7f8fa;
  width: 100%;
  display: flex;
  flex-direction: column;
  padding-bottom: 100px;
  position: relative;
  z-index: 1;
  overflow: visible;
  box-sizing: border-box;
}

.login-content {
  padding-top: 20px;
  padding-bottom: 40px;
  width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: visible;
  min-height: 0;
  box-sizing: border-box;
}

.app-description {
  text-align: center;
  padding: 40px 20px 20px;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.app-title {
  font-size: 24px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 12px;
}

.app-slogan {
  font-size: 15px;
  color: #6b7280;
  line-height: 1.5;
  padding: 0 20px;
}

.form-wrapper {
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: visible;
}

.third-party-login-wrapper {
  width: 100%;
  padding: 0 16px;
  margin-top: 24px;
  margin-bottom: 40px;
  position: relative;
  z-index: 2;
  flex-shrink: 0;
}

.circular-login-buttons {
  display: flex;
  gap: 24px;
  align-items: center;
  justify-content: center;
  margin-top: 16px;
  position: relative;
  z-index: 10;
  width: 100%;
  box-sizing: border-box;
}

.circular-login-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  position: relative;
  overflow: hidden;
  z-index: 10;
  flex-shrink: 0;
}

.circular-login-btn:active {
  transform: scale(0.95);
}

.circular-login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.circular-login-btn-wechat {
  background: linear-gradient(135deg, #07c160, #06ad56);
}

.circular-login-btn-dingtalk {
  background-image: url('/dingding.png');
  background-size: 100% 100%;
  background-position: center;
  background-repeat: no-repeat;
  background-color: transparent;
}

.circular-login-btn :deep(.van-icon) {
  font-size: 24px;
  color: #ffffff;
}


.circular-login-btn.loading :deep(.van-icon) {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 移动端适配 */
@media (max-width: 768px) {
  .login-container {
    padding-bottom: 120px;
  }
  
  .circular-login-buttons {
    margin-top: 24px;
    gap: 20px;
  }
  
  .circular-login-btn {
    width: 48px;
    height: 48px;
  }
  
  .circular-login-btn :deep(.van-icon) {
    font-size: 24px;
  }
}

@media (min-width: 768px) {
  .login-content {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
  }
}

@media (min-width: 1024px) {
  .login-container {
    max-width: 600px;
    margin: 0 auto;
  }
  
  .login-content {
    padding: 60px 40px;
  }
}

.recommended-login {
  background: linear-gradient(135deg, #07c160, #06ad56);
  border: none;
  box-shadow: 0 4px 12px rgba(7, 193, 96, 0.3);
}

.email-login-section {
  margin-bottom: 12px;
}

.other-login-section {
  margin-top: 12px;
}

.third-party-login-section {
  margin-bottom: 12px;
}

.divider {
  display: flex;
  align-items: center;
  margin: 16px 0;
  color: #969799;
  font-size: 14px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #ebedf0;
}

.divider span {
  padding: 0 16px;
}

.wechat-login-dialog {
  text-align: center;
}

.dialog-title {
  font-size: 20px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 8px;
}

.dialog-tips {
  font-size: 14px;
  color: #969799;
  margin-bottom: 20px;
}

.qr-code-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background: #f7f8fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.qr-code-canvas {
  display: block;
  max-width: 100%;
  height: auto;
}

.dialog-actions {
  margin-top: 20px;
}
</style>


