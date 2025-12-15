<template>
  <div>
    <!-- 顶部 App 头部（点击可选择/新增孩子） -->
    <div class="home-header" @click="openStudentPicker">
      <div class="header-left">
        <div class="header-avatar">
          <span v-if="student" class="header-avatar-text">
            {{ (student.name || '').charAt(0) || '学' }}
          </span>
        </div>
        <div class="header-info" v-if="student">
          <div class="header-name">{{ student.name }}</div>
          <div class="header-meta">
            {{ student.school || '年级未设置' }} · Lv.1
          </div>
        </div>
      </div>
      <div class="header-right">
        <van-icon name="bell" class="header-icon" />
      </div>
    </div>

    <!-- 孩子下拉选择 / 新增 -->
    <van-popup v-model:show="showPicker" position="bottom" round>
      <van-picker
        title="选择孩子"
        :columns="studentColumns"
        @confirm="onConfirm"
        @cancel="showPicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  student: {
    type: Object,
    default: null
  },
  allStudents: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['switch', 'add'])
const router = useRouter()
const showPicker = ref(false)

// 孩子选择下拉选项：所有孩子 + “＋ 添加孩子”
const studentColumns = computed(() => {
  const base = props.allStudents.map((item) => ({
    text: item.name,
    value: item.id
  }))
  return [
    ...base,
    {
      text: '＋ 添加孩子',
      value: 'add'
    }
  ]
})

// 打开孩子选择下拉
const openStudentPicker = () => {
  if (!props.allStudents.length) {
    emit('add')
    return
  }
  showPicker.value = true
}

// 下拉确认选择
const onConfirm = ({ selectedOptions }) => {
  const option = selectedOptions?.[0]
  if (!option) {
    showPicker.value = false
    return
  }
  if (option.value === 'add') {
    showPicker.value = false
    emit('add')
    return
  }
  emit('switch', option.value)
  showPicker.value = false
}
</script>

<style scoped>
.home-header {
  padding: 10px 12px 6px;
  padding-top: calc(12px + env(safe-area-inset-top));
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-avatar {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background: linear-gradient(135deg, #ffcc80, #ffb74d);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 18px;
  font-weight: 600;
}

.header-avatar-text {
  transform: translateY(1px);
}

.header-info {
  display: flex;
  flex-direction: column;
}

.header-name {
  font-size: 17px;
  font-weight: 600;
  color: #111827;
}

.header-meta {
  margin-top: 2px;
  font-size: 12px;
  color: #9ca3af;
}

.header-right {
  display: flex;
  align-items: center;
}

.header-icon {
  font-size: 20px;
  color: #9ca3af;
}
</style>
