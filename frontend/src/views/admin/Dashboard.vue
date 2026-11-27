<script setup>
import { onMounted, ref } from 'vue'
import { getStats } from '@/api/admin'

const loading = ref(true)
const stats = ref({})

const cards = [
  { key: 'book_count', label: '书籍总数', color: 'var(--c-primary)' },
  { key: 'chapter_count', label: '章节总数', color: '#d93e73' },
  { key: 'user_count', label: '用户总数', color: '#3f8f5b' },
  { key: 'comment_count', label: '评论总数', color: '#d48806' }
]

const todayCards = [
  { key: 'today_new_books', label: '今日新增书籍' },
  { key: 'today_new_chapters', label: '今日新增章节' },
  { key: 'today_new_users', label: '今日新增用户' },
  { key: 'today_new_comments', label: '今日新增评论' }
]

onMounted(async () => {
  try {
    stats.value = await getStats()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-loading="loading">
    <el-row :gutter="16">
      <el-col v-for="card in cards" :key="card.key" :xs="12" :sm="12" :md="6">
        <el-card shadow="never" class="stat">
          <p class="stat__label">{{ card.label }}</p>
          <p class="stat__value" :style="{ color: card.color }">
            {{ stats[card.key] ?? '—' }}
          </p>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="panel">
      <template #header>
        <span class="panel__title">今日数据</span>
      </template>
      <div class="today">
        <div v-for="item in todayCards" :key="item.key" class="today__item">
          <span class="today__label">{{ item.label }}</span>
          <span class="today__value">{{ stats[item.key] ?? 0 }}</span>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="panel">
      <template #header>
        <span class="panel__title">分类分布</span>
      </template>
      <p class="tip">分类总数：{{ stats.category_count ?? '—' }}</p>
    </el-card>
  </div>
</template>

<style scoped>
.stat {
  border: 1px solid #e8e3da;
  border-radius: 8px;
}

.stat__label {
  margin: 0 0 8px;
  font-size: 13px;
  color: #7a7a7a;
}

.stat__value {
  margin: 0;
  font-size: 30px;
  font-weight: 600;
  line-height: 1.2;
}

.panel {
  margin-top: 16px;
  border: 1px solid #e8e3da;
  border-radius: 8px;
}

.panel__title {
  font-size: 14px;
  font-weight: 600;
  color: #2b2b2b;
}

.today {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.today__item {
  padding: 12px 16px;
  background: #faf8f4;
  border-radius: 6px;
}

.today__label {
  display: block;
  font-size: 12px;
  color: #7a7a7a;
}

.today__value {
  display: block;
  margin-top: 4px;
  font-size: 20px;
  font-weight: 600;
  color: var(--c-primary);
}

.tip {
  margin: 0;
  font-size: 13px;
  color: #7a7a7a;
}
</style>