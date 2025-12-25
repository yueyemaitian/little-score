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
          v-model.number="form.reward_points"
          type="number"
          label="奖励积分"
          placeholder="输入或选择积分"
          is-link
          required
          @click-right-icon="showPointsPicker = true"
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

    <!-- 新增一级项目表单 -->
    <van-popup v-model:show="showAddProject1Form" position="bottom" :style="{ height: '60%' }">
      <van-nav-bar
        title="新增一级项目"
        left-arrow
        @click-left="showAddProject1Form = false"
      />
      <ProjectForm
        v-if="showAddProject1Form"
        :project="null"
        level="1"
        :prefilled-name="missingProject1Name"
        @success="handleProject1Success"
        @cancel="showAddProject1Form = false"
      />
    </van-popup>

    <!-- 新增二级项目表单 -->
    <van-popup v-model:show="showAddProject2Form" position="bottom" :style="{ height: '60%' }">
      <van-nav-bar
        title="新增二级项目"
        left-arrow
        @click-left="showAddProject2Form = false"
      />
      <ProjectForm
        v-if="showAddProject2Form"
        :project="null"
        level="2"
        :parent-id="form.project_level1_id"
        :prefilled-name="missingProject2Name"
        @success="handleProject2Success"
        @cancel="showAddProject2Form = false"
      />
    </van-popup>

    <!-- 新增惩罚选项表单 -->
    <van-popup v-model:show="showAddPunishmentForm" position="bottom" :style="{ height: '80%' }">
      <van-nav-bar
        title="新增惩罚选项"
        left-arrow
        @click-left="showAddPunishmentForm = false"
      />
      <PunishmentOptionForm
        v-if="showAddPunishmentForm"
        :option="null"
        :prefilled-name="missingPunishmentOptionName"
        @success="handlePunishmentSuccess"
        @cancel="showAddPunishmentForm = false"
      />
    </van-popup>

    <!-- 未匹配的一级项目提示对话框 -->
    <van-dialog
      v-model:show="showMissingProject1Prompt"
      title="创建一级项目"
      :message="`未找到一级项目「${missingProject1Name}」，是否创建？`"
      show-cancel-button
      confirm-button-text="创建"
      cancel-button-text="取消"
      @confirm="handleCreateMissingProject1"
      @cancel="missingProject1Name = null"
    />

    <!-- 未匹配的二级项目提示对话框 -->
    <van-dialog
      v-model:show="showMissingProject2Prompt"
      title="创建二级项目"
      :message="`未找到二级项目「${missingProject2Name}」，是否创建？`"
      show-cancel-button
      confirm-button-text="创建"
      cancel-button-text="取消"
      @confirm="handleCreateMissingProject2"
      @cancel="missingProject2Name = null"
    />

    <!-- 未匹配的惩罚选项提示对话框 -->
    <van-dialog
      v-model:show="showMissingPunishmentOptionPrompt"
      title="创建惩罚选项"
      :message="`未找到惩罚选项「${missingPunishmentOptionName}」，是否创建？`"
      show-cancel-button
      confirm-button-text="创建"
      cancel-button-text="取消"
      @confirm="handleCreateMissingPunishmentOption"
      @cancel="missingPunishmentOptionName = null"
    />

    <!-- 自定义分数输入对话框 -->
    <van-dialog
      v-model:show="showCustomPointsDialog"
      title="自定义分数"
      show-cancel-button
      confirm-button-text="确定"
      cancel-button-text="取消"
      @confirm="handleCustomPointsConfirm"
      @cancel="customPoints = ''"
    >
      <van-field
        v-model.number="customPoints"
        type="number"
        label="积分"
        placeholder="请输入积分"
        style="margin: 16px;"
      />
    </van-dialog>
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
import ProjectForm from './ProjectForm.vue'
import PunishmentOptionForm from './PunishmentOptionForm.vue'

const props = defineProps({
  task: {
    type: Object,
    default: null
  },
  studentId: {
    type: Number,
    required: true
  },
  prefill: {
    type: Object,
    default: null
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
const showAddProject1Form = ref(false)
const showAddProject2Form = ref(false)
const showAddPunishmentForm = ref(false)
const showCustomPointsDialog = ref(false)
const customPoints = ref('')

const enumsStore = useEnumsStore()

const project1Columns = computed(() => {
  const base = level1Projects.value.map(p => ({ text: p.name, value: p.id }))
  return [
    ...base,
    {
      text: '＋ 新增一级项目',
      value: 'add'
    }
  ]
})

const project2Columns = computed(() => {
  const base = level2Projects.value.map(p => ({ text: p.name, value: p.id }))
  return [
    ...base,
    {
      text: '＋ 新增二级项目',
      value: 'add'
    }
  ]
})

// 从 store 获取枚举值
const statusColumns = computed(() => enumsStore.taskStatus)
const ratingColumns = computed(() => enumsStore.taskRating)
const rewardTypeColumns = computed(() => enumsStore.rewardType)
const pointsColumns = computed(() => {
  const base = enumsStore.rewardPoints || []
  return [
    ...base,
    {
      text: '＋ 自定义分数',
      value: 'custom'
    }
  ]
})

const punishmentColumns = computed(() => {
  const base = punishmentOptions.value.map(p => ({ text: p.name, value: p.id }))
  return [
    ...base,
    {
      text: '＋ 新增惩罚选项',
      value: 'add'
    }
  ]
})

// 计算默认索引
const project1DefaultIndex = computed(() => {
  if (!form.value.project_level1_id) return 0
  const index = level1Projects.value.findIndex(p => p.id === form.value.project_level1_id)
  return index >= 0 ? index : 0
})

const project2DefaultIndex = computed(() => {
  if (!form.value.project_level2_id) return 0
  const index = level2Projects.value.findIndex(p => p.id === form.value.project_level2_id)
  return index >= 0 ? index : 0
})

const statusDefaultIndex = computed(() => {
  if (!form.value.status) return 0
  const index = enumsStore.taskStatus.findIndex(s => s.value === form.value.status)
  return index >= 0 ? index : 0
})

const ratingDefaultIndex = computed(() => {
  if (!form.value.rating) return 0
  const index = enumsStore.taskRating.findIndex(r => r.value === form.value.rating)
  return index >= 0 ? index : 0
})

const rewardTypeDefaultIndex = computed(() => {
  if (!form.value.reward_type) return 0
  const index = enumsStore.rewardType.findIndex(r => r.value === form.value.reward_type)
  return index >= 0 ? index : 0
})

const pointsDefaultIndex = computed(() => {
  if (!form.value.reward_points) return 0
  const index = enumsStore.rewardPoints.findIndex(p => p.value === form.value.reward_points)
  // 如果是自定义分数，默认选中"自定义分数"选项（最后一个）
  return index >= 0 ? index : (pointsColumns.value.length - 1)
})

const punishmentDefaultIndex = computed(() => {
  if (!form.value.punishment_option_id) return 0
  const index = punishmentOptions.value.findIndex(p => p.id === form.value.punishment_option_id)
  return index >= 0 ? index : 0
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
  return option ? option.text : `${form.value.reward_points}积分`
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
  const option = selectedOptions[0]
  if (option.value === 'add') {
    showProject1Picker.value = false
    showAddProject1Form.value = true
    return
  }
  
  const projectId = option.value
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
  const option = selectedOptions[0]
  if (option.value === 'add') {
    // 如果还没有选择一级项目，提示用户先选择
    if (!form.value.project_level1_id) {
      showFailToast('请先选择一级项目')
      showProject2Picker.value = false
      return
    }
    showProject2Picker.value = false
    showAddProject2Form.value = true
    return
  }
  
  form.value.project_level2_id = option.value
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
  const option = selectedOptions[0]
  if (option.value === 'custom') {
    // 打开自定义分数输入框
    showPointsPicker.value = false
    showCustomPointsDialog.value = true
  } else {
    form.value.reward_points = option.value
    showPointsPicker.value = false
  }
}

const onPunishmentConfirm = ({ selectedOptions }) => {
  const option = selectedOptions[0]
  if (option.value === 'add') {
    showPunishmentPicker.value = false
    showAddPunishmentForm.value = true
    return
  }
  
  form.value.punishment_option_id = option.value
  showPunishmentPicker.value = false
}

// 处理新增一级项目成功
const handleProject1Success = async () => {
  showAddProject1Form.value = false
  const createdProjectName = missingProject1Name.value
  missingProject1Name.value = null
  // 刷新一级项目列表
  await fetchProjects()
  // 自动选择刚创建的一级项目
  if (createdProjectName) {
    const newProject = level1Projects.value.find(p => p.name === createdProjectName)
    if (newProject) {
      form.value.project_level1_id = newProject.id
      // 加载二级项目
      const projects = await projectsApi.getList({ level: 2, parent_id: newProject.id })
      level2Projects.value = projects
      // 如果之前有未匹配的二级项目名称，现在一级项目已创建，可以创建二级项目了
      if (missingProject2Name.value) {
        showMissingProject2Prompt.value = true
        return
      }
    }
  }
  // 重新打开选择器
  showProject1Picker.value = true
}

// 处理新增二级项目成功
const handleProject2Success = async () => {
  showAddProject2Form.value = false
  const createdProjectName = missingProject2Name.value
  missingProject2Name.value = null
  // 刷新二级项目列表
  if (form.value.project_level1_id) {
    try {
      const projects = await projectsApi.getList({ level: 2, parent_id: form.value.project_level1_id })
      level2Projects.value = projects
      // 自动选择刚创建的二级项目
      if (createdProjectName) {
        const newProject = projects.find(p => p.name === createdProjectName)
        if (newProject) {
          form.value.project_level2_id = newProject.id
        }
      }
    } catch (error) {
      level2Projects.value = []
    }
  }
  // 重新打开选择器
  showProject2Picker.value = true
}

// 处理新增惩罚选项成功
const handlePunishmentSuccess = async () => {
  showAddPunishmentForm.value = false
  const createdOptionName = missingPunishmentOptionName.value
  missingPunishmentOptionName.value = null
  // 刷新惩罚选项列表
  await fetchPunishmentOptions()
  // 自动选择刚创建的惩罚选项
  if (createdOptionName) {
    const newOption = punishmentOptions.value.find(p => p.name === createdOptionName)
    if (newOption) {
      form.value.punishment_option_id = newOption.id
    }
  }
  // 重新打开选择器
  showPunishmentPicker.value = true
}

// 处理自定义分数确认
const handleCustomPointsConfirm = () => {
  const points = parseInt(customPoints.value)
  if (isNaN(points) || points <= 0) {
    showFailToast('请输入有效的积分（大于0的整数）')
    return
  }
  form.value.reward_points = points
  customPoints.value = ''
  showCustomPointsDialog.value = false
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
  // 确保枚举值已加载
  await enumsStore.fetchEnums()
  await fetchProjects()
  await fetchPunishmentOptions()
  
  if (props.task) {
    // 编辑现有任务
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
  } else if (props.prefill) {
    // 从语音助手预填数据
    const prefillData = props.prefill
    
    // 设置状态（通常是已完成）
    if (prefillData.status) {
      form.value.status = prefillData.status
    } else if (prefillData.rating) {
      // 如果有评分但没有状态，默认设置为已完成（因为评分通常意味着任务已完成）
      form.value.status = 'completed'
    }
    
    // 设置一级项目
    if (prefillData.project_level1_id) {
      form.value.project_level1_id = prefillData.project_level1_id
      // 加载二级项目
      const projects = await projectsApi.getList({ level: 2, parent_id: prefillData.project_level1_id })
      level2Projects.value = projects
      
      // 设置二级项目
      if (prefillData.project_level2_id) {
        form.value.project_level2_id = prefillData.project_level2_id
      } else if (prefillData.project_level2_name) {
        // 如果二级项目名称存在但没有ID，提示用户创建
        missingProject2Name.value = prefillData.project_level2_name
        showMissingProject2Prompt.value = true
      }
    } else if (prefillData.project_level1_name) {
      // 如果有一级项目名称但没有ID，提示用户创建
      missingProject1Name.value = prefillData.project_level1_name
      showMissingProject1Prompt.value = true
      // 如果同时有二级项目名称，保存起来，等一级项目创建后再处理
      if (prefillData.project_level2_name) {
        missingProject2Name.value = prefillData.project_level2_name
      }
    }
    
    // 设置评分（必须在设置status之后，因为评分字段的显示依赖于status）
    if (prefillData.rating) {
      form.value.rating = prefillData.rating
      // 如果有评分，确保状态是已完成（这样评分字段才会显示）
      if (!form.value.status || form.value.status !== 'completed') {
        form.value.status = 'completed'
      }
    }
    
    // 设置奖励类型和积分
    if (prefillData.reward_type) {
      form.value.reward_type = prefillData.reward_type
    }
    if (prefillData.reward_points) {
      form.value.reward_points = prefillData.reward_points
    }
    
    // 设置惩罚选项
    if (prefillData.punishment_option_id) {
      form.value.punishment_option_id = prefillData.punishment_option_id
    } else if (prefillData.punishment_option_name) {
      // 如果有惩罚选项名称但没有ID，提示用户创建
      missingPunishmentOptionName.value = prefillData.punishment_option_name
      showMissingPunishmentOptionPrompt.value = true
    }
  }
})

// 处理创建未匹配的一级项目
const handleCreateMissingProject1 = () => {
  showMissingProject1Prompt.value = false
  showAddProject1Form.value = true
}

// 处理创建未匹配的二级项目
const handleCreateMissingProject2 = () => {
  showMissingProject2Prompt.value = false
  if (!form.value.project_level1_id) {
    showFailToast('请先选择一级项目')
    return
  }
  showAddProject2Form.value = true
}

// 处理创建未匹配的惩罚选项
const handleCreateMissingPunishmentOption = () => {
  showMissingPunishmentOptionPrompt.value = false
  showAddPunishmentForm.value = true
}
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

