<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAdminReports, handleReport } from '@/api/admin'
import { confirmDialog } from '@/composables/useConfirm'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ status: 0, target_type: '', page: 1, size: 10 })

const statusText = (v) => (v === 2 ? '已隐藏' : v === 1 ? '已忽略' : '待处理')
const statusType = (v) => (v === 2 ? 'danger' : v === 1 ? 'info' : 'warning')

function formatTime(value) {
  return (value || '').replace('T', ' ').slice(0, 16)
}

function rowClass({ row }) {
  return row.status === 0 ? 'row-pending' : ''
}

async function load() {
  loading.value = true
  try {
    const params = { page: query.page, size: query.size }
    if (query.status !== null && query.status !== '') params.status = query.status
    if (query.target_type) params.target_type = query.target_type
    const data = await getAdminReports(params)
    list.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function search() {
  query.page = 1
  load()
}

async function act(row, action) {
  const isHide = action === 'hide'
  const ok = await confirmDialog({
    title: isHide ? '隐藏这条内容？' : '忽略这条举报？',
    message: isHide
      ? `将隐藏被举报的${row.target_type_label}，并把同一目标的所有待处理举报一并结案。隐藏后前台不可见。`
      : '忽略后该内容保持不变，举报标记为已忽略。',
    confirmText: isHide ? '隐藏并处理' : '忽略',
    danger: isHide
  })
  if (!ok) return
  try {
    await handleReport(row.id, action)
    ElMessage.success(isHide ? '已隐藏并结案' : '已忽略')
    await load()
  } catch {
    /* 拦截器已提示 */
  }
}

onMounted(load)
</script>

<template>
  <el-card shadow="never" class="panel">
    <div class="bar">
      <el-select v-model="query.status" placeholder="全部状态" clearable style="width: 130px">
        <el-option label="待处理" :value="0" />
        <el-option label="已忽略" :value="1" />
        <el-option label="已隐藏" :value="2" />
      </el-select>
      <el-select v-model="query.target_type" placeholder="全部类型" clearable style="width: 130px">
        <el-option label="书评" value="book_comment" />
        <el-option label="间贴" value="paragraph_comment" />
      </el-select>
      <el-button type="primary" @click="search">查询</el-button>
      <span class="bar__tip">隐藏内容会同时结案同一目标下的所有待处理举报</span>
    </div>

    <el-table v-loading="loading" :data="list" border stripe :row-class-name="rowClass">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="类型" width="80">
        <template #default="{ row }">
          <el-tag size="small" :type="row.target_type === 'book_comment' ? 'info' : 'primary'">
            {{ row.target_type_label }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="被举报内容" min-width="240">
        <template #default="{ row }">
          <div class="cell__content">{{ row.target.content }}</div>
          <div class="cell__sub">
            《{{ row.target.book_title }}》
            <template v-if="row.target.chapter_title"> · {{ row.target.chapter_title }}</template>
            <template v-if="row.target.paragraph_index !== null">
              · 第 {{ row.target.paragraph_index + 1 }} 段
            </template>
            <span v-if="row.target.status === 0" class="cell__hidden">（内容已隐藏）</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="举报理由" width="150">
        <template #default="{ row }">
          <div>{{ row.reason }}</div>
          <div v-if="row.detail" class="cell__sub">{{ row.detail }}</div>
        </template>
      </el-table-column>
      <el-table-column label="举报人" width="110">
        <template #default="{ row }">{{ row.reporter.nickname }}</template>
      </el-table-column>
      <el-table-column label="时间" width="150">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 0">
            <el-button link type="danger" @click="act(row, 'hide')">隐藏并处理</el-button>
            <el-button link @click="act(row, 'ignore')">忽略</el-button>
          </template>
          <span v-else class="cell__done">{{ formatTime(row.handled_at) }}</span>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="pager"
      layout="total, prev, pager, next"
      :total="total"
      :page-size="query.size"
      :current-page="query.page"
      @current-change="(p) => { query.page = p; load() }"
    />
  </el-card>
</template>

<style scoped>
.panel {
  border: 1px solid #e8e3da;
  border-radius: 8px;
}

.bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.bar__tip {
  margin-left: auto;
  font-size: 12px;
  color: #a8a39a;
}

.pager {
  margin-top: 16px;
  justify-content: flex-end;
}

.cell__content {
  font-size: 13px;
  color: #2b2b2b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell__sub {
  font-size: 12px;
  color: #a8a39a;
}

.cell__hidden {
  color: #e34d59;
}

.cell__done {
  font-size: 12px;
  color: #b0b0b0;
}

:deep(.row-pending) {
  --el-table-tr-bg-color: #fffbf0;
}
</style>
