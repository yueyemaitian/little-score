<template>
  <div class="page-container home-container">
    <van-nav-bar title="学生积分管理" />
    
    <van-loading v-if="loading" vertical>加载中...</van-loading>
    
    <div v-else class="home-content">
      <van-empty v-if="students.length === 0" description="暂无学生数据" />
      <div v-else>
        <div
          class="student-card"
          v-for="studentDashboard in students"
          :key="studentDashboard.student.id"
        >
          <div class="student-header">
            <div class="student-name">{{ studentDashboard.student.name }}</div>
            <div class="student-meta">
              {{ studentDashboard.student.school || '学校未填写' }}
            </div>
          </div>

          <div class="student-section">
            <div class="section-title">积分汇总</div>
            <div class="summary-grid">
              <div class="summary-item">
                <div class="summary-label">可用积分</div>
                <div class="summary-value highlight">{{ studentDashboard.score_summary.available_points }}</div>
              </div>
              <div class="summary-item">
                <div class="summary-label">已兑换积分</div>
                <div class="summary-value">{{ studentDashboard.score_summary.exchanged_points }}</div>
              </div>
            </div>
          </div>

          <div class="student-section">
            <div class="section-title">最近 1 个月任务评分</div>
            <div v-if="studentDashboard.task_rating_summary.length === 0" class="empty-state compact">
              <van-empty description="暂无评分数据" />
            </div>
            <div v-else class="rating-list">
              <div
                class="rating-item"
                v-for="item in studentDashboard.task_rating_summary"
                :key="item.project_level1_id"
              >
                <div class="rating-project">{{ item.project_level1_name }}</div>
                <div class="rating-tags">
                  <van-tag
                    v-for="(count, rating) in item.ratings"
                    :key="rating"
                    type="primary"
                  >
                    {{ rating }}: {{ count }}
                  </van-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部导航 -->
    <BottomNav />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { showFailToast } from 'vant'
import { dashboardApi } from '../api/dashboard'
import { useStudentsStore } from '../stores/students'
import BottomNav from '../components/BottomNav.vue'

const studentsStore = useStudentsStore()

const loading = ref(true)
const dashboardData = ref(null)

const students = computed(() => {
  return dashboardData.value?.students || []
})

const fetchDashboard = async () => {
  loading.value = true
  try {
    const data = await dashboardApi.getDashboard()
    dashboardData.value = data
    if (data.students.length > 0) {
      studentsStore.setCurrentStudent(data.students[0].student.id)
    }
  } catch (error) {
    showFailToast('加载数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDashboard()
})
</script>

<style scoped>
.home-container {
  width: 100%;
}

.home-content {
  padding-bottom: 20px;
  width: 100%;
}

@media (min-width: 1024px) {
  .home-content {
    max-width: 1000px;
    margin: 0 auto;
  }
}

.student-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

@media (min-width: 768px) {
  .student-card {
    margin: 16px auto;
    padding: 20px;
    max-width: 720px;
  }
}

@media (min-width: 1024px) {
  .student-card {
    margin: 20px auto;
    padding: 24px;
    max-width: 800px;
  }
}

.student-header {
  border-bottom: 1px solid #f1f2f5;
  padding-bottom: 12px;
  margin-bottom: 12px;
}

.student-name {
  font-size: 18px;
  font-weight: 600;
  color: #111;
}

.student-meta {
  margin-top: 4px;
  font-size: 14px;
  color: #909399;
}

.student-section + .student-section {
  margin-top: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #323233;
  margin-bottom: 8px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.summary-item {
  background: #f7f8fa;
  border-radius: 8px;
  padding: 12px;
}

.summary-label {
  font-size: 13px;
  color: #646566;
}

.summary-value {
  margin-top: 6px;
  font-size: 20px;
  font-weight: 600;
  color: #323233;
}

.summary-value.highlight {
  color: #1989fa;
}

.rating-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rating-item {
  border: 1px solid #f1f2f5;
  border-radius: 8px;
  padding: 10px 12px;
}

.rating-project {
  font-size: 14px;
  font-weight: 500;
  color: #323233;
}

.rating-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.empty-state {
  padding: 12px 0;
}

.empty-state.compact :deep(.van-empty) {
  padding: 0;
}
</style>


