<template>
  <div class="app-root">
    <div class="app-shell">
      <!-- 可滚动内容区域：承载各个路由页面 -->
      <div class="page-content">
        <router-view />
      </div>
      <!-- 底部主导航 -->
      <BottomNav />
      <!-- 语音助手组件 - 仅在登录后显示 -->
      <VoiceAssistant v-if="authStore.isAuthenticated" />
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import VoiceAssistant from './components/VoiceAssistant.vue'
import BottomNav from './components/BottomNav.vue'

const authStore = useAuthStore()

onMounted(async () => {
  if (authStore.isAuthenticated) {
    try {
      await authStore.fetchUser()
    } catch (error) {
      console.error('Failed to fetch user:', error)
    }
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  width: 100%;
  height: 100%;
}

body {
  background-color: #e5e7eb;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100vh;
  min-height: 100dvh; /* 使用动态视口高度，适配移动浏览器 */
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue',
    Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow-x: hidden;
}

.app-root {
  width: 100%;
  display: flex;
  justify-content: center;
}

.app-shell {
  width: 100%;
  max-width: 420px;
  height: 100vh;
  height: 100dvh; /* 使用动态视口高度，适配移动浏览器 */
  max-height: 900px;
  background: #f9fafb;
  position: relative;
  box-shadow: 0 0 25px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

@media (min-width: 450px) {
  .app-shell {
    height: 90vh;
    margin-top: 40px;
    border-radius: 20px;
    border: 12px solid #fff;
  }
}

.page-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  padding-bottom: 2px; /* 预留底部导航高度（约50px），避免内容被遮挡 */
  position: relative;
  margin: 0 1px;
  min-height: 0; /* 确保 flex 子元素可以正确收缩 */
  box-sizing: border-box; /* 确保 padding 包含在总高度内 */
}

.page-content::-webkit-scrollbar {
  width: 0;
  background: transparent;
}
</style>
