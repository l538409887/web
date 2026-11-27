<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { auditChapter, getAdminChapters } from '@/api/admin'
import { confirmDialog } from '@/composables/useConfirm'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ audit_status: 1, book_id: null, page: 1, size: 10 })
const busyId = ref(0)

const AUDIT = {
  0: { text: '草稿', type: 'info' },
  1: { text: '待审核', type: 'warning' },
  2: { text: '已通过', type: 'success' },
  3: { text: '未通过', type: 'danger' }
}
const auditOf = (v) => AUDIT[v] || AUDIT[1]

function formatTime(value) {
  return (value || '').replace('T', ' ').slice(0, 16)
}

async function load() {
  loading.value = true
  try {
    const params = { page: query.page, size: query.size }
    if (query.audit_status !== null) params.audit_status = query.audit_status
    if (query.book_id) params.book_id = query.book_id
    const data = await getAdminChapters(params)
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

async function review(row, value) {
  const isReject = value === 3
  const ok = await confirmDialog({
    title: isReject ? '驳回这一章？' : '通过这一章？',
    message: isReject
      ? '驳回后读者看不到该章节，作者可在作者中心看到「未通过」。'
      : '通过后该章节会出现在前台目录中（书籍已上架的前提下）。',
    confirmText: isReject ? '驳回' : '通过'
  })
  if (!ok) return

  busyId.value = row.id
  try {
    await auditChapter(row.id, value)
    row.audit_status = value
    ElMessage.success(isReject ? '已驳回' : '已通过')
  } catch {
    /* 拦截器已提示 */
  } finally {
    busyId.value = 0
  }
}

onMounted(load)
</script>

<template>
  <el-card shadow="never" class="panel">
    <div class="bar">
      <el-radio-group v-model="query.audit_status" @change="search">
        <el-radio-button :value="1">待审核</el-radio-button>
        <el-radio-button :value="2">已通过</el-radio-button>
        <el-radio-button :value="3">未通过</el-radio-button>
        <el-radio-button :value="null">全部</el-radio-button>
      </el-radio-group>
      <el-input
        v-model.number="query.book_id"
        placeholder="按作品 ID 筛选"
        clearable
        style="width: 160px"
        @keyup.enter="search"
      />
      <el-button type="primary" @click="search">查询</el-button>
      <span class="bar__tip">章节采用先审后发，未通过审核的章节前台不可见</span>
    </div>

    <el-table v-loading="loading" :data="list" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="作品" min-width="150">
        <template #default="{ row }">
          <div class="cell__book">{{ row.book_title }}</div>
          <div class="cell__sub">书名 ID {{ row.book_id }}</div>
        </template>
      </el-table-column>
      <el-table-column label="章节" min-width="200">
        <template #default="{ row }">
          <div>第 {{ row.chapter_no }} 章 · {{ row.title }}</div>
          <div class="cell__sub">{{ row.preview }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="word_count" label="字数" width="90" />
      <el-table-column label="审核" width="100">
        <template #default="{ row }">
          <el-tag :type="auditOf(row.audit_status).type" size="small">
            {{ auditOf(row.audit_status).text }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="提交时间" width="160">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.audit_status !== 2"
            link
            type="success"
            :disabled="busyId === row.id"
            @click="review(row, 2)"
          >
            通过
          </el-button>
          <el-button
            v-if="row.audit_status !== 3"
            link
            type="danger"
            :disabled="busyId === row.id"
            @click="review(row, 3)"
          >
            驳回
          </el-button>
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
  gap: 12px;
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

.cell__book {
  font-size: 13px;
  color: #2b2b2b;
}

.cell__sub {
  font-size: 12px;
  color: #a8a39a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
