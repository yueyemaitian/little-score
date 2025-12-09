<template>
  <router-view />
  <!-- 语音助手组件 - 仅在登录后显示 -->
  <VoiceAssistant v-if="authStore.isAuthenticated" />
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import VoiceAssistant from './components/VoiceAssistant.vue'

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

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  width: 100%;
  overflow-x: hidden;
}

#app {
  width: 100%;
  min-height: 100vh;
}

/* 响应式布局 - 桌面端居中显示 */
@media (min-width: 1024px) {
  #app {
    max-width: 1400px;
    margin: 0 auto;
  }
}
</style>
