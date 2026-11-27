<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createCategory, deleteCategory, getCategories, updateCategory } from '@/api/admin'
import { confirmDialog } from '@/composables/useConfirm'

const loading = ref(true)
const list = ref([])
const dialogVisible = ref(false)
const editing = ref(null)
const form = ref({ name: '', sort: 0 })

async function load() {
  loading.value = true
  try {
    list.value = await getCategories()
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.value = { name: '', sort: 0 }
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = row
  form.value = { name: row.name, sort: row.sort }
  dialogVisible.value = true
}

async function submit() {
  const name = form.value.name.trim()
  if (!name) {
    ElMessage.warning('请输入分类名')
    return
  }
  try {
    if (editing.value) {
      await updateCategory(editing.value.id, { name, sort: Number(form.value.sort) || 0 })
    } else {
      await createCategory({ name, sort: Number(form.value.sort) || 0 })
    }
    ElMessage.success('已保存')
    dialogVisible.value = false
    await load()
  } catch {
    /* 拦截器已提示 */
  }
}

async function remove(row) {
  const confirmed = await confirmDialog({
    title: '删除分类？',
    message: `「${row.name}」下如果还有书籍，将无法删除。`,
    confirmText: '删除'
  })
  if (!confirmed) return
  try {
    await deleteCategory(row.id)
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
      <span class="bar__title">分类列表（{{ list.length }}）</span>
      <el-button type="primary" @click="openCreate">新增分类</el-button>
    </div>

    <el-table v-loading="loading" :data="list" border stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="分类名" min-width="160" />
      <el-table-column prop="book_count" label="书籍数" width="100" />
      <el-table-column prop="sort" label="排序值" width="100" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="editing ? '编辑分类' : '新增分类'"
      width="420px"
    >
      <el-form label-width="80px">
        <el-form-item label="分类名">
          <el-input v-model="form.name" maxlength="32" placeholder="例如：科幻未来" />
        </el-form-item>
        <el-form-item label="排序值">
          <el-input-number v-model="form.sort" :min="0" :max="9999" />
          <span class="hint">数值越小越靠前</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
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
  justify-content: space-between;
  margin-bottom: 16px;
}

.bar__title {
  font-size: 14px;
  font-weight: 600;
  color: #2b2b2b;
}

.hint {
  margin-left: 10px;
  font-size: 12px;
  color: #a8a39a;
}
</style>