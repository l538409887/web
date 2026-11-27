<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAdminComments, updateCommentStatus } from '@/api/admin'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ status: null, page: 1, size: 10 })

const statusText = (value) => {
  if (value === 0) return '待审核'
  if (value === 2) return '已隐藏'
  return '显示中'
}
const statusType = (value) => {
  if (value === 0) return 'warning'
  if (value === 2) return 'info'
  return 'success'
}

async function load() {
  loading.value = true
  try {
    const params = { page: query.page, size: query.size }
    if (query.status !== null) params.status = query.status
    const data = await getAdminComments(params)
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

async function setStatus(row, status) {
  try {
    await updateCommentStatus(row.id, status)
    row.status = status
    ElMessage.success(status === 1 ? '已恢复显示' : '已隐藏')
  } catch {
    /* 拦截器已提示 */
  }
}

onMounted(load)
</script>

<template>
  <el-card shadow="never" class="panel">
    <div class="bar">
      <el-select v-model="query.status" placeholder="全部状态" clearable style="width: 150px">
        <el-option label="显示中" :value="1" />
        <el-option label="待审核" :value="0" />
        <el-option label="已隐藏" :value="2" />
      </el-select>
      <el-button type="primary" @click="search">查询</el-button>
    </div>

    <el-table v-loading="loading" :data="list" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="所属" min-width="180">
        <template #default="{ row }">
          <div class="cell__book">{{ row.book_title }}</div>
          <div v-if="row.chapter_title" class="cell__chapter">{{ row.chapter_title }}</div>
        </template>
      </el-table-column>
      <el-table-column label="用户" width="120">
        <template #default="{ row }">{{ row.user?.nickname }}</template>
      </el-table-column>
      <el-table-column prop="content" label="内容" min-width="220" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="170" />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status !== 2" link type="danger" @click="setStatus(row, 2)">
            隐藏
          </el-button>
          <el-button v-else link type="success" @click="setStatus(row, 1)">恢复</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="pager"
      layout="total, prev, pager, next"
      :total="total"
      :page-size="query.size"
      :current-page="query.page"
      @current-change="(page) => { query.page = page; load() }"
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

.pager {
  margin-top: 16px;
  justify-content: flex-end;
}

.cell__book {
  font-size: 13px;
  color: #2b2b2b;
}

.cell__chapter {
  font-size: 12px;
  color: #a8a39a;
}
</style>