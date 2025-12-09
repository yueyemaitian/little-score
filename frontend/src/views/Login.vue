<template>
  <div class="login-container">
    <div class="login-content">
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
          <van-button round block type="primary" native-type="submit" :loading="loading">
            登录
          </van-button>
          <div style="margin-top: 16px; text-align: center;">
            <van-button type="primary" plain size="small" @click="$router.push('/register')">
              还没有账号？去注册
            </van-button>
          </div>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast, showFailToast } from 'vant'
import { useAuthStore } from '../stores/auth'
import { extractErrorMessage } from '../utils/errorHandler'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  email: '',
  password: ''
})

const loading = ref(false)

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
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background: #f7f8fa;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.login-content {
  padding-top: 20px;
  width: 100%;
  flex: 1;
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
</style>


