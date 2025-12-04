<template>
  <div class="register-container">
    <van-nav-bar title="注册" left-arrow @click-left="$router.back()" />
    <div class="register-content">
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
          <van-field
            v-model="form.confirmPassword"
            type="password"
            name="confirmPassword"
            label="确认密码"
            placeholder="请再次输入密码"
            :rules="[
              { required: true, message: '请确认密码' },
              { validator: validatePassword }
            ]"
          />
        </van-cell-group>
        <div style="margin: 16px;">
          <van-button round block type="primary" native-type="submit" :loading="loading">
            注册
          </van-button>
          <div style="margin-top: 16px; text-align: center;">
            <van-button type="primary" plain size="small" @click="$router.push('/login')">
              已有账号？去登录
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
  password: '',
  confirmPassword: ''
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

// 确认密码验证器
const validatePassword = (val) => {
  if (val !== form.value.password) {
    return '两次输入的密码不一致'
  }
  return true
}

const onSubmit = async () => {
  loading.value = true
  try {
    await authStore.register(form.value.email, form.value.password)
    showSuccessToast('注册成功，请登录')
    router.push('/login')
  } catch (error) {
    console.error('注册失败:', error)
    const message = extractErrorMessage(error)
    showFailToast(message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  background: #f7f8fa;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.register-content {
  padding-top: 20px;
  width: 100%;
  flex: 1;
}

@media (min-width: 768px) {
  .register-content {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
  }
}

@media (min-width: 1024px) {
  .register-container {
    max-width: 600px;
    margin: 0 auto;
  }
  
  .register-content {
    padding: 60px 40px;
  }
}
</style>


