<template>
  <div class="reward-option-form">
    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field
          v-model="form.name"
          name="name"
          label="名称"
          placeholder="请输入奖励名称"
          :rules="[{ required: true, message: '请填写名称' }]"
        />
        <van-field
          v-model="form.description"
          name="description"
          label="描述"
          placeholder="请输入描述（可选）"
          type="textarea"
          rows="2"
        />
        <van-field
          v-model.number="form.cost_points"
          name="cost_points"
          label="所需积分"
          placeholder="请输入所需积分"
          type="digit"
          :rules="[{ required: true, message: '请填写所需积分' }]"
        />
      </van-cell-group>
      
      <div style="margin: 16px;">
        <van-button round block type="primary" native-type="submit" :loading="loading">
          保存
        </van-button>
        <van-button round block style="margin-top: 12px;" @click="$emit('cancel')">
          取消
        </van-button>
      </div>
    </van-form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'
import { scoresApi } from '../api/scores'
import { extractErrorMessage } from '../utils/errorHandler'

const props = defineProps({
  option: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['success', 'cancel'])

const loading = ref(false)
const form = ref({
  name: '',
  description: '',
  cost_points: null
})

const onSubmit = async () => {
  loading.value = true
  try {
    if (props.option) {
      await scoresApi.updateRewardOption(props.option.id, form.value)
    } else {
      await scoresApi.createRewardOption(form.value)
    }
    showSuccessToast('保存成功')
    emit('success')
  } catch (error) {
    const message = extractErrorMessage(error)
    showFailToast(message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (props.option) {
    form.value = {
      name: props.option.name,
      description: props.option.description,
      cost_points: props.option.cost_points
    }
  }
})
</script>

<style scoped>
.reward-option-form {
  padding: 12px;
  width: 100%;
}

@media (min-width: 768px) {
  .reward-option-form {
    padding: 16px;
  }
}

@media (min-width: 1024px) {
  .reward-option-form {
    padding: 24px;
    max-width: 600px;
    margin: 0 auto;
  }
}
</style>

