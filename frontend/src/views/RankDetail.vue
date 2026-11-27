<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { addShelf, feedWatermelon, getBooks, getMonthlyRank, getPeriodRank } from '@/api'
import { useUserStore } from '@/stores/user'
import { toast } from '@/utils/toast'
import EmptyState from '@/components/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const user = useUserStore()

const loading = ref(true)
const rows = ref([])
const busyId = ref(0)
const period = ref('week')

const PERIOD_TABS = [
  { key: 'week', label: '周榜' },
  { key: 'month', label: '月榜' },
  { key: 'all', label: '总榜' }
]
// 这三个榜有按天流水，可以切周期；新书榜/更新榜是另外的口径
const PERIOD_KEYS = ['click', 'collect', 'watermelon']

const DEFS = {
  click: { label: '点击榜', field: 'click_count', tip: '按点击量排序', unit: '次' },
  collect: { label: '收藏榜', field: 'collect_count', tip: '按被加入书架的次数排序', unit: '次' },
  watermelon: { label: '推荐榜', field: 'watermelon_count', tip: '按读者投喂的西瓜数排序', unit: '个' },
  subscribe: { label: '订阅榜', field: 'revenue_coin', tip: '按付费作品累计收入排序' },
  comment: { label: '吐槽榜', field: 'paragraph_comment_count', tip: '按间贴总数排序' },
  new: { label: '新书榜', field: null, tip: '按上架时间排序' },
  monthly: { label: '更新榜', field: null, tip: '按本月新增章节字数排序' }
}

const NAV = ['click', 'collect', 'watermelon', 'subscribe', 'comment', 'new', 'monthly']

const current = computed(() => DEFS[route.params.key] || DEFS.click)

function formatCount(value) {
  const num = Number(value || 0)
  if (num >= 10000) return `${(num / 10000).toFixed(1)}万`
  return String(num)
}

function metric(book) {
  if (book._extra) return book._extra
  if (!current.value.field) return (book.last_update_at || '').slice(0, 10)
  return formatCount(book[current.value.field])
}

function hueOf(text) {
  let h = 7
  for (const ch of text || '') h = (h * 31 + ch.charCodeAt(0)) % 360
  return h
}

function coverStyle(book) {
  const h = hueOf(book.title)
  return {
    background: `linear-gradient(140deg, hsl(${h}, 42%, 54%), hsl(${(h + 40) % 360}, 44%, 36%))`
  }
}

function readBook(book) {
  router.push(book.last_chapter_id ? `/read/${book.last_chapter_id}` : `/book/${book.id}`)
}

async function onShelf(book) {
  if (!user.isLogin) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  busyId.value = book.id
  try {
    await addShelf(book.id)
    toast('已加入书架')
  } catch {
    /* 拦截器已提示 */
  } finally {
    busyId.value = 0
  }
}

async function onFeed(book) {
  if (!user.isLogin) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  busyId.value = book.id
  try {
    const res = await feedWatermelon(book.id, 1)
    toast(`投喂成功，剩余西瓜 ${res.watermelon_left} 个 · 今天还能喂 ${res.remain_today} 个`)
  } catch {
    /* 拦截器已提示 */
  } finally {
    busyId.value = 0
  }
}

async function load() {
  loading.value = true
  rows.value = []
  const key = route.params.key
  try {
    if (key === 'monthly') {
      const data = await getMonthlyRank(50)
      rows.value = data.map((item) => ({ ...item.book, _extra: `${formatCount(item.words)} 字` }))
    } else if (PERIOD_KEYS.includes(key) && period.value !== 'all') {
      const data = await getPeriodRank(key, period.value, 50)
      const unit = current.value.unit || '次'
      rows.value = data.list.map((item) => ({
        ...item.book,
        _extra: `${formatCount(item.value)} ${unit}`
      }))
    } else {
      const data = await getBooks({ sort: key, page: 1, size: 50 })
      rows.value = data.list
    }
  } catch {
    rows.value = []
  } finally {
    loading.value = false
  }
}

function switchPeriod(next) {
  period.value = next
  load()
}

watch(() => route.params.key, () => { period.value = 'week'; load() })
onMounted(load)
</script>

<template>
  <div class="container rd">
    <div class="rd__layout">
      <aside class="rd__side">
        <h2 class="rd__side-title">小说排行榜</h2>
        <nav class="rd__nav">
          <router-link
            v-for="key in NAV"
            :key="key"
            class="rd__navitem"
            :class="{ 'rd__navitem--on': route.params.key === key || (!route.params.key && key === 'click') }"
            :to="`/rank/${key}`"
          >
            {{ DEFS[key].label }}
          </router-link>
        </nav>
        <router-link class="rd__back" to="/rank">← 返回总览</router-link>
      </aside>

      <main class="rd__main">
        <div class="rd__head">
          <h1 class="rd__title">{{ current.label }}</h1>
          <span class="rd__tip">{{ current.tip }}</span>
          <div v-if="PERIOD_KEYS.includes(route.params.key)" class="rd__tabs">
            <button
              v-for="tab in PERIOD_TABS"
              :key="tab.key"
              class="rd__tab"
              :class="{ 'rd__tab--on': period === tab.key }"
              type="button"
              @click="switchPeriod(tab.key)"
            >
              {{ tab.label }}
            </button>
          </div>
        </div>

        <div v-if="loading" class="skeleton" style="height: 360px"></div>

        <EmptyState v-else-if="!rows.length" text="榜单暂无数据" action-text="去书库看看" to="/search" />

        <ol v-else class="rlist">
          <li v-for="(book, index) in rows" :key="book.id" class="rrow">
            <div class="rrow__rank" :class="`rrow__rank--${index + 1}`">{{ index + 1 }}</div>

            <router-link class="rrow__cover" :style="coverStyle(book)" :to="`/book/${book.id}`">
              <img v-if="book.cover" :src="book.cover" :alt="book.title" />
              <span v-else>{{ book.title.slice(0, 2) }}</span>
            </router-link>

            <div class="rrow__body">
              <router-link class="rrow__title" :to="`/book/${book.id}`">{{ book.title }}</router-link>

              <p class="rrow__meta">
                <span class="rrow__label">小说作者：</span>
                <span class="rrow__author">{{ book.author?.nickname }}</span>
              </p>

              <p class="rrow__meta">
                <span class="rrow__label">最近更新：</span>
                {{ (book.last_update_at || '').slice(0, 16).replace('T', ' ') }}
                <template v-if="book.last_chapter_title"> / {{ book.last_chapter_title }}</template>
              </p>

              <p class="rrow__intro">{{ book.intro }}</p>
            </div>

            <div class="rrow__side">
              <span class="rrow__value">{{ metric(book) }}</span>
              <button class="rbtn rbtn--read" type="button" @click="readBook(book)">点击阅读</button>
              <button
                class="rbtn"
                type="button"
                :disabled="busyId === book.id"
                @click="onShelf(book)"
              >
                加入书架
              </button>
              <button
                class="rbtn"
                type="button"
                :disabled="busyId === book.id"
                @click="onFeed(book)"
              >
                投喂西瓜
              </button>
            </div>
          </li>
        </ol>
      </main>
    </div>
  </div>
</template>

<style scoped>
.rd {
  padding-top: 20px;
}

.rd__layout {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 20px;
}

.rd__side {
  position: sticky;
  top: 130px;
  align-self: start;
  padding: 16px 0;
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.rd__side-title {
  margin: 0 16px 12px;
  font-size: 16px;
  font-weight: 600;
}

.rd__nav {
  display: flex;
  flex-direction: column;
}

.rd__navitem {
  padding: 11px 16px;
  font-size: 14px;
  color: var(--c-text-secondary);
  border-left: 3px solid transparent;
}

.rd__navitem:hover {
  color: var(--c-primary);
  background: #fffafb;
}

.rd__navitem--on {
  color: var(--c-primary);
  font-weight: 600;
  border-left-color: var(--c-primary);
  background: var(--c-primary-soft);
}

.rd__back {
  display: block;
  margin: 12px 16px 0;
  padding-top: 12px;
  border-top: 1px dashed var(--c-border);
  font-size: 12px;
  color: var(--c-text-muted);
}

.rd__back:hover {
  color: var(--c-primary);
}

.rd__main {
  min-width: 0;
}

.rd__head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 14px;
  padding: 16px 20px;
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.rd__title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
}

.rd__tip {
  font-size: 12px;
  color: var(--c-text-muted);
}

.rd__tabs {
  margin-left: auto;
  display: flex;
  gap: 6px;
}

.rd__tab {
  padding: 4px 14px;
  border: 1px solid var(--c-border-strong);
  border-radius: 14px;
  background: #fff;
  font-size: 12px;
  color: var(--c-text-secondary);
}

.rd__tab:hover {
  border-color: var(--c-primary);
  color: var(--c-primary);
}

.rd__tab--on {
  background: var(--c-primary);
  border-color: var(--c-primary);
  color: #fff;
}

.rd__badge {
  margin-left: auto;
  padding: 2px 10px;
  border-radius: 3px;
  background: var(--c-primary-soft);
  color: var(--c-primary);
  font-size: 12px;
}

/* 榜单行 */
.rlist {
  margin: 0;
  padding: 0;
  list-style: none;
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.rrow {
  display: flex;
  gap: 18px;
  padding: 20px;
  border-bottom: 1px solid #f5f5f5;
}

.rrow:last-child {
  border-bottom: none;
}

.rrow:hover {
  background: #fffcfd;
}

.rrow__rank {
  width: 46px;
  flex-shrink: 0;
  font-size: 34px;
  font-weight: 700;
  font-style: italic;
  line-height: 1;
  text-align: center;
  color: #d9d9d9;
  font-family: 'Georgia', 'Times New Roman', serif;
}

.rrow__rank--1 {
  color: #e34d59;
}

.rrow__rank--2 {
  color: #f5a623;
}

.rrow__rank--3 {
  color: #d4a373;
}

.rrow__cover {
  width: 108px;
  height: 144px;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 2px;
  color: rgba(255, 255, 255, 0.92);
  font-family: 'Songti SC', 'Noto Serif SC', serif;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.12);
}

.rrow__cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.rrow__body {
  flex: 1;
  min-width: 0;
}

.rrow__title {
  display: inline-block;
  margin-bottom: 8px;
  font-size: 17px;
  font-weight: 600;
  color: var(--c-text);
}

.rrow__title:hover {
  color: var(--c-primary);
}

.rrow__meta {
  margin: 0 0 5px;
  font-size: 12px;
  color: var(--c-text-muted);
}

.rrow__label {
  color: var(--c-text-muted);
}

.rrow__author {
  color: var(--c-primary);
}

.rrow__intro {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.85;
  color: var(--c-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.rrow__side {
  width: 108px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
}

.rrow__value {
  margin-bottom: 2px;
  font-size: 15px;
  font-weight: 700;
  color: var(--c-accent);
  text-align: center;
}

.rbtn {
  padding: 7px 0;
  border: 1px solid var(--c-border-strong);
  border-radius: var(--radius-sm);
  background: #fff;
  font-size: 13px;
  color: var(--c-text-secondary);
}

.rbtn:hover {
  border-color: var(--c-primary);
  color: var(--c-primary);
}

.rbtn--read {
  background: var(--c-danger);
  border-color: var(--c-danger);
  color: #fff;
}

.rbtn--read:hover {
  background: #d93e73;
  border-color: #d93e73;
  color: #fff;
}

.rbtn[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 900px) {
  .rd__layout {
    grid-template-columns: 1fr;
  }
  .rd__side {
    position: static;
  }
  .rd__nav {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 8px;
    padding: 0 16px;
  }
  .rd__navitem {
    border-left: none;
    border: 1px solid var(--c-border);
    border-radius: 16px;
    padding: 5px 14px;
    font-size: 13px;
  }
  .rrow {
    flex-wrap: wrap;
  }
  .rrow__cover {
    width: 84px;
    height: 112px;
  }
  .rrow__side {
    width: 100%;
    flex-direction: row;
  }
  .rrow__value {
    margin-right: auto;
  }
}
</style>
