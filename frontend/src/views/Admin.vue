<template>
  <div class="admin-container">
    <van-nav-bar title="管理员" />
    
    <van-tabs v-model:active="activeTab">
      <van-tab title="系统设置">
        <div class="settings-section">
          <van-cell-group inset style="margin: 12px;">
            <van-cell title="允许注册">
              <template #value>
                <van-switch v-model="settings.allow_registration" @change="onSettingsChange" />
              </template>
            </van-cell>
          </van-cell-group>
        </div>
      </van-tab>
      
      <van-tab title="用户管理">
        <van-loading v-if="loadingUsers" vertical>加载中...</van-loading>
        <div v-else>
          <van-empty v-if="users.length === 0" description="暂无用户" />
          <van-cell-group v-else inset style="margin: 12px;">
            <van-cell
              v-for="user in users"
              :key="user.id"
              :title="user.email"
              :label="`注册时间: ${formatLocalDateTime(user.created_at)} | 最后登录: ${formatLocalDateTime(user.last_login_at)}`"
            />
          </van-cell-group>
        </div>
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showToast } from 'vant'
import { adminApi } from '../api/admin'
import { extractErrorMessage } from '../utils/errorHandler'
import { formatLocalDateTime } from '../utils/date'

const activeTab = ref(0)
const loadingUsers = ref(false)
const settings = ref({
  allow_registration: true
})
const users = ref([])

const fetchSettings = async () => {
  try {
    settings.value = await adminApi.getSettings()
  } catch (error) {
    const message = extractErrorMessage(error)
    showToast.fail(message || '加载设置失败')
  }
}

const fetchUsers = async () => {
  loadingUsers.value = true
  try {
    users.value = await adminApi.getUsers()
  } catch (error) {
    const message = extractErrorMessage(error)
    showToast.fail(message || '加载用户失败')
  } finally {
    loadingUsers.value = false
  }
}

const onSettingsChange = async () => {
  try {
    await adminApi.updateSettings(settings.value)
    showToast.success('设置已更新')
  } catch (error) {
    const message = extractErrorMessage(error)
    showToast.fail(message || '更新设置失败')
    // 恢复原值
    await fetchSettings()
  }
}

onMounted(() => {
  fetchSettings()
  fetchUsers()
})
</script>

<style scoped>
.admin-container {
  min-height: 100vh;
  background: #f7f8fa;
  padding-bottom: 20px;
  width: 100%;
}

@media (min-width: 1024px) {
  .admin-container {
    max-width: 1200px;
    margin: 0 auto;
    padding-bottom: 40px;
  }
}

.settings-section {
  padding: 12px;
}

@media (min-width: 768px) {
  .settings-section {
    padding: 16px;
  }
}

@media (min-width: 1024px) {
  .settings-section {
    padding: 24px;
    max-width: 800px;
    margin: 0 auto;
  }
}
</style>

