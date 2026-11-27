<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createOrder, getMyOrders, getPayInfo, getWallet, signIn } from '@/api/wallet'

const loading = ref(true)
const wallet = ref(null)
const signing = ref(false)
const orders = ref([])
const orderTotal = ref(0)

const payDialog = ref(false)
const payInfo = ref({ qr_url: null, coin_per_yuan: 100, amounts: [] })
const selected = ref(null)
const creating = ref(false)
const createdOrder = ref(null)

const amounts = computed(() => payInfo.value.amounts || [])

const statusText = (value) => (value === 1 ? '已到账' : value === 2 ? '已取消' : '待支付')
const statusType = (value) => (value === 1 ? 'success' : value === 2 ? 'info' : 'warning')
const yuan = (fen) => (fen / 100).toFixed(2)

async function loadWallet() {
  wallet.value = await getWallet()
}

async function loadOrders() {
  const data = await getMyOrders({ page: 1, size: 10 })
  orders.value = data.list
  orderTotal.value = data.total
}

async function doSignIn() {
  signing.value = true
  try {
    wallet.value = await signIn()
    ElMessage.success(`签到成功，西瓜 +${wallet.value.sign_reward}`)
  } catch {
    /* 拦截器已提示 */
  } finally {
    signing.value = false
  }
}

async function openRecharge() {
  payInfo.value = await getPayInfo()
  selected.value = payInfo.value.amounts?.[2] ?? payInfo.value.amounts?.[0] ?? null
  createdOrder.value = null
  payDialog.value = true
}

async function submitRecharge() {
  if (!selected.value) {
    ElMessage.warning('请选择充值金额')
    return
  }
  creating.value = true
  try {
    createdOrder.value = await createOrder(selected.value)
    await loadOrders()
  } catch {
    /* 拦截器已提示 */
  } finally {
    creating.value = false
  }
}

async function refreshStatus() {
  await loadOrders()
  await loadWallet()
  const target = orders.value.find((item) => item.id === createdOrder.value?.id)
  if (target && target.status === 1) {
    ElMessage.success('已到账')
    payDialog.value = false
    createdOrder.value = null
  } else {
    ElMessage.info('暂未到账，请稍后再试')
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await Promise.all([loadWallet(), loadOrders()])
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-loading="loading" class="wallet">
    <div class="cards">
      <div class="wcard wcard--coin">
        <p class="wcard__label">软妹币余额</p>
        <p class="wcard__value">{{ wallet?.coin ?? 0 }}</p>
        <p class="wcard__hint">1 元 = {{ wallet?.coin_per_yuan ?? 100 }} 软妹币</p>
      </div>

      <div class="wcard wcard--melon">
        <p class="wcard__label">西瓜</p>
        <p class="wcard__value">{{ wallet?.watermelon ?? 0 }}</p>
        <p class="wcard__hint">签到每次 +{{ wallet?.sign_reward ?? 1 }}</p>
      </div>

      <div class="wcard wcard--days">
        <p class="wcard__label">累计签到</p>
        <p class="wcard__value">{{ wallet?.total_sign_days ?? 0 }}</p>
        <p class="wcard__hint">天</p>
      </div>
    </div>

    <div class="actions">
      <el-button
        type="primary"
        :disabled="wallet?.signed_today"
        :loading="signing"
        @click="doSignIn"
      >
        {{ wallet?.signed_today ? '今日已签到' : '立即签到' }}
      </el-button>
      <el-button @click="openRecharge">充值软妹币</el-button>
    </div>

    <div class="orders">
      <div class="orders__head">
        <span>我的充值记录</span>
        <span class="orders__count">共 {{ orderTotal }} 笔</span>
      </div>

      <el-table :data="orders" size="small" border>
        <el-table-column prop="order_no" label="订单号" min-width="180" />
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
      </el-table>
    </div>

    <el-dialog v-model="payDialog" title="充值软妹币" width="480px">
      <div v-if="!createdOrder">
        <p class="pay__tip">选择充值金额，1 元 = {{ payInfo.coin_per_yuan }} 软妹币</p>
        <div class="pay__amounts">
          <button
            v-for="item in amounts"
            :key="item"
            class="pay__amount"
            :class="{ 'pay__amount--on': selected === item }"
            type="button"
            @click="selected = item"
          >
            <b>{{ item / 100 }} 元</b>
            <span>{{ item }} 软妹币</span>
          </button>
        </div>
      </div>

      <div v-else class="pay__done">
        <p class="pay__amount-big">{{ yuan(createdOrder.amount_fen) }} 元</p>
        <p class="pay__coin">到账 {{ createdOrder.coin }} 软妹币</p>

        <div class="pay__qr">
          <img v-if="payInfo.qr_url" :src="payInfo.qr_url" alt="收款码" />
          <div v-else class="pay__qr-empty">
            管理员尚未配置收款码<br />
            请把收款码放到 backend/static/pay/wechat.png
          </div>
        </div>

        <p class="pay__order">订单号：{{ createdOrder.order_no }}</p>
        <p class="pay__note">
          扫码支付后，请联系管理员在后台确认到账。确认后余额自动增加。
        </p>
      </div>

      <template #footer>
        <template v-if="!createdOrder">
          <el-button @click="payDialog = false">取消</el-button>
          <el-button type="primary" :loading="creating" @click="submitRecharge">生成订单</el-button>
        </template>
        <template v-else>
          <el-button @click="payDialog = false">关闭</el-button>
          <el-button type="primary" @click="refreshStatus">刷新状态</el-button>
        </template>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.wallet {
  padding-top: 16px;
}

.cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.wcard {
  padding: 18px 20px;
  border-radius: var(--radius-md);
  color: #fff;
}

.wcard--coin {
  background: linear-gradient(135deg, #f24f86, #d93e73);
}

.wcard--melon {
  background: linear-gradient(135deg, #57b894, #3f9e6a);
}

.wcard--days {
  background: linear-gradient(135deg, #ffa94d, #f08c1a);
}

.wcard__label {
  margin: 0;
  font-size: 13px;
  opacity: 0.9;
}

.wcard__value {
  margin: 6px 0 4px;
  font-size: 30px;
  font-weight: 700;
  line-height: 1.1;
}

.wcard__hint {
  margin: 0;
  font-size: 12px;
  opacity: 0.82;
}

.actions {
  display: flex;
  gap: 12px;
  margin: 18px 0 26px;
}

.orders__head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 600;
}

.orders__count {
  font-size: 12px;
  font-weight: 400;
  color: var(--c-text-muted);
}

.pay__tip {
  margin: 0 0 14px;
  font-size: 13px;
  color: var(--c-text-secondary);
}

.pay__amounts {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.pay__amount {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px 0;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  background: #fff;
}

.pay__amount b {
  font-size: 16px;
  color: var(--c-text);
}

.pay__amount span {
  font-size: 12px;
  color: var(--c-text-muted);
}

.pay__amount--on {
  border-color: var(--c-primary);
  background: var(--c-primary-soft);
}

.pay__amount--on b,
.pay__amount--on span {
  color: var(--c-primary);
}

.pay__done {
  text-align: center;
}

.pay__amount-big {
  margin: 0;
  font-size: 30px;
  font-weight: 700;
  color: var(--c-primary);
}

.pay__coin {
  margin: 4px 0 16px;
  font-size: 13px;
  color: var(--c-text-secondary);
}

.pay__qr {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  padding: 12px;
  border: 1px dashed var(--c-border-strong);
  border-radius: var(--radius-md);
}

.pay__qr img {
  width: 200px;
  height: 200px;
  object-fit: contain;
}

.pay__qr-empty {
  font-size: 13px;
  line-height: 2;
  color: var(--c-text-muted);
}

.pay__order {
  margin: 14px 0 4px;
  font-size: 12px;
  color: var(--c-text-muted);
}

.pay__note {
  margin: 0;
  font-size: 12px;
  line-height: 1.8;
  color: var(--c-text-muted);
}

@media (max-width: 640px) {
  .cards {
    grid-template-columns: 1fr;
  }
  .pay__amounts {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>