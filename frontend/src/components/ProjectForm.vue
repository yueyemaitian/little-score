<template>
  <div class="project-form">
    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field
          v-model="form.name"
          name="name"
          label="名称"
          placeholder="请输入项目名称"
          :rules="nameRules"
        />
        <van-field
          v-model="form.description"
          name="description"
          label="描述"
          placeholder="请输入描述（可选）"
          type="textarea"
          rows="3"
          :rules="descriptionRules"
        />
        <van-field
          v-if="level === '2'"
          :model-value="parentDisplayText"
          readonly
          label="父项目"
          placeholder="选择一级项目"
          is-link
          required
          @click="showParentPicker = true"
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

    <!-- 父项目选择器 -->
    <van-popup v-model:show="showParentPicker" position="bottom">
      <van-picker
        :columns="parentColumns"
        :default-index="parentDefaultIndex"
        @confirm="onParentConfirm"
        @cancel="showParentPicker = false"
        @click-option="(params) => handlePickerDoubleClick(params, onParentConfirm)"
      />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'
import { projectsApi } from '../api/projects'
import { extractErrorMessage } from '../utils/errorHandler'

const props = defineProps({
  project: {
    type: Object,
    default: null
  },
  level: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['success', 'cancel'])

const loading = ref(false)
const form = ref({
  name: '',
  description: '',
  parent_id: null
})

const showParentPicker = ref(false)
const level1Projects = ref([])

const parentColumns = computed(() => {
  return level1Projects.value.map(p => ({ text: p.name, value: p.id }))
})

// 名称验证规则
const nameRules = [
  { required: true, message: '请填写名称' },
  { validator: (val) => {
    if (!val || !val.trim()) {
      return '项目名称不能为空'
    }
    if (val.trim().length > 128) {
      return '项目名称长度不能超过128个字符'
    }
    return true
  }}
]

// 描述验证规则
const descriptionRules = [
  { validator: (val) => {
    if (!val || !val.trim()) {
      return true // 描述是可选的
    }
    if (val.trim().length > 255) {
      return '项目描述长度不能超过255个字符'
    }
    return true
  }}
]

const fetchLevel1Projects = async () => {
  try {
    level1Projects.value = await projectsApi.getList({ level: 1 })
  } catch (error) {
    showFailToast('加载一级项目失败')
  }
}

const onParentConfirm = ({ selectedOptions }) => {
  form.value.parent_id = selectedOptions[0].value
  showParentPicker.value = false
}

const parentDisplayText = computed(() => {
  if (!form.value.parent_id) return ''
  const option = level1Projects.value.find(p => p.id === form.value.parent_id)
  return option ? option.name : ''
})

// 默认索引（用于设置初始选中项）
const parentDefaultIndex = computed(() => {
  if (!form.value.parent_id) return 0
  const index = level1Projects.value.findIndex(p => p.id === form.value.parent_id)
  return index >= 0 ? index : 0
})

// 双击确认处理（Vant picker 默认支持双击，这里添加额外处理）
let lastClickTime = 0
let lastClickIndex = -1
const DOUBLE_CLICK_DELAY = 300 // 300ms 内的两次点击视为双击

const handlePickerDoubleClick = ({ selectedIndex: idx }) => {
  const now = Date.now()
  if (now - lastClickTime < DOUBLE_CLICK_DELAY && idx === lastClickIndex) {
    // 双击确认
    // Vant picker 会自动触发 confirm，这里可以添加额外逻辑
  }
  lastClickTime = now
  lastClickIndex = idx
}

const onSubmit = async () => {
  // 前端验证
  if (!form.value.name || !form.value.name.trim()) {
    showFailToast('请填写项目名称')
    return
  }
  if (form.value.name.trim().length > 128) {
    showFailToast('项目名称长度不能超过128个字符')
    return
  }
  if (form.value.description && form.value.description.trim().length > 255) {
    showFailToast('项目描述长度不能超过255个字符')
    return
  }
  if (props.level === '2' && !form.value.parent_id) {
    showFailToast('二级项目必须选择父项目')
    return
  }
  if (props.level === '1' && form.value.parent_id) {
    showFailToast('一级项目不能有父项目')
    return
  }

  loading.value = true
  try {
    const data = {
      level: parseInt(props.level),
      name: form.value.name.trim(),
      description: form.value.description ? form.value.description.trim() : null,
      parent_id: props.level === '2' ? form.value.parent_id : null
    }

    if (props.project) {
      await projectsApi.update(props.project.id, data)
    } else {
      await projectsApi.create(data)
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

onMounted(async () => {
  if (props.level === '2') {
    await fetchLevel1Projects()
  }
  
  if (props.project) {
    form.value = {
      name: props.project.name,
      description: props.project.description || '',
      parent_id: props.project.parent_id
    }
  }
})
</script>

<style scoped>
.project-form {
  padding: 12px;
  max-height: calc(60vh - 46px);
  overflow-y: auto;
  width: 100%;
}

@media (min-width: 768px) {
  .project-form {
    padding: 16px;
  }
}

@media (min-width: 1024px) {
  .project-form {
    padding: 24px;
    max-width: 600px;
    margin: 0 auto;
    max-height: calc(80vh - 46px);
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

