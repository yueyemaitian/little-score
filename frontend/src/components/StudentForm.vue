<template>
  <div class="student-form">
    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field
          v-model="form.name"
          name="name"
          label="姓名"
          placeholder="请输入姓名"
          :rules="nameRules"
        />
        <van-field
          :model-value="genderDisplayText"
          readonly
          label="性别"
          placeholder="选择性别"
          is-link
          required
          @click="showGenderPicker = true"
        />
        <van-field
          :model-value="stageDisplayText"
          readonly
          label="教育阶段"
          placeholder="选择阶段"
          is-link
          required
          @click="showStagePicker = true"
        />
        <van-field
          v-model="form.school"
          name="school"
          label="学校"
          placeholder="请输入学校"
          :rules="schoolRules"
        />
        <van-field
          v-model="form.enroll_date"
          readonly
          label="入学年月"
          placeholder="选择年月"
          is-link
          @click="showEnrollDatePicker = true"
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

    <!-- 性别选择器 -->
    <van-popup v-model:show="showGenderPicker" position="bottom">
      <van-picker
        :columns="genderColumns"
        :default-index="genderDefaultIndex"
        @confirm="onGenderConfirm"
        @cancel="showGenderPicker = false"
        @click-option="(params) => handlePickerDoubleClick(params, onGenderConfirm)"
      />
    </van-popup>

    <!-- 阶段选择器 -->
    <van-popup v-model:show="showStagePicker" position="bottom">
      <van-picker
        :columns="stageColumns"
        :default-index="stageDefaultIndex"
        @confirm="onStageConfirm"
        @cancel="showStagePicker = false"
        @click-option="(params) => handlePickerDoubleClick(params, onStageConfirm)"
      />
    </van-popup>

    <!-- 入学年月选择器 -->
    <van-popup v-model:show="showEnrollDatePicker" position="bottom" round>
      <van-date-picker
        v-model="currentEnrollDate"
        title="选择入学年月"
        type="year-month"
        :min-date="new Date(2000, 0, 1)"
        :max-date="new Date()"
        @confirm="onEnrollDateConfirm"
        @cancel="showEnrollDatePicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'
import { studentsApi } from '../api/students'
import { useEnumsStore } from '../stores/enums'
import { extractErrorMessage } from '../utils/errorHandler'

const props = defineProps({
  student: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['success', 'cancel'])

const loading = ref(false)
const form = ref({
  name: '',
  gender: null, // 初始值为 null，显示 placeholder
  stage: null, // 初始值为 null，显示 placeholder
  school: '',
  enroll_date: ''
})

const showGenderPicker = ref(false)
const showStagePicker = ref(false)
const showEnrollDatePicker = ref(false)

const enumsStore = useEnumsStore()

const currentEnrollDate = ref(['2020', '09'])

// 从 store 获取枚举值
const genderColumns = computed(() => enumsStore.gender)
const stageColumns = computed(() => enumsStore.educationStage)

// 默认索引（用于设置初始选中项）
const genderDefaultIndex = computed(() => {
  if (!form.value.gender) return 0
  const index = enumsStore.gender.findIndex(item => item.value === form.value.gender)
  return index >= 0 ? index : 0
})

const stageDefaultIndex = computed(() => {
  if (!form.value.stage) return 0
  const index = enumsStore.educationStage.findIndex(item => item.value === form.value.stage)
  return index >= 0 ? index : 0
})

// 显示文本（中文标签）
const genderDisplayText = computed(() => {
  if (!form.value.gender) return ''
  const option = enumsStore.gender.find(g => g.value === form.value.gender)
  return option ? option.text : ''
})

const stageDisplayText = computed(() => {
  if (!form.value.stage) return ''
  const option = enumsStore.educationStage.find(s => s.value === form.value.stage)
  return option ? option.text : ''
})

// 双击确认处理（Vant picker 默认支持双击，这里添加额外处理）
let lastClickTime = 0
let lastClickIndex = -1
const DOUBLE_CLICK_DELAY = 300 // 300ms 内的两次点击视为双击

const handlePickerDoubleClick = ({ currentOption, selectedIndex: idx }, confirmCallback) => {
  const now = Date.now()
  if (now - lastClickTime < DOUBLE_CLICK_DELAY && idx === lastClickIndex) {
    // 双击确认
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

// 姓名验证规则
const nameRules = [
  { required: true, message: '请填写姓名' },
  { validator: (val) => {
    if (!val || !val.trim()) {
      return '姓名不能为空'
    }
    if (val.trim().length > 64) {
      return '姓名长度不能超过64个字符'
    }
    return true
  }}
]

// 学校验证规则
const schoolRules = [
  { validator: (val) => {
    if (!val || !val.trim()) {
      return true // 学校是可选的
    }
    if (val.trim().length > 128) {
      return '学校名称长度不能超过128个字符'
    }
    return true
  }}
]

const onGenderConfirm = ({ selectedOptions }) => {
  form.value.gender = selectedOptions[0].value
  showGenderPicker.value = false
}

const onStageConfirm = ({ selectedOptions }) => {
  form.value.stage = selectedOptions[0].value
  showStagePicker.value = false
}

const onEnrollDateConfirm = ({ selectedValues }) => {
  // 只保存年月，格式：YYYY-MM
  form.value.enroll_date = selectedValues.join('-')
  showEnrollDatePicker.value = false
}

const onSubmit = async () => {
  // 前端验证
  if (!form.value.name || !form.value.name.trim()) {
    showFailToast('请填写姓名')
    return
  }
  if (form.value.name.trim().length > 64) {
    showFailToast('姓名长度不能超过64个字符')
    return
  }
  if (form.value.school && form.value.school.trim().length > 128) {
    showFailToast('学校名称长度不能超过128个字符')
    return
  }
  
  loading.value = true
  try {
    if (props.student) {
      await studentsApi.update(props.student.id, form.value)
    } else {
      await studentsApi.create(form.value)
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
  if (props.student) {
    form.value = {
      name: props.student.name,
      gender: props.student.gender,
      stage: props.student.stage,
      school: props.student.school || '',
      enroll_date: props.student.enroll_date || ''
    }
    if (props.student.enroll_date) {
      // 如果已有日期，提取年月部分（格式：YYYY-MM 或 YYYY-MM-DD）
      const dateParts = props.student.enroll_date.split('-')
      currentEnrollDate.value = [dateParts[0], dateParts[1]]
    }
  } else {
    // 新增学生时，设置默认值为第一个选项的值（如果枚举已加载）
    if (enumsStore.gender.length > 0) {
      form.value.gender = enumsStore.gender[0].value
    }
    if (enumsStore.educationStage.length > 0) {
      form.value.stage = enumsStore.educationStage[0].value
    }
  }
})
</script>

<style scoped>
.student-form {
  padding: 12px;
  max-height: calc(80vh - 46px);
  overflow-y: auto;
  width: 100%;
}

@media (min-width: 768px) {
  .student-form {
    padding: 16px;
  }
}

@media (min-width: 1024px) {
  .student-form {
    padding: 24px;
    max-width: 600px;
    margin: 0 auto;
    max-height: calc(90vh - 46px);
  }
}

/* 确保 picker 支持鼠标滚轮滚动 */
:deep(.van-picker-column) {
  cursor: pointer;
  touch-action: pan-y;
  -webkit-overflow-scrolling: touch;
}

:deep(.van-picker-column__wrapper) {
  touch-action: pan-y;
  -webkit-overflow-scrolling: touch;
}

/* 支持双击确认 */
:deep(.van-picker-column__item) {
  cursor: pointer;
  user-select: none;
}

/* 确保 popup 内容可以正常交互 */
:deep(.van-popup) {
  touch-action: pan-y;
}

:deep(.van-date-picker) {
  touch-action: pan-y;
}
</style>

