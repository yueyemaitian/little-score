<template>
  <div class="task-form">
    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field
          :model-value="project1DisplayText"
          readonly
          label="一级项目"
          placeholder="选择一级项目"
          is-link
          required
          @click="showProject1Picker = true"
        />
        <van-field
          :model-value="project2DisplayText"
          readonly
          label="二级项目"
          placeholder="选择二级项目（可选）"
          is-link
          @click="showProject2Picker = true"
        />
        <van-field
          :model-value="statusDisplayText"
          readonly
          label="状态"
          placeholder="选择状态"
          is-link
          required
          @click="showStatusPicker = true"
        />
        <van-field
          v-if="isCompletedStatus"
          :model-value="ratingDisplayText"
          readonly
          label="评分"
          placeholder="选择评分"
          is-link
          required
          @click="showRatingPicker = true"
        />
        <van-field
          v-if="isCompletedStatus"
          :model-value="rewardTypeDisplayText"
          readonly
          label="惩奖类型"
          placeholder="选择惩奖类型"
          is-link
          required
          @click="showRewardTypePicker = true"
        />
        <van-field
          v-if="isCompletedStatus && form.reward_type === 'reward'"
          :model-value="rewardPointsDisplayText"
          readonly
          label="奖励积分"
          placeholder="选择积分"
          is-link
          required
          @click="showPointsPicker = true"
        />
        <van-field
          v-if="isCompletedStatus && form.reward_type === 'punish'"
          :model-value="punishmentDisplayText"
          readonly
          label="惩罚选项"
          placeholder="选择惩罚选项"
          is-link
          required
          @click="showPunishmentPicker = true"
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

    <!-- 选择器 -->
    <van-popup v-model:show="showProject1Picker" position="bottom">
      <van-picker
        :columns="project1Columns"
        :default-index="project1DefaultIndex"
        @confirm="onProject1Confirm"
        @cancel="showProject1Picker = false"
        @click-option="(params) => handlePickerDoubleClick(params, onProject1Confirm)"
      />
    </van-popup>

    <van-popup v-model:show="showProject2Picker" position="bottom">
      <van-picker
        :columns="project2Columns"
        :default-index="project2DefaultIndex"
        @confirm="onProject2Confirm"
        @cancel="showProject2Picker = false"
        @click-option="(params) => handlePickerDoubleClick(params, onProject2Confirm)"
      />
    </van-popup>

    <van-popup v-model:show="showStatusPicker" position="bottom">
      <van-picker
        :columns="statusColumns"
        :default-index="statusDefaultIndex"
        @confirm="onStatusConfirm"
        @cancel="showStatusPicker = false"
        @click-option="(params) => handlePickerDoubleClick(params, onStatusConfirm)"
      />
    </van-popup>

    <van-popup v-model:show="showRatingPicker" position="bottom">
      <van-picker
        :columns="ratingColumns"
        :default-index="ratingDefaultIndex"
        @confirm="onRatingConfirm"
        @cancel="showRatingPicker = false"
        @click-option="(params) => handlePickerDoubleClick(params, onRatingConfirm)"
      />
    </van-popup>

    <van-popup v-model:show="showRewardTypePicker" position="bottom">
      <van-picker
        :columns="rewardTypeColumns"
        :default-index="rewardTypeDefaultIndex"
        @confirm="onRewardTypeConfirm"
        @cancel="showRewardTypePicker = false"
        @click-option="(params) => handlePickerDoubleClick(params, onRewardTypeConfirm)"
      />
    </van-popup>

    <van-popup v-model:show="showPointsPicker" position="bottom">
      <van-picker
        :columns="pointsColumns"
        :default-index="pointsDefaultIndex"
        @confirm="onPointsConfirm"
        @cancel="showPointsPicker = false"
        @click-option="(params) => handlePickerDoubleClick(params, onPointsConfirm)"
      />
    </van-popup>

    <van-popup v-model:show="showPunishmentPicker" position="bottom">
      <van-picker
        :columns="punishmentColumns"
        :default-index="punishmentDefaultIndex"
        @confirm="onPunishmentConfirm"
        @cancel="showPunishmentPicker = false"
        @click-option="(params) => handlePickerDoubleClick(params, onPunishmentConfirm)"
      />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'
import { tasksApi } from '../api/tasks'
import { projectsApi } from '../api/projects'
import { scoresApi } from '../api/scores'
import { useEnumsStore } from '../stores/enums'
import { extractErrorMessage } from '../utils/errorHandler'

const props = defineProps({
  task: {
    type: Object,
    default: null
  },
  studentId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['success', 'cancel'])

const loading = ref(false)
const form = ref({
  project_level1_id: null,
  project_level2_id: null,
  status: 'not_started',
  rating: null,
  reward_type: 'none',
  reward_points: null,
  punishment_option_id: null
})

const level1Projects = ref([])
const level2Projects = ref([])
const punishmentOptions = ref([])

const showProject1Picker = ref(false)
const showProject2Picker = ref(false)
const showStatusPicker = ref(false)
const showRatingPicker = ref(false)
const showRewardTypePicker = ref(false)
const showPointsPicker = ref(false)
const showPunishmentPicker = ref(false)

const enumsStore = useEnumsStore()

const project1Columns = computed(() => {
  return level1Projects.value.map(p => ({ text: p.name, value: p.id }))
})

const project2Columns = computed(() => {
  return level2Projects.value.map(p => ({ text: p.name, value: p.id }))
})

// 从 store 获取枚举值
const statusColumns = computed(() => enumsStore.taskStatus)
const ratingColumns = computed(() => enumsStore.taskRating)
const rewardTypeColumns = computed(() => enumsStore.rewardType)
const pointsColumns = computed(() => enumsStore.rewardPoints)

const punishmentColumns = computed(() => {
  return punishmentOptions.value.map(p => ({ text: p.name, value: p.id }))
})

// Picker 双击确认支持
let lastClickTime = 0
let lastClickIndex = -1
const DOUBLE_CLICK_DELAY = 300

const handlePickerDoubleClick = ({ currentOption, selectedIndex: idx }, confirmCallback) => {
  const now = Date.now()
  if (now - lastClickTime < DOUBLE_CLICK_DELAY && idx === lastClickIndex) {
    if (confirmCallback) {
      confirmCallback({ selectedOptions: [currentOption] })
    }
    lastClickTime = 0
    lastClickIndex = -1
  } else {
    lastClickTime = now
    lastClickIndex = idx
  }
}

// 判断是否为已完成状态
const isCompletedStatus = computed(() => {
  // 直接比较状态值，更加稳健
  return form.value.status === 'completed'
})

// 显示文本（中文标签）
const statusDisplayText = computed(() => {
  if (!form.value.status) return ''
  const option = enumsStore.taskStatus.find(s => s.value === form.value.status)
  return option ? option.text : form.value.status
})

const ratingDisplayText = computed(() => {
  if (!form.value.rating) return ''
  const option = enumsStore.taskRating.find(r => r.value === form.value.rating)
  return option ? option.text : form.value.rating
})

const rewardTypeDisplayText = computed(() => {
  if (!form.value.reward_type) return ''
  const option = enumsStore.rewardType.find(r => r.value === form.value.reward_type)
  return option ? option.text : form.value.reward_type
})

const rewardPointsDisplayText = computed(() => {
  if (!form.value.reward_points) return ''
  const option = enumsStore.rewardPoints.find(p => p.value === form.value.reward_points)
  return option ? option.text : ''
})

const punishmentDisplayText = computed(() => {
  if (!form.value.punishment_option_id) return ''
  const option = punishmentOptions.value.find(p => p.id === form.value.punishment_option_id)
  return option ? option.name : ''
})

const project1DisplayText = computed(() => {
  if (!form.value.project_level1_id) return ''
  const option = level1Projects.value.find(p => p.id === form.value.project_level1_id)
  return option ? option.name : ''
})

const project2DisplayText = computed(() => {
  if (!form.value.project_level2_id) return ''
  const option = level2Projects.value.find(p => p.id === form.value.project_level2_id)
  return option ? option.name : ''
})

const fetchProjects = async () => {
  try {
    const projects = await projectsApi.getList({ level: 1 })
    level1Projects.value = projects
  } catch (error) {
    showFailToast('加载项目失败')
  }
}

const fetchPunishmentOptions = async () => {
  try {
    const options = await scoresApi.getPunishmentOptions()
    punishmentOptions.value = options
  } catch (error) {
    showFailToast('加载惩罚选项失败')
  }
}

const onProject1Confirm = async ({ selectedOptions }) => {
  const projectId = selectedOptions[0].value
  form.value.project_level1_id = projectId
  
  // 获取二级项目
  try {
    const projects = await projectsApi.getList({ level: 2, parent_id: projectId })
    level2Projects.value = projects
  } catch (error) {
    level2Projects.value = []
  }
  
  showProject1Picker.value = false
}

const onProject2Confirm = ({ selectedOptions }) => {
  form.value.project_level2_id = selectedOptions[0].value
  showProject2Picker.value = false
}

const onStatusConfirm = ({ selectedOptions }) => {
  form.value.status = selectedOptions[0].value
  // 如果状态不是已完成，清空评分和奖惩相关字段
  if (form.value.status !== 'completed') {
    form.value.rating = null
    form.value.reward_type = 'none'
    form.value.reward_points = null
    form.value.punishment_option_id = null
  }
  showStatusPicker.value = false
}

const onRatingConfirm = ({ selectedOptions }) => {
  form.value.rating = selectedOptions[0].value
  showRatingPicker.value = false
}

const onRewardTypeConfirm = ({ selectedOptions }) => {
  form.value.reward_type = selectedOptions[0].value
  const rewardType = enumsStore.rewardType.find(r => r.value === 'reward')
  const punishType = enumsStore.rewardType.find(r => r.value === 'punish')
  
  if (rewardType && form.value.reward_type !== rewardType.value) {
    form.value.reward_points = null
  }
  if (punishType && form.value.reward_type !== punishType.value) {
    form.value.punishment_option_id = null
  }
  showRewardTypePicker.value = false
}

const onPointsConfirm = ({ selectedOptions }) => {
  form.value.reward_points = selectedOptions[0].value
  showPointsPicker.value = false
}

const onPunishmentConfirm = ({ selectedOptions }) => {
  form.value.punishment_option_id = selectedOptions[0].value
  showPunishmentPicker.value = false
}

const onSubmit = async () => {
  // 前端验证
  if (!form.value.project_level1_id) {
    showFailToast('请选择一级项目')
    return
  }
  
  // 检查已完成状态是否需要评分
  if (form.value.status === 'completed' && !form.value.rating) {
    showFailToast('已完成的任务必须提供评分')
    return
  }
  
  // 检查奖励类型逻辑
  if (form.value.reward_type === 'reward' && !form.value.reward_points) {
    showFailToast('奖励类型必须提供奖励积分')
    return
  }
  
  if (form.value.reward_type === 'punish' && !form.value.punishment_option_id) {
    showFailToast('惩罚类型必须提供惩罚选项')
    return
  }
  
  if (form.value.reward_type === 'none') {
    if (form.value.reward_points) {
      showFailToast('无惩奖类型不应有奖励积分')
      return
    }
    if (form.value.punishment_option_id) {
      showFailToast('无惩奖类型不应有惩罚选项')
      return
    }
  }

  loading.value = true
  try {
    const data = {
      student_id: props.studentId,
      project_level1_id: form.value.project_level1_id,
      project_level2_id: form.value.project_level2_id,
      status: form.value.status,
      rating: (form.value.status === 'completed') ? form.value.rating : null,
      reward_type: form.value.reward_type,
      reward_points: (form.value.reward_type === 'reward') 
        ? form.value.reward_points : null,
      punishment_option_id: (form.value.reward_type === 'punish')
        ? form.value.punishment_option_id : null
    }

    if (props.task) {
      await tasksApi.update(props.task.id, { student_id: props.studentId }, data)
    } else {
      await tasksApi.create(data)
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

watch(() => form.value.project_level1_id, async (newVal) => {
  if (newVal && typeof newVal === 'number') {
    try {
      const projects = await projectsApi.getList({ level: 2, parent_id: newVal })
      level2Projects.value = projects
    } catch (error) {
      level2Projects.value = []
    }
  }
})

onMounted(async () => {
  await fetchProjects()
  await fetchPunishmentOptions()
  
  if (props.task) {
    form.value = {
      project_level1_id: props.task.project_level1_id,
      project_level2_id: props.task.project_level2_id,
      status: props.task.status,
      rating: props.task.rating,
      reward_type: props.task.reward_type,
      reward_points: props.task.reward_points,
      punishment_option_id: props.task.punishment_option_id
    }
    
    if (props.task.project_level1_id) {
      const projects = await projectsApi.getList({ level: 2, parent_id: props.task.project_level1_id })
      level2Projects.value = projects
    }
  }
})
</script>

<style scoped>
.task-form {
  padding: 12px;
  max-height: calc(80vh - 46px);
  overflow-y: auto;
  width: 100%;
}

@media (min-width: 768px) {
  .task-form {
    padding: 16px;
  }
}

@media (min-width: 1024px) {
  .task-form {
    padding: 24px;
    max-width: 700px;
    margin: 0 auto;
    max-height: calc(90vh - 46px);
  }
}

/* 确保 picker 支持鼠标滚轮滚动和双击确认 */
:deep(.van-picker-column) {
  touch-action: pan-y;
  -webkit-overflow-scrolling: touch;
  cursor: pointer;
}

:deep(.van-picker-column__wrapper) {
  overflow-y: auto;
  scrollbar-width: none;
}

:deep(.van-picker-column__wrapper::-webkit-scrollbar) {
  display: none;
}

/* 支持双击确认 */
:deep(.van-picker-column__item) {
  cursor: pointer;
  user-select: none;
}
</style>

