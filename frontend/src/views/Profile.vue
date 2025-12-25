<template>
  <div class="profile-container">
    <van-cell-group inset style="margin: 12px;">
      <van-cell title="账号管理" is-link @click="showAccountList = true" />
      <van-cell title="学生管理" is-link @click="showStudentList = true" />
      <van-cell title="一级项目" is-link @click="showProject1List = true" />
      <van-cell title="二级项目" is-link @click="showProject2List = true" />
      <van-cell title="惩罚选项" is-link @click="openPunishmentOptions" />
      <van-cell title="奖励选项" is-link @click="openRewardOptions" />
      <van-cell title="语音输入测试" is-link @click="goToVoiceTest" />
      <van-cell title="退出登录" is-link @click="handleLogout" />
    </van-cell-group>

    <!-- 账号管理列表 -->
    <van-popup v-model:show="showAccountList" position="bottom" :style="{ height: '80%' }">
      <van-nav-bar
        title="账号管理"
        left-arrow
        @click-left="showAccountList = false"
      />
      <div class="account-list-content">
        <van-loading v-if="loadingAccounts" vertical>加载中...</van-loading>
        <div v-else>
          <van-cell-group inset style="margin: 12px;">
            <van-cell
              v-for="account in accounts"
              :key="account.id"
              :title="getAccountTypeName(account.account_type)"
              :label="account.account_name || account.account_id"
              :value="account.account_type === 'email' ? '已绑定' : '已绑定'"
            >
              <template #icon>
                <van-icon :name="getAccountIcon(account.account_type)" style="margin-right: 8px;" />
              </template>
            </van-cell>
          </van-cell-group>
          
          <div class="bind-account-section">
            <div class="section-title">绑定账号</div>
            <van-cell-group inset style="margin: 12px;">
              <van-cell
                v-if="!hasAccountType('wechat')"
                title="微信"
                is-link
                @click="handleBindWechat"
              >
                <template #icon>
                  <van-icon name="wechat" style="margin-right: 8px;" />
                </template>
              </van-cell>
              <van-cell
                v-if="!hasAccountType('dingtalk')"
                title="钉钉"
                is-link
                @click="showBindDingtalk = true"
              >
                <template #icon>
                  <van-icon name="dingtalk" style="margin-right: 8px;" />
                </template>
              </van-cell>
              <van-cell
                v-if="!hasAccountType('email')"
                title="邮箱"
                is-link
                @click="showBindEmail = true"
              >
                <template #icon>
                  <van-icon name="envelop-o" style="margin-right: 8px;" />
                </template>
              </van-cell>
            </van-cell-group>
          </div>
        </div>
      </div>
    </van-popup>

    <!-- 绑定邮箱弹窗 -->
    <van-popup v-model:show="showBindEmail" position="bottom" :style="{ height: '60%' }">
      <van-nav-bar
        title="绑定邮箱"
        left-arrow
        @click-left="showBindEmail = false"
      />
      <van-form @submit="handleBindEmail" style="padding: 16px;">
        <van-cell-group inset>
          <van-field
            v-model="bindEmailForm.email"
            name="email"
            label="邮箱"
            placeholder="请输入邮箱"
            :rules="[{ required: true, message: '请填写邮箱' }]"
            type="email"
          />
          <van-field
            v-model="bindEmailForm.password"
            type="password"
            name="password"
            label="密码"
            placeholder="请输入密码（6-20位）"
            :rules="passwordRules"
          />
        </van-cell-group>
        <div style="margin: 16px;">
          <van-button round block type="primary" native-type="submit" :loading="binding">
            绑定
          </van-button>
        </div>
      </van-form>
    </van-popup>

    <!-- 绑定微信弹窗（非微信浏览器） -->
    <van-popup
      v-model:show="showBindWechatDialog"
      position="center"
      round
      :style="{ width: '90%', maxWidth: '400px', padding: '20px' }"
      closeable
    >
      <div class="wechat-bind-dialog">
        <div class="dialog-title">绑定微信</div>
        <div class="dialog-tips">请使用微信扫码或打开链接完成绑定</div>
        
        <!-- 二维码 -->
        <div class="qr-code-container" v-if="wechatBindAuthUrl">
          <canvas ref="wechatBindQrCodeCanvas" class="qr-code-canvas"></canvas>
        </div>
        
        <!-- 操作按钮 -->
        <div class="dialog-actions">
          <van-button
            type="primary"
            block
            round
            @click="openWechatClientForBind"
            style="margin-bottom: 10px;"
          >
            打开微信客户端
          </van-button>
          <van-button
            plain
            block
            round
            @click="copyBindAuthUrl"
          >
            复制链接
          </van-button>
        </div>
      </div>
    </van-popup>

    <!-- 绑定钉钉弹窗 -->
    <van-popup v-model:show="showBindDingtalk" position="bottom" :style="{ height: '60%' }">
      <van-nav-bar
        title="绑定钉钉"
        left-arrow
        @click-left="showBindDingtalk = false"
      />
      <div style="padding: 20px;">
        <div style="text-align: center; margin-bottom: 20px;">
          <van-icon name="dingtalk" size="60" color="#007fff" />
          <div style="margin-top: 16px; font-size: 16px; color: #323233;">
            绑定钉钉账号
          </div>
          <div style="margin-top: 8px; font-size: 14px; color: #969799;">
            绑定后可以使用钉钉快速登录
          </div>
        </div>
        <van-button
          type="primary"
          block
          round
          @click="handleBindDingtalk"
          :loading="binding"
        >
          开始绑定
        </van-button>
      </div>
    </van-popup>

    <!-- 学生管理列表 -->
    <van-popup v-model:show="showStudentList" position="bottom" :style="{ height: '80%' }">
      <van-nav-bar
        title="学生管理"
        left-arrow
        @click-left="showStudentList = false"
      >
        <template #right>
          <van-icon name="plus" @click="handleAddStudent" />
        </template>
      </van-nav-bar>
      <div class="student-list-content">
        <van-loading v-if="loading" vertical>加载中...</van-loading>
        <div v-else>
          <van-empty v-if="students.length === 0" description="暂无学生，请添加" />
          <van-cell-group v-else inset style="margin: 12px;">
            <van-cell
              v-for="student in students"
              :key="student.id"
              :title="student.name"
              :label="getStudentLabel(student)"
              is-link
              @click="editStudent(student)"
            >
              <template #right-icon>
                <van-icon name="delete-o" @click.stop="handleDeleteStudent(student)" />
              </template>
            </van-cell>
          </van-cell-group>
        </div>
        <div class="add-student-actions" v-if="!loading">
          <van-button round block type="primary" icon="plus" @click="handleAddStudent">
            新增学生
          </van-button>
        </div>
      </div>
    </van-popup>

    <!-- 学生表单弹窗 -->
    <van-popup v-model:show="showStudentForm" position="bottom" :style="{ height: '80%' }">
      <van-nav-bar
        :title="editingStudent ? '编辑学生' : '新增学生'"
        left-arrow
        @click-left="showStudentForm = false"
      />
      <StudentForm
        v-if="showStudentForm"
        :student="editingStudent"
        @success="handleStudentSuccess"
        @cancel="showStudentForm = false"
      />
    </van-popup>

    <!-- 一级项目列表 -->
    <van-popup v-model:show="showProject1List" position="bottom" :style="{ height: '80%' }">
      <van-nav-bar
        title="一级项目"
        left-arrow
        @click-left="showProject1List = false"
      />
      <ProjectList level="1" @close="showProject1List = false" />
    </van-popup>

    <!-- 二级项目列表 -->
    <van-popup v-model:show="showProject2List" position="bottom" :style="{ height: '80%' }">
      <van-nav-bar
        title="二级项目"
        left-arrow
        @click-left="showProject2List = false"
      />
      <ProjectList level="2" @close="showProject2List = false" />
    </van-popup>

    <!-- 新增一级项目表单 -->
    <van-popup v-model:show="showAddProject1Form" position="bottom" :style="{ height: '60%' }">
      <van-nav-bar
        title="新增一级项目"
        left-arrow
        @click-left="showAddProject1Form = false"
      />
      <ProjectForm
        v-if="showAddProject1Form"
        :project="null"
        level="1"
        @success="handleProjectSuccess"
        @cancel="showAddProject1Form = false"
      />
    </van-popup>

    <!-- 新增二级项目表单 -->
    <van-popup v-model:show="showAddProject2Form" position="bottom" :style="{ height: '60%' }">
      <van-nav-bar
        title="新增二级项目"
        left-arrow
        @click-left="showAddProject2Form = false"
      />
      <ProjectForm
        v-if="showAddProject2Form"
        :project="null"
        level="2"
        @success="handleProjectSuccess"
        @cancel="showAddProject2Form = false"
      />
    </van-popup>

    <!-- 惩罚选项列表 -->
    <van-popup v-model:show="showPunishmentOptions" position="bottom" :style="{ height: '80%' }">
      <van-nav-bar
        title="惩罚选项"
        left-arrow
        @click-left="showPunishmentOptions = false"
      />
      <PunishmentOptionList v-if="showPunishmentOptions" @close="showPunishmentOptions = false" />
    </van-popup>

    <!-- 兑换奖励选项列表 -->
    <van-popup v-model:show="showRewardOptions" position="bottom" :style="{ height: '80%' }">
      <van-nav-bar
        title="奖励选项"
        left-arrow
        @click-left="showRewardOptions = false"
      />
      <RewardOptionList v-if="showRewardOptions" @close="showRewardOptions = false" />
    </van-popup>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showConfirmDialog, showSuccessToast, showFailToast } from 'vant'
import { useAuthStore } from '../stores/auth'
import { useStudentsStore } from '../stores/students'
import { useEnumsStore } from '../stores/enums'
import { studentsApi } from '../api/students'
import { authApi } from '../api/auth'
import { extractErrorMessage } from '../utils/errorHandler'
import { getBrowserType } from '../utils/browser'
import StudentForm from '../components/StudentForm.vue'
import ProjectList from '../components/ProjectList.vue'
import ProjectForm from '../components/ProjectForm.vue'
import PunishmentOptionList from '../components/PunishmentOptionList.vue'
import RewardOptionList from '../components/RewardOptionList.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const studentsStore = useStudentsStore()
const enumsStore = useEnumsStore()

const loading = ref(false)
const loadingProjects = ref(false)
const students = ref([])
const showStudentList = ref(false)
const showStudentForm = ref(false)
const editingStudent = ref(null)
const showProject1List = ref(false)
const showProject2List = ref(false)
const showAddProject1Form = ref(false)
const showAddProject2Form = ref(false)
const showPunishmentOptions = ref(false)
const showRewardOptions = ref(false)
const editingProject = ref(null)
const wasEmptyBeforeAdd = ref(false) // 记录添加前是否为空

// 账号管理相关
const showAccountList = ref(false)
const loadingAccounts = ref(false)
const accounts = ref([])
const showBindEmail = ref(false)
const showBindWechat = ref(false)
const showBindWechatDialog = ref(false) // 非微信浏览器的绑定弹窗
const wechatBindAuthUrl = ref('')
const wechatBindQrCodeCanvas = ref(null)
const showBindDingtalk = ref(false)
const binding = ref(false)
const bindEmailForm = ref({
  email: '',
  password: ''
})

// 密码验证规则
const validatePasswordLength = (val) => {
  if (!val) {
    return true
  }
  if (val.length < 6) {
    return '密码长度至少为6位'
  }
  if (val.length > 20) {
    return '密码长度不能超过20位'
  }
  return true
}

const passwordRules = [
  { required: true, message: '请填写密码' },
  { validator: validatePasswordLength }
]

const getStudentLabel = (student) => {
  const genderOption = enumsStore.gender.find(g => g.value === student.gender)
  const stageOption = enumsStore.educationStage.find(s => s.value === student.stage)
  const genderText = genderOption ? genderOption.text : student.gender
  const stageText = stageOption ? stageOption.text : student.stage
  return `${genderText} | ${stageText}`
}

const fetchStudents = async () => {
  loading.value = true
  try {
    // 记录添加前的状态
    wasEmptyBeforeAdd.value = students.value.length === 0
    
    await studentsStore.fetchStudents()
    students.value = studentsStore.students
  } catch (error) {
    console.error('加载学生失败:', error)
  } finally {
    loading.value = false
  }
}

const editStudent = (student) => {
  editingStudent.value = student
  showStudentForm.value = true
}

const handleAddStudent = () => {
  editingStudent.value = null
  showStudentForm.value = true
}

const openPunishmentOptions = () => {
  console.log('Opening punishment options')
  showPunishmentOptions.value = true
}

const openRewardOptions = () => {
  console.log('Opening reward options')
  showRewardOptions.value = true
}

const handleStudentSuccess = () => {
  showStudentForm.value = false
  editingStudent.value = null
  
  // 记录添加前的状态
  const wasEmpty = students.value.length === 0
  
  fetchStudents().then(() => {
    // 如果添加前没有学生（从登录页面跳转过来的），添加完学生后跳转到首页
    if (wasEmpty && students.value.length > 0) {
      // 刚添加了第一个学生，跳转到首页
      router.push('/')
    }
    // 刷新学生列表显示
    if (showStudentList.value) {
      // 如果学生列表弹窗是打开的，保持打开状态
    }
  })
}

const handleDeleteStudent = async (student) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: `确定要删除学生"${student.name}"吗？删除后将同时删除该学生的所有任务和积分记录。`,
      confirmButtonText: '删除',
      confirmButtonColor: '#ee0a24',
    })
    
    loading.value = true
    try {
      await studentsApi.delete(student.id)
      showSuccessToast('删除成功')
      await fetchStudents()
    } catch (error) {
      const message = extractErrorMessage(error)
      showFailToast(message)
    } finally {
      loading.value = false
    }
  } catch {
    // 用户取消删除
  }
}

const goToVoiceTest = () => {
  router.push('/voice-test')
}

const handleLogout = async () => {
  try {
    await showConfirmDialog({
      title: '确认退出',
      message: '确定要退出登录吗？'
    })
    authStore.logout()
    router.push('/login')
  } catch {
    // 用户取消
  }
}

// 处理 URL 参数
const handleRouteAction = async () => {
  const action = route.query.action
  const code = route.query.code
  const state = route.query.state
  
  if (action === 'add-student') {
    // 打开学生管理列表
    showStudentList.value = true
    // 打开学生表单
    showStudentForm.value = true
    editingStudent.value = null
    // 清除 URL 参数
    router.replace({ path: '/profile', query: {} })
  } else if (action === 'bind-wechat' && code) {
    // 处理微信绑定回调
    await handleWechatBindCallback(code, state)
  } else if (action === 'bind-dingtalk' && code) {
    // 处理钉钉绑定回调
    await handleDingtalkBindCallback(code, state)
  }
}

// 处理微信绑定回调
const handleWechatBindCallback = async (code, state) => {
  binding.value = true
  try {
    // 通过 code 获取微信用户信息
    const wechatInfo = await authApi.getWechatUserInfo(code)
    
    // 绑定账号
    await authApi.bindAccount({
      account_type: 'wechat',
      account_id: wechatInfo.openid,
      account_name: wechatInfo.nickname,
      avatar_url: wechatInfo.headimgurl,
      extra_data: wechatInfo.extra_data
    })
    
    showSuccessToast('微信绑定成功')
    // 清除 URL 参数
    router.replace({ path: '/profile', query: {} })
    // 刷新账号列表
    await fetchAccounts()
  } catch (error) {
    console.error('微信绑定失败:', error)
    const message = extractErrorMessage(error)
    showFailToast(message || '微信绑定失败')
  } finally {
    binding.value = false
  }
}

// 处理钉钉绑定回调
const handleDingtalkBindCallback = async (code, state) => {
  binding.value = true
  try {
    // 类似微信绑定，需要调用后端接口
    showFailToast('钉钉绑定功能开发中')
  } catch (error) {
    console.error('钉钉绑定失败:', error)
    const message = extractErrorMessage(error)
    showFailToast(message || '钉钉绑定失败')
  } finally {
    binding.value = false
  }
}

// 监听路由变化
watch(() => route.query, () => {
  handleRouteAction()
}, { immediate: false })

// 获取账号类型名称
const getAccountTypeName = (type) => {
  const names = {
    email: '邮箱',
    wechat: '微信',
    dingtalk: '钉钉'
  }
  return names[type] || type
}

// 获取账号类型图标
const getAccountIcon = (type) => {
  const icons = {
    email: 'envelop-o',
    wechat: 'wechat',
    dingtalk: 'dingtalk'
  }
  return icons[type] || 'user-o'
}

// 检查是否已有某种类型的账号
const hasAccountType = (type) => {
  return accounts.value.some(account => account.account_type === type)
}

// 获取账号列表
const fetchAccounts = async () => {
  loadingAccounts.value = true
  try {
    accounts.value = await authApi.getMyAccounts()
  } catch (error) {
    console.error('获取账号列表失败:', error)
    showFailToast('获取账号列表失败')
  } finally {
    loadingAccounts.value = false
  }
}

// 绑定邮箱
const handleBindEmail = async () => {
  if (bindEmailForm.value.password.length < 6 || bindEmailForm.value.password.length > 20) {
    showFailToast('密码长度必须在6-20位之间')
    return
  }
  
  binding.value = true
  try {
    await authApi.bindAccount({
      account_type: 'email',
      account_id: bindEmailForm.value.email,
      password: bindEmailForm.value.password
    })
    showSuccessToast('绑定成功')
    showBindEmail.value = false
    bindEmailForm.value = { email: '', password: '' }
    await fetchAccounts()
  } catch (error) {
    const message = extractErrorMessage(error)
    showFailToast(message)
  } finally {
    binding.value = false
  }
}

// 绑定微信
const handleBindWechat = async () => {
  const browserType = getBrowserType()
  
  // 如果在微信浏览器中，直接走绑定流程
  if (browserType === 'wechat') {
    await startWechatBindFlow()
  } else {
    // 如果不在微信浏览器中，显示弹窗提供选项
    await showWechatBindOptions()
  }
}

// 开始微信绑定流程（在微信浏览器中）
const startWechatBindFlow = async () => {
  binding.value = true
  try {
    // 从后端获取 AppID 和授权回调基础URL
    const appIdResponse = await authApi.getWechatAppId()
    const appId = appIdResponse.appId
    
    if (!appId) {
      showFailToast('微信登录功能需要配置微信AppID，请联系管理员')
      return
    }
    
    // 构建授权回调 URL
    const baseUrl = appIdResponse.redirectBaseUrl || window.location.origin
    const redirectUri = encodeURIComponent(baseUrl + '/profile?action=bind-wechat')
    const state = 'bind_wechat_' + Date.now()
    
    console.log('微信绑定授权跳转:', { appId, baseUrl, redirectUri })
    
    // 跳转到微信授权页面
    const authUrl = `https://open.weixin.qq.com/connect/oauth2/authorize?appid=${appId}&redirect_uri=${redirectUri}&response_type=code&scope=snsapi_userinfo&state=${state}#wechat_redirect`
    window.location.href = authUrl
  } catch (error) {
    console.error('获取微信 AppID 失败:', error)
    const message = extractErrorMessage(error)
    showFailToast(message || '微信绑定功能需要配置微信AppID，请联系管理员')
  } finally {
    binding.value = false
  }
}

// 显示微信绑定选项（非微信浏览器）
const showWechatBindOptions = async () => {
  try {
    // 从后端获取 AppID 和授权回调基础URL
    const appIdResponse = await authApi.getWechatAppId()
    const appId = appIdResponse.appId
    
    if (!appId) {
      showFailToast('微信登录功能需要配置微信AppID，请联系管理员')
      return
    }
    
    // 构建授权回调 URL
    const baseUrl = appIdResponse.redirectBaseUrl || window.location.origin
    const redirectUri = encodeURIComponent(baseUrl + '/profile?action=bind-wechat')
    const state = 'bind_wechat_' + Date.now()
    
    // 构建授权URL
    wechatBindAuthUrl.value = `https://open.weixin.qq.com/connect/oauth2/authorize?appid=${appId}&redirect_uri=${redirectUri}&response_type=code&scope=snsapi_userinfo&state=${state}#wechat_redirect`
    
    // 显示绑定选项弹窗
    showBindWechatDialog.value = true
    
    // 生成二维码
    nextTick(() => {
      generateBindQRCode(wechatBindAuthUrl.value)
    })
  } catch (error) {
    console.error('获取微信 AppID 失败:', error)
    const message = extractErrorMessage(error)
    showFailToast(message || '微信绑定功能需要配置微信AppID，请联系管理员')
  }
}

// 生成绑定二维码
const generateBindQRCode = (url) => {
  if (!wechatBindQrCodeCanvas.value) return
  
  const size = 200
  const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(url)}`
  
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    const canvas = wechatBindQrCodeCanvas.value
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

// 打开微信客户端（用于绑定）
const openWechatClientForBind = () => {
  if (!wechatBindAuthUrl.value) {
    showFailToast('链接未生成')
    return
  }
  
  const userAgent = navigator.userAgent.toLowerCase()
  const isWindows = userAgent.indexOf('win') > -1
  const isMac = userAgent.indexOf('mac') > -1
  
  try {
    if (isWindows || isMac) {
      const weixinScheme = `weixin://dl/business/?t=${encodeURIComponent(wechatBindAuthUrl.value)}`
      try {
        window.location.href = weixinScheme
        setTimeout(() => {
          window.open(wechatBindAuthUrl.value, '_blank')
          showSuccessToast('请在微信中打开链接完成绑定')
        }, 2000)
      } catch (error) {
        window.open(wechatBindAuthUrl.value, '_blank')
        showSuccessToast('已在新窗口打开，请在微信中完成绑定')
      }
    } else {
      window.open(wechatBindAuthUrl.value, '_blank')
      showSuccessToast('已在新窗口打开，请在微信中完成绑定')
    }
  } catch (error) {
    console.error('打开微信客户端失败:', error)
    copyBindAuthUrl()
  }
}

// 复制绑定链接
const copyBindAuthUrl = async () => {
  if (!wechatBindAuthUrl.value) {
    showFailToast('链接未生成')
    return
  }
  
  try {
    await navigator.clipboard.writeText(wechatBindAuthUrl.value)
    showSuccessToast('链接已复制，请在微信中打开')
  } catch (error) {
    const textArea = document.createElement('textarea')
    textArea.value = wechatBindAuthUrl.value
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

// 绑定钉钉
const handleBindDingtalk = async () => {
  const browserType = getBrowserType()
  if (browserType !== 'dingtalk') {
    showFailToast('请在钉钉浏览器中绑定')
    return
  }
  
  // 触发钉钉授权流程
  showFailToast('钉钉绑定功能开发中，请通过钉钉登录后自动绑定')
}

// 监听账号管理弹窗
watch(showAccountList, (show) => {
  if (show) {
    fetchAccounts()
  }
})

onMounted(() => {
  fetchStudents()
  // 检查是否有 action 参数
  handleRouteAction()
})
</script>

<style scoped>
.profile-container {
  width: 100%;
}

.student-list-content {
  padding: 12px;
  height: calc(80vh - 46px);
  overflow-y: auto;
}

.add-student-actions {
  padding: 12px;
  padding-top: 0;
}

.wechat-bind-dialog {
  text-align: center;
}

.wechat-bind-dialog .dialog-title {
  font-size: 20px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 8px;
}

.wechat-bind-dialog .dialog-tips {
  font-size: 14px;
  color: #969799;
  margin-bottom: 20px;
}

.wechat-bind-dialog .qr-code-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background: #f7f8fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.wechat-bind-dialog .qr-code-canvas {
  display: block;
  max-width: 100%;
  height: auto;
}

.wechat-bind-dialog .dialog-actions {
  margin-top: 20px;
}
</style>

