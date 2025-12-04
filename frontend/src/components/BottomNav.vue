<template>
  <van-tabbar v-model="activeTabbar" @change="onTabbarChange" fixed placeholder>
    <van-tabbar-item icon="home-o" to="/">首页</van-tabbar-item>
    <van-tabbar-item icon="orders-o" to="/tasks">任务</van-tabbar-item>
    <van-tabbar-item icon="gold-coin-o" to="/scores">积分</van-tabbar-item>
    <van-tabbar-item icon="user-o" to="/profile">我的</van-tabbar-item>
  </van-tabbar>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const activeTabbar = ref(0)

// 根据路由设置激活的标签
const updateActiveTabbar = () => {
  const path = route.path
  const tabMap = {
    '/': 0,
    '/tasks': 1,
    '/scores': 2,
    '/profile': 3
  }
  activeTabbar.value = tabMap[path] ?? 0
}

const onTabbarChange = (index) => {
  const routes = ['/', '/tasks', '/scores', '/profile']
  if (routes[index] && routes[index] !== route.path) {
    router.push(routes[index])
  }
}

// 监听路由变化
watch(() => route.path, updateActiveTabbar, { immediate: true })

onMounted(() => {
  updateActiveTabbar()
})
</script>

<style scoped>
/* 确保底部导航栏在所有设备上都显示 */
:deep(.van-tabbar) {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

/* 桌面端也显示，但可以调整样式 */
@media (min-width: 1024px) {
  :deep(.van-tabbar) {
    max-width: 600px;
    left: 50%;
    transform: translateX(-50%);
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  }
}
</style>

