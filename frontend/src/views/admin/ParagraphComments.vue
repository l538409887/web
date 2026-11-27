<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  auditParagraphComment,
  getParagraphComments,
  updateParagraphStatus
} from '@/api/admin'
import { confirmDialog } from '@/composables/useConfirm'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ only_reported: false, status: null, audit_status: 0, page: 1, size: 10 })

const statusText = (v) => (v === 1 ? '显示中' : '已隐藏')
const statusType = (v) => (v === 1 ? 'success' : 'info')

function rowClass({ row }) {
  if (row.report_count >= 3) return 'row-danger'
  if (row.report_count > 0) return 'row-warn'
  return ''
}

async function load() {
  loading.value = true
  try {
    const params = {
      only_reported: query.only_reported,
      page: query.page,
      size: query.size
    }
    if (query.status !== null) params.status = query.status
    if (query.audit_status !== null) params.audit_status = query.audit_status
    const data = await getParagraphComments(params)
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

const AUDIT = {
  0: { text: '待审核', type: 'warning' },
  1: { text: '已通过', type: 'success' },
  2: { text: '已驳回', type: 'danger' }
}
const auditOf = (v) => AUDIT[v] || AUDIT[0]

async function review(row, value) {
  const isReject = value === 2
  const ok = await confirmDialog({
    title: isReject ? '驳回这条间贴？' : '通过审核？',
    message: isReject ? '驳回后前台不再展示，书籍间贴计数减一。' : '通过后正常展示。',
    confirmText: isReject ? '驳回' : '通过'
  })
  if (!ok) return
  try {
    await auditParagraphComment(row.id, value)
    row.audit_status = value
    if (isReject) row.status = 0
    ElMessage.success(isReject ? '已驳回' : '已通过')
  } catch {
    /* 拦截器已提示 */
  }
}

async function toggle(row) {
  const toHide = row.status === 1
  const ok = await confirmDialog({
    title: toHide ? '隐藏这条间贴？' : '恢复这条间贴？',
    message: toHide
      ? '隐藏后读者看不到，书籍间贴计数会同步减少。'
      : '恢复后重新对读者可见。',
    confirmText: toHide ? '隐藏' : '恢复'
  })
  if (!ok) return
  try {
    await updateParagraphStatus(row.id, toHide ? 0 : 1)
    row.status = toHide ? 0 : 1
    ElMessage.success(toHide ? '已隐藏' : '已恢复')
  } catch {
    /* 拦截器已提示 */
  }
}

onMounted(load)
</script>

<template>
  <el-card shadow="never" class="panel">
    <div class="bar">
      <el-switch
        v-model="query.only_reported"
        active-text="只看被举报"
        @change="search"
      />
      <el-select v-model="query.audit_status" placeholder="全部审核态" clearable style="width: 140px">
        <el-option label="待审核" :value="0" />
        <el-option label="已通过" :value="1" />
        <el-option label="已驳回" :value="2" />
      </el-select>
      <el-select v-model="query.status" placeholder="全部状态" clearable style="width: 140px">
        <el-option label="显示中" :value="1" />
        <el-option label="已隐藏" :value="0" />
      </el-select>
      <el-button type="primary" @click="search">查询</el-button>
      <span class="bar__tip">举报数 ≥3 标红，1~2 标黄</span>
    </div>

    <el-table v-loading="loading" :data="list" border stripe :row-class-name="rowClass">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="所属" min-width="170">
        <template #default="{ row }">
          <div class="cell__book">{{ row.book_title }}</div>
          <div class="cell__sub">
            {{ row.chapter_title }} · 第 {{ row.paragraph_index + 1 }} 段
          </div>
        </template>
      </el-table-column>
      <el-table-column label="用户" width="110">
        <template #default="{ row }">{{ row.nickname || row.username }}</template>
      </el-table-column>
      <el-table-column prop="content" label="间贴内容" min-width="220" show-overflow-tooltip />
      <el-table-column label="互动" width="150">
        <template #default="{ row }">
          <span class="stat">赞 {{ row.like_count }}</span>
          <span class="stat">踩 {{ row.dislike_count }}</span>
          <span class="stat stat--report">举报 {{ row.report_count }}</span>
        </template>
      </el-table-column>
      <el-table-column label="审核" width="100">
        <template #default="{ row }">
          <el-tag :type="auditOf(row.audit_status).type" size="small">
            {{ auditOf(row.audit_status).text }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="165" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.audit_status !== 1"
            link
            type="success"
            @click="review(row, 1)"
          >
            通过
          </el-button>
          <el-button
            v-if="row.audit_status !== 2"
            link
            type="danger"
            @click="review(row, 2)"
          >
            驳回
          </el-button>
          <el-button v-if="row.status === 1" link @click="toggle(row)">隐藏</el-button>
          <el-button v-else link @click="toggle(row)">恢复</el-button>
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
  gap: 14px;
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
}

.stat {
  margin-right: 8px;
  font-size: 12px;
  color: #7a7a7a;
}

.stat--report {
  color: #e34d59;
  font-weight: 600;
}

:deep(.row-warn) {
  --el-table-tr-bg-color: #fffbf0;
}

:deep(.row-danger) {
  --el-table-tr-bg-color: #fff2f2;
}
</style>