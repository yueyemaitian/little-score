import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Vant from 'vant'
import 'vant/lib/index.css'
import './style.css'
import './styles/responsive.css'
import App from './App.vue'
import router from './router'
import { useEnumsStore } from './stores/enums'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(Vant)

// 全局错误处理：捕获未处理的 Promise 错误
window.addEventListener('unhandledrejection', (event) => {
  const error = event.reason
  // 忽略 Vant 库中常见的正则匹配错误（通常不影响功能）
  if (error && error.message && (
    error.message.includes('Cannot read properties of null') ||
    error.message.includes('reading \'2\'') ||
    error.message.includes('reading \'1\'') ||
    error.message.includes('reading \'0\'') ||
    error.message.includes('exec') ||
    (error.message.includes('Cannot read') && error.message.includes('null'))
  )) {
    // 检查是否是 host 解析相关的错误
    if (error.message.includes('location.host') || error.stack?.includes('location.host')) {
      console.warn('捕获到 host 解析错误（已忽略）:', error.message)
      event.preventDefault() // 阻止错误在控制台显示
      return
    }
    console.warn('捕获到 Vant 库内部错误（已忽略）:', error.message)
    event.preventDefault() // 阻止错误在控制台显示
    return
  }
  // 其他错误正常处理
  console.error('未处理的 Promise 错误:', error)
})

// 全局错误处理：捕获运行时错误
window.addEventListener('error', (event) => {
  const error = event.error || event.message
  const errorMessage = typeof error === 'string' ? error : error?.message || ''
  const errorStack = event.error?.stack || ''
  
  // 忽略 Vant 库中常见的正则匹配错误
  if (error && (
    errorMessage.includes('Cannot read properties of null') ||
    errorMessage.includes('reading \'2\'') ||
    errorMessage.includes('reading \'1\'') ||
    errorMessage.includes('reading \'0\'') ||
    errorStack.includes('location.host') ||
    errorStack.includes('.exec(')
  )) {
    // 检查是否是 host 解析相关的错误
    if (errorMessage.includes('location.host') || errorStack.includes('location.host')) {
      console.warn('捕获到 host 解析错误（已忽略）:', errorMessage || error)
      event.preventDefault()
      return
    }
    console.warn('捕获到 Vant 库内部错误（已忽略）:', errorMessage || error)
    event.preventDefault()
    return
  }
  // 其他错误正常处理
  console.error('运行时错误:', error)
})

// 初始化枚举值
const enumsStore = useEnumsStore()
enumsStore.fetchEnums().catch(err => {
  console.error('初始化枚举值失败:', err)
})

app.mount('#app')
