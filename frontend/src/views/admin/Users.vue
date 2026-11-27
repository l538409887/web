<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAdminUsers, updateUser } from '@/api/admin'
import { confirmDialog } from '@/composables/useConfirm'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ keyword: '', role: null, status: null, page: 1, size: 10 })

const roles = [
  { value: 'reader', label: '读者' },
  { value: 'author', label: '作者' },
  { value: 'admin', label: '管理员' }
]

async function load() {
  loading.value = true
  try {
    const params = { keyword: query.keyword || undefined, page: query.page, size: query.size }
    if (query.role) params.role = query.role
    if (query.status !== null) params.status = query.status
    const data = await getAdminUsers(params)
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

async function changeRole(row, role) {
  try {
    await updateUser(row.id, { role })
    row.role = role
    ElMessage.success('角色已更新')
  } catch {
    await load()
  }
}

async function toggleStatus(row, value) {
  if (!value) {
    const confirmed = await confirmDialog({
      title: '禁用该账号？',
      message: `禁用后「${row.nickname || row.username}」将无法登录。`,
      confirmText: '禁用'
    })
    if (!confirmed) return
  }
  try {
    await updateUser(row.id, { status: value ? 1 : 0 })
    row.status = value ? 1 : 0
    ElMessage.success('状态已更新')
  } catch {
    await load()
  }
}

onMounted(load)
</script>

<template>
  <el-card shadow="never" class="panel">
    <div class="bar">
      <el-input
        v-model="query.keyword"
        placeholder="搜索用户名"
        clearable
        style="width: 220px"
        @keyup.enter="search"
      />
      <el-radio-group v-model="query.role" @change="search">
        <el-radio-button :value="null">全部</el-radio-button>
        <el-radio-button value="reader">读者</el-radio-button>
        <el-radio-button value="author">作者</el-radio-button>
        <el-radio-button value="admin">管理员</el-radio-button>
      </el-radio-group>
      <el-select v-model="query.status" placeholder="全部状态" clearable style="width: 140px">
        <el-option label="正常" :value="1" />
        <el-option label="已禁用" :value="0" />
      </el-select>
      <el-button type="primary" @click="search">查询</el-button>
    </div>

    <el-table v-loading="loading" :data="list" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="用户名" width="130" />
      <el-table-column prop="nickname" label="昵称" min-width="120" />
      <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
      <el-table-column label="角色" width="140">
        <template #default="{ row }">
          <el-select
            :model-value="row.role"
            size="small"
            @change="(value) => changeRole(row, value)"
          >
            <el-option v-for="role in roles" :key="role.value" :label="role.label" :value="role.value" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-switch
            :model-value="row.status === 1"
            @change="(value) => toggleStatus(row, value)"
          />
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="注册时间" width="170" />
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
  flex-wrap: wrap;
}

.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>