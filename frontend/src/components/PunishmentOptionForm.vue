<template>
  <div class="punishment-option-form">
    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field
          v-model="form.name"
          name="name"
          label="名称"
          placeholder="请输入惩罚名称"
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
        <van-cell center title="生成关联任务">
          <template #right-icon>
            <van-switch v-model="form.generate_related_task" />
          </template>
        </van-cell>
        
        <template v-if="form.generate_related_task">
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
        </template>
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

    <!-- 项目选择器 -->
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'
import { scoresApi } from '../api/scores'
import { projectsApi } from '../api/projects'
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
  generate_related_task: false,
  related_project_level1_id: null,
  related_project_level2_id: null
})

const level1Projects = ref([])
const level2Projects = ref([])
const showProject1Picker = ref(false)
const showProject2Picker = ref(false)

const project1Columns = computed(() => {
  return level1Projects.value.map(p => ({ text: p.name, value: p.id }))
})

const project2Columns = computed(() => {
  return level2Projects.value.map(p => ({ text: p.name, value: p.id }))
})

const project1DisplayText = computed(() => {
  if (!form.value.related_project_level1_id) return ''
  const option = level1Projects.value.find(p => p.id === form.value.related_project_level1_id)
  return option ? option.name : ''
})

const project2DisplayText = computed(() => {
  if (!form.value.related_project_level2_id) return ''
  const option = level2Projects.value.find(p => p.id === form.value.related_project_level2_id)
  return option ? option.name : ''
})

// 默认索引
const project1DefaultIndex = computed(() => {
  if (!form.value.related_project_level1_id) return 0
  const index = level1Projects.value.findIndex(p => p.id === form.value.related_project_level1_id)
  return index >= 0 ? index : 0
})

const project2DefaultIndex = computed(() => {
  if (!form.value.related_project_level2_id) return 0
  const index = level2Projects.value.findIndex(p => p.id === form.value.related_project_level2_id)
  return index >= 0 ? index : 0
})

// 双击确认处理
let lastClickTime = 0
let lastClickIndex = -1
const DOUBLE_CLICK_DELAY = 300

const handlePickerDoubleClick = ({ currentOption, selectedIndex }, confirmCallback) => {
  const now = Date.now()
  if (now - lastClickTime < DOUBLE_CLICK_DELAY && selectedIndex === lastClickIndex) {
    confirmCallback({ selectedOptions: [currentOption] })
    lastClickTime = 0
    lastClickIndex = -1
  } else {
    lastClickTime = now
    lastClickIndex = selectedIndex
  }
}

const fetchProjects = async () => {
  try {
    level1Projects.value = await projectsApi.getList({ level: 1 })
  } catch (error) {
    showFailToast('加载项目失败')
  }
}

const onProject1Confirm = async ({ selectedOptions }) => {
  const projectId = selectedOptions[0].value
  form.value.related_project_level1_id = projectId
  form.value.related_project_level2_id = null // 清空二级项目
  
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
  form.value.related_project_level2_id = selectedOptions[0].value
  showProject2Picker.value = false
}

const onSubmit = async () => {
  if (form.value.generate_related_task && !form.value.related_project_level1_id) {
    showFailToast('生成关联任务时必须选择一级项目')
    return
  }

  loading.value = true
  try {
    if (props.option) {
      await scoresApi.updatePunishmentOption(props.option.id, form.value)
    } else {
      await scoresApi.createPunishmentOption(form.value)
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

watch(() => form.value.related_project_level1_id, async (newVal) => {
  if (newVal && typeof newVal === 'number') {
    try {
      const projects = await projectsApi.getList({ level: 2, parent_id: newVal })
      level2Projects.value = projects
    } catch (error) {
      level2Projects.value = []
    }
  } else {
    level2Projects.value = []
  }
})

onMounted(async () => {
  await fetchProjects()
  if (props.option) {
    form.value = {
      name: props.option.name,
      description: props.option.description,
      generate_related_task: props.option.generate_related_task,
      related_project_level1_id: props.option.related_project_level1_id,
      related_project_level2_id: props.option.related_project_level2_id
    }
  }
})
</script>

<style scoped>
.punishment-option-form {
  padding: 12px;
  max-height: calc(80vh - 46px);
  overflow-y: auto;
  width: 100%;
}

@media (min-width: 1024px) {
  .punishment-option-form {
    padding: 24px;
    max-width: 600px;
    margin: 0 auto;
    max-height: calc(90vh - 46px);
  }
}

/* 确保 picker 支持鼠标滚轮滚动和双击确认 */
:deep(.van-picker-column) {
  cursor: pointer;
}

/* 支持双击确认 */
:deep(.van-picker-column__item) {
  cursor: pointer;
  user-select: none;
}
</style>

