<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getMyNotices, readAllNotices, readNotice } from '@/api'
import { toast } from '@/utils/toast'
import EmptyState from '@/components/EmptyState.vue'

const router = useRouter()
const loading = ref(true)
const list = ref([])
const total = ref(0)
const unread = ref(0)
const query = reactive({ page: 1, size: 10, unread_only: false })

const TYPE = {
  audit: { text: '审核', color: '#e6a23c' },
  shelf: { text: '上架', color: '#409eff' },
  report: { text: '处理', color: '#f56c6c' },
  system: { text: '系统', color: '#909399' }
}
const typeOf = (v) => TYPE[v] || TYPE.system

function formatTime(value) {
  return (value || '').replace('T', ' ').slice(0, 16)
}

async function load() {
  loading.value = true
  try {
    const data = await getMyNotices({
      page: query.page,
      size: query.size,
      unread_only: query.unread_only
    })
    list.value = data.list
    total.value = data.total
    unread.value = data.unread
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

async function open(item) {
  if (!item.is_read) {
    try {
      const res = await readNotice(item.id)
      item.is_read = true
      unread.value = res.unread
    } catch {
      /* 拦截器已提示 */
    }
  }
  if (item.link) router.push(item.link)
}

async function readAll() {
  try {
    await readAllNotices()
    list.value = list.value.map((item) => ({ ...item, is_read: true }))
    unread.value = 0
    toast('已全部标为已读')
  } catch {
    /* 拦截器已提示 */
  }
}

function switchFilter(onlyUnread) {
  query.unread_only = onlyUnread
  query.page = 1
  load()
}

onMounted(load)
</script>

<template>
  <div class="nt">
    <div class="nt__bar">
      <el-radio-group
        :model-value="query.unread_only"
        @change="(v) => switchFilter(v)"
      >
        <el-radio-button :value="false">全部</el-radio-button>
        <el-radio-button :value="true">未读{{ unread ? `（${unread}）` : '' }}</el-radio-button>
      </el-radio-group>
      <el-button v-if="unread > 0" link type="primary" @click="readAll">全部标为已读</el-button>
    </div>

    <div v-if="loading" class="skeleton" style="height: 160px"></div>

    <EmptyState v-else-if="!list.length" text="暂时没有消息" />

    <ul v-else class="nt__list">
      <li
        v-for="item in list"
        :key="item.id"
        class="msg"
        :class="{ 'msg--unread': !item.is_read }"
        @click="open(item)"
      >
        <span class="msg__dot" :style="{ background: typeOf(item.type).color }"></span>
        <div class="msg__body">
          <div class="msg__top">
            <span class="msg__type" :style="{ color: typeOf(item.type).color }">
              {{ typeOf(item.type).text }}
            </span>
            <span class="msg__title">{{ item.title }}</span>
            <span v-if="!item.is_read" class="msg__new">未读</span>
          </div>
          <p v-if="item.content" class="msg__content">{{ item.content }}</p>
          <span class="msg__time">{{ formatTime(item.created_at) }}</span>
        </div>
        <span v-if="item.link" class="msg__go">›</span>
      </li>
    </ul>

    <div v-if="total > query.size" class="nt__pager">
      <el-button
        size="small"
        :disabled="query.page <= 1"
        @click="query.page -= 1; load()"
      >
        上一页
      </el-button>
      <span class="nt__page">{{ query.page }} / {{ Math.ceil(total / query.size) }}</span>
      <el-button
        size="small"
        :disabled="query.page >= Math.ceil(total / query.size)"
        @click="query.page += 1; load()"
      >
        下一页
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.nt {
  padding-top: 16px;
}

.nt__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.nt__list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.msg {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px 16px;
  margin-bottom: 8px;
  background: #fff;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.msg:hover {
  border-color: var(--c-primary-light);
  box-shadow: var(--shadow-card);
}

.msg--unread {
  background: #fffbfc;
  border-color: var(--c-primary-soft);
}

.msg__dot {
  width: 7px;
  height: 7px;
  margin-top: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.msg__body {
  flex: 1;
  min-width: 0;
}

.msg__top {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.msg__type {
  font-size: 12px;
  font-weight: 600;
}

.msg__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text);
}

.msg__new {
  padding: 0 6px;
  border-radius: 3px;
  background: var(--c-primary);
  color: #fff;
  font-size: 11px;
  line-height: 17px;
}

.msg__content {
  margin: 5px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--c-text-secondary);
}

.msg__time {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: var(--c-text-muted);
}

.msg__go {
  color: var(--c-text-muted);
  font-size: 18px;
  line-height: 1;
}

.nt__pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 14px;
}

.nt__page {
  font-size: 13px;
  color: var(--c-text-muted);
}
</style>
