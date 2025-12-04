<template>
  <div class="option-list">
    <div style="padding: 12px;">
      <van-button round block type="primary" icon="plus" @click="showAddForm = true">
        新增奖励选项
      </van-button>
    </div>
    <van-loading v-if="loading" vertical>加载中...</van-loading>
    <div v-else>
      <van-empty v-if="options.length === 0" description="暂无奖励选项，请添加" />
      <van-cell-group v-else inset style="margin: 12px;">
        <van-cell
          v-for="option in options"
          :key="option.id"
          :title="option.name"
          :label="`${option.cost_points} 积分`"
          is-link
          @click="editOption(option)"
        >
          <template #right-icon>
            <van-icon name="delete-o" @click.stop="handleDelete(option)" />
          </template>
        </van-cell>
      </van-cell-group>
    </div>
    <van-floating-bubble
      axis="xy"
      icon="plus"
      @click="showAddForm = true"
    />

    <!-- 表单弹窗 -->
    <van-popup v-model:show="showAddForm" position="bottom" :style="{ height: '80%' }">
      <van-nav-bar
        :title="editingOption ? '编辑奖励选项' : '新增奖励选项'"
        left-arrow
        @click-left="closeForm"
      />
      <RewardOptionForm
        v-if="showAddForm"
        :option="editingOption"
        @success="handleSuccess"
        @cancel="closeForm"
      />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showConfirmDialog, showSuccessToast, showFailToast } from 'vant'
import { scoresApi } from '../api/scores'
import { extractErrorMessage } from '../utils/errorHandler'
import RewardOptionForm from './RewardOptionForm.vue'

const emit = defineEmits(['close'])

const loading = ref(false)
const options = ref([])
const showAddForm = ref(false)
const editingOption = ref(null)

const fetchOptions = async () => {
  loading.value = true
  try {
    options.value = await scoresApi.getRewardOptions()
  } catch (error) {
    showFailToast('加载选项失败')
  } finally {
    loading.value = false
  }
}

const editOption = (option) => {
  editingOption.value = option
  showAddForm.value = true
}

const closeForm = () => {
  showAddForm.value = false
  editingOption.value = null
}

const handleSuccess = () => {
  closeForm()
  fetchOptions()
}

const handleDelete = async (option) => {
  try {
    await showConfirmDialog({
      title: '删除选项',
      message: `确定要删除 "${option.name}" 吗？`
    })
    await scoresApi.deleteRewardOption(option.id)
    showSuccessToast('删除成功')
    fetchOptions()
  } catch (error) {
    if (error !== 'cancel') {
      const message = extractErrorMessage(error)
      showFailToast(message)
    }
  }
}

onMounted(() => {
  fetchOptions()
})
</script>

<style scoped>
.option-list {
  height: 100%;
  background: #f7f8fa;
  padding-bottom: 50px;
  overflow-y: auto;
  position: relative;
}
</style>

