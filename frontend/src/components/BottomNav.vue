<template>
  <van-tabbar
    v-model="activeTabbar"
    @change="onTabbarChange"
    :fixed="false"
    class="app-tabbar"
    active-color="#4A90E2"
  >
    <van-tabbar-item icon="home-o" to="/">首页</van-tabbar-item>
    <van-tabbar-item icon="orders-o" to="/tasks">任务</van-tabbar-item>
    <van-tabbar-item icon="gift-o" to="/scores">商城</van-tabbar-item>
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
.app-tabbar {
  border-top: 1px solid #e5e7eb;
  background-color: #ffffff;
  flex-shrink: 0; /* 确保底部导航不会被压缩 */
}
</style>

