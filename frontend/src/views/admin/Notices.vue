<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createNotice, deleteNotice, getAdminNotices, updateNotice } from '@/api/admin'
import { confirmDialog } from '@/composables/useConfirm'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ status: null, page: 1, size: 10 })

const dialog = ref(false)
const editing = ref(null)
const form = reactive({ title: '', content: '', category: '公告', is_top: false })
const saving = ref(false)

const categories = ['公告', '活动', '更新']

function catType(c) {
  return c === '活动' ? 'warning' : c === '更新' ? 'primary' : 'info'
}

async function load() {
  loading.value = true
  try {
    const params = { page: query.page, size: query.size }
    if (query.status !== null) params.status = query.status
    const data = await getAdminNotices(params)
    list.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.title = ''
  form.content = ''
  form.category = '公告'
  form.is_top = false
  dialog.value = true
}

function openEdit(row) {
  editing.value = row
  form.title = row.title
  form.content = row.content
  form.category = row.category
  form.is_top = row.is_top
  dialog.value = true
}

async function save() {
  if (!form.title.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateNotice(editing.value.id, { ...form })
      ElMessage.success('已保存')
    } else {
      await createNotice({ ...form })
      ElMessage.success('已发布')
    }
    dialog.value = false
    await load()
  } catch {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}

async function toggleStatus(row) {
  try {
    await updateNotice(row.id, { status: row.status !== 1 })
    row.status = row.status === 1 ? 0 : 1
    ElMessage.success(row.status === 1 ? '已显示' : '已隐藏')
  } catch {
    /* 拦截器已提示 */
  }
}

async function remove(row) {
  const ok = await confirmDialog({
    title: '删除这条公告？',
    message: `「${row.title}」删除后不可恢复。`,
    confirmText: '删除'
  })
  if (!ok) return
  try {
    await deleteNotice(row.id)
    ElMessage.success('已删除')
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
      <el-select v-model="query.status" placeholder="全部状态" clearable style="width: 140px">
        <el-option label="显示中" :value="1" />
        <el-option label="已隐藏" :value="0" />
      </el-select>
      <el-button type="primary" @click="query.page = 1; load()">查询</el-button>
      <el-button type="success" @click="openCreate">新建公告</el-button>
      <span class="bar__tip">首页右侧「最新活动」展示置顶优先、最多 5 条</span>
    </div>

    <el-table v-loading="loading" :data="list" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="分类" width="90">
        <template #default="{ row }">
          <el-tag :type="catType(row.category)" size="small">{{ row.category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="标题" min-width="240">
        <template #default="{ row }">
          <span v-if="row.is_top" class="top">置顶</span>
          {{ row.title }}
        </template>
      </el-table-column>
      <el-table-column prop="content" label="正文" min-width="200" show-overflow-tooltip />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
            {{ row.status === 1 ? '显示中' : '已隐藏' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="190" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link :type="row.status === 1 ? 'warning' : 'success'" @click="toggleStatus(row)">
            {{ row.status === 1 ? '隐藏' : '显示' }}
          </el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
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

    <el-dialog v-model="dialog" :title="editing ? '编辑公告' : '新建公告'" width="560px">
      <el-form label-width="70px">
        <el-form-item label="标题">
          <el-input v-model="form.title" maxlength="120" show-word-limit />
        </el-form-item>
        <el-form-item label="分类">
          <el-radio-group v-model="form.category">
            <el-radio v-for="c in categories" :key="c" :value="c">{{ c }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="置顶">
          <el-switch v-model="form.is_top" />
        </el-form-item>
        <el-form-item label="正文">
          <el-input v-model="form.content" type="textarea" :rows="5" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
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

.top {
  display: inline-block;
  margin-right: 6px;
  padding: 0 6px;
  border-radius: 3px;
  background: #f24f86;
  color: #fff;
  font-size: 11px;
}
</style>
