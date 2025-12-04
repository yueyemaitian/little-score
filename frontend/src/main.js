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

// 初始化枚举值
const enumsStore = useEnumsStore()
enumsStore.fetchEnums().catch(err => {
  console.error('初始化枚举值失败:', err)
})

app.mount('#app')
