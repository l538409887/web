<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { cancelOrder, confirmOrder, getAdminOrders } from '@/api/wallet'
import { confirmDialog } from '@/composables/useConfirm'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ status: 0, page: 1, size: 10 })

const statusText = (v) => (v === 1 ? '已到账' : v === 2 ? '已取消' : '待支付')
const statusType = (v) => (v === 1 ? 'success' : v === 2 ? 'info' : 'warning')
const yuan = (fen) => (fen / 100).toFixed(2)

async function load() {
  loading.value = true
  try {
    const params = { page: query.page, size: query.size }
    if (query.status !== null) params.status = query.status
    const data = await getAdminOrders(params)
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

async function doConfirm(row) {
  const ok = await confirmDialog({
    title: '确认已收到款项？',
    message: `订单 ${row.order_no}，金额 ${yuan(row.amount_fen)} 元，确认后将为「${row.nickname || row.username}」增加 ${row.coin} 软妹币。`,
    confirmText: '确认到账',
    danger: false
  })
  if (!ok) return
  try {
    const res = await confirmOrder(row.id)
    ElMessage.success(`已到账，该用户当前余额 ${res.balance}`)
    await load()
  } catch {
    /* 拦截器已提示 */
  }
}

async function doCancel(row) {
  const ok = await confirmDialog({
    title: '取消这笔订单？',
    message: `订单 ${row.order_no} 将被置为已取消。`,
    confirmText: '取消订单'
  })
  if (!ok) return
  try {
    await cancelOrder(row.id)
    ElMessage.success('已取消')
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
      <el-select v-model="query.status" placeholder="全部状态" clearable style="width: 150px">
        <el-option label="待支付" :value="0" />
        <el-option label="已到账" :value="1" />
        <el-option label="已取消" :value="2" />
      </el-select>
      <el-button type="primary" @click="search">查询</el-button>
      <span class="bar__tip">确认到账后余额会立即增加，且不可重复确认</span>
    </div>

    <el-table v-loading="loading" :data="list" border stripe>
      <el-table-column prop="order_no" label="订单号" min-width="180" />
      <el-table-column label="用户" width="140">
        <template #default="{ row }">{{ row.nickname || row.username }}</template>
      </el-table-column>
      <el-table-column label="金额" width="100">
        <template #default="{ row }">{{ yuan(row.amount_fen) }} 元</template>
      </el-table-column>
      <el-table-column prop="coin" label="软妹币" width="100" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="下单时间" width="170" />
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 0">
            <el-button link type="primary" @click="doConfirm(row)">确认到账</el-button>
            <el-button link type="danger" @click="doCancel(row)">取消</el-button>
          </template>
          <span v-else class="done">—</span>
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

.done {
  color: #c0c0c0;
}
</style>