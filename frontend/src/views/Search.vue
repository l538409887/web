<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getBooks } from '@/api'
import { useCatalogStore } from '@/stores/catalog'
import EmptyState from '@/components/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const catalog = useCatalogStore()

const loading = ref(true)
const list = ref([])
const total = ref(0)
const size = 20

const keyword = ref('')
const categoryId = ref(null)
const sort = ref('update')
const status = ref(null)
const days = ref(null)
const wordRange = ref(null)
const page = ref(1)
const jumpPage = ref('')

const sortOptions = [
  { key: 'update', label: '默认' },
  { key: 'click', label: '最多点击' },
  { key: 'collect', label: '最多收藏' },
  { key: 'recommend', label: '最多推荐' },
  { key: 'word', label: '字数最多' },
  { key: 'new', label: '最新上架' }
]

const wordOptions = [
  { key: null, label: '不限' },
  { key: 'lt30', label: '30 万字以下' },
  { key: '30to100', label: '30-100 万字' },
  { key: 'gt100', label: '100 万字以上' }
]

const updateOptions = [
  { key: null, label: '不限' },
  { key: 3, label: '三日内' },
  { key: 7, label: '七日内' },
  { key: 30, label: '一月内' }
]

const statusOptions = [
  { key: null, label: '不限' },
  { key: 0, label: '连载中' },
  { key: 1, label: '已完结' }
]

const pages = computed(() => Math.max(1, Math.ceil(total.value / size)))

const pageList = computed(() => {
  const sum = pages.value
  const cur = page.value
  if (sum <= 7) {
    return Array.from({ length: sum }, (_, i) => i + 1)
  }
  const result = [1]
  const start = Math.max(2, cur - 2)
  const end = Math.min(sum - 1, cur + 2)
  if (start > 2) result.push('...')
  for (let i = start; i <= end; i++) result.push(i)
  if (end < sum - 1) result.push('...')
  result.push(sum)
  return result
})

const activeSummary = computed(() => {
  const parts = []
  if (keyword.value) parts.push(`关键词「${keyword.value}」`)
  if (categoryId.value) {
    const cat = catalog.categories.find((item) => item.id === categoryId.value)
    if (cat) parts.push(cat.name)
  }
  if (status.value !== null) parts.push(status.value === 1 ? '已完结' : '连载中')
  if (days.value) {
    const opt = updateOptions.find((item) => item.key === days.value)
    if (opt) parts.push(opt.label)
  }
  if (wordRange.value) {
    const opt = wordOptions.find((item) => item.key === wordRange.value)
    if (opt) parts.push(opt.label)
  }
  return parts.join(' · ')
})

function initFromRoute() {
  const query = route.query
  keyword.value = (query.keyword || '').toString()
  categoryId.value = query.category ? Number(query.category) : null
  sort.value = (query.sort || 'update').toString()
  status.value = query.status === undefined || query.status === '' ? null : Number(query.status)
  days.value = query.days ? Number(query.days) : null
  wordRange.value = query.words ? query.words.toString() : null
  page.value = query.page ? Number(query.page) : 1
}

function syncQuery() {
  const query = {}
  if (keyword.value) query.keyword = keyword.value
  if (categoryId.value) query.category = categoryId.value
  if (sort.value !== 'update') query.sort = sort.value
  if (status.value !== null) query.status = status.value
  if (days.value) query.days = days.value
  if (wordRange.value) query.words = wordRange.value
  if (page.value > 1) query.page = page.value
  router.replace({ path: '/search', query })
}

function dayParams() {
  return days.value ? { days: days.value } : {}
}

function wordParams() {
  if (wordRange.value === 'lt30') return { max_words: 300000 }
  if (wordRange.value === '30to100') return { min_words: 300000, max_words: 1000000 }
  if (wordRange.value === 'gt100') return { min_words: 1000000 }
  return {}
}

async function load() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      size,
      sort: sort.value,
      ...dayParams(),
      ...wordParams()
    }
    if (keyword.value) params.keyword = keyword.value
    if (categoryId.value) params.category_id = categoryId.value
    if (status.value !== null) params.status = status.value

    const data = await getBooks(params)
    list.value = data.list
    total.value = data.total
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

function apply() {
  page.value = 1
  syncQuery()
  load()
}

function selectCategory(id) {
  categoryId.value = categoryId.value === id ? null : id
  apply()
}

function selectSort(key) {
  sort.value = key
  apply()
}

function selectStatus(key) {
  status.value = key
  apply()
}

function selectDays(key) {
  days.value = key
  apply()
}

function selectWord(key) {
  wordRange.value = key
  apply()
}

function goPage(target) {
  if (typeof target !== 'number' || target < 1 || target > pages.value) return
  page.value = target
  syncQuery()
  load()
}

function doJump() {
  const target = Number(jumpPage.value)
  if (!Number.isInteger(target) || target < 1 || target > pages.value) {
    jumpPage.value = ''
    return
  }
  goPage(target)
  jumpPage.value = ''
}

watch(
  () => route.query.keyword,
  (value) => {
    const next = (value || '').toString()
    if (next !== keyword.value) {
      keyword.value = next
      page.value = 1
      load()
    }
  }
)

onMounted(async () => {
  initFromRoute()
  await catalog.ensureCategories()
  load()
})
</script>

<template>
  <div class="container lib">
    <section class="filters">
      <div class="filters__row">
        <span class="filters__label">作品分类：</span>
        <div class="filters__opts">
          <button
            class="chip"
            :class="{ 'chip--on': !categoryId }"
            type="button"
            @click="selectCategory(null)"
          >
            全部
          </button>
          <button
            v-for="cat in catalog.categories"
            :key="cat.id"
            class="chip"
            :class="{ 'chip--on': categoryId === cat.id }"
            type="button"
            @click="selectCategory(cat.id)"
          >
            {{ cat.name }}
            <em>{{ cat.book_count }}</em>
          </button>
        </div>
      </div>

      <div class="filters__row">
        <span class="filters__label">排序方式：</span>
        <div class="filters__opts">
          <button
            v-for="opt in sortOptions"
            :key="opt.key"
            class="chip"
            :class="{ 'chip--on': sort === opt.key }"
            type="button"
            @click="selectSort(opt.key)"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <div class="filters__row">
        <span class="filters__label">作品字数：</span>
        <div class="filters__opts">
          <button
            v-for="opt in wordOptions"
            :key="String(opt.key)"
            class="chip"
            :class="{ 'chip--on': wordRange === opt.key }"
            type="button"
            @click="selectWord(opt.key)"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <div class="filters__row">
        <span class="filters__label">更新时间：</span>
        <div class="filters__opts">
          <button
            v-for="opt in updateOptions"
            :key="String(opt.key)"
            class="chip"
            :class="{ 'chip--on': days === opt.key }"
            type="button"
            @click="selectDays(opt.key)"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <div class="filters__row">
        <span class="filters__label">连载状态：</span>
        <div class="filters__opts">
          <button
            v-for="opt in statusOptions"
            :key="String(opt.key)"
            class="chip"
            :class="{ 'chip--on': status === opt.key }"
            type="button"
            @click="selectStatus(opt.key)"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>
    </section>

    <div class="result-head">
      <h1 class="result-head__title">{{ keyword ? '搜索结果' : '全部作品' }}</h1>
      <span class="result-head__count">共 {{ total }} 本</span>
      <span v-if="activeSummary" class="result-head__summary">{{ activeSummary }}</span>
    </div>

    <div v-if="loading" class="skeleton" style="height: 300px"></div>

    <EmptyState
      v-else-if="!list.length"
      text="没有符合条件的作品，试试放宽筛选"
      action-text="重置筛选"
      to="/search"
    />

    <template v-else>
      <div class="tablewrap">
        <table class="utable">
          <thead>
            <tr>
              <th class="col-cat">分类</th>
              <th>书名</th>
              <th>最新章节</th>
              <th class="col-author">作者</th>
              <th class="col-num">字数</th>
              <th class="col-time">更新时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="book in list" :key="book.id">
              <td class="col-cat">
                <span class="ucat">[{{ book.category?.name }}]</span>
              </td>
              <td>
                <router-link class="ubook" :to="`/book/${book.id}`">{{ book.title }}</router-link>
              </td>
              <td>
                <router-link
                  v-if="book.last_chapter_id"
                  class="uch"
                  :to="`/read/${book.last_chapter_id}`"
                >
                  {{ book.last_chapter_title }}
                </router-link>
                <span v-else class="uch uch--none">暂无章节</span>
              </td>
              <td class="col-author">{{ book.author?.nickname }}</td>
              <td class="col-num">{{ book.word_count }}</td>
              <td class="col-time">{{ (book.last_update_at || '').slice(0, 10) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="pages > 1" class="pager">
        <button class="pager__btn" type="button" :disabled="page <= 1" @click="goPage(page - 1)">
          上一页
        </button>
        <template v-for="(item, index) in pageList" :key="index">
          <span v-if="item === '...'" class="pager__gap">…</span>
          <button
            v-else
            class="pager__num"
            :class="{ 'pager__num--on': item === page }"
            type="button"
            @click="goPage(item)"
          >
            {{ item }}
          </button>
        </template>
        <button class="pager__btn" type="button" :disabled="page >= pages" @click="goPage(page + 1)">
          下一页
        </button>
        <span class="pager__jump">
          跳至
          <input v-model="jumpPage" type="text" @keyup.enter="doJump" />
          页
          <button class="pager__go" type="button" @click="doJump">确定</button>
        </span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.lib {
  padding-top: 20px;
}

/* 筛选面板 */
.filters {
  padding: 8px 20px;
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.filters__row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px dashed #f2f2f2;
}

.filters__row:last-child {
  border-bottom: none;
}

.filters__label {
  width: 76px;
  flex-shrink: 0;
  font-size: 13px;
  color: var(--c-text-secondary);
  line-height: 26px;
}

.filters__opts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  padding: 3px 14px;
  border: 1px solid transparent;
  border-radius: 13px;
  background: transparent;
  font-size: 13px;
  color: var(--c-text-secondary);
  line-height: 20px;
}

.chip:hover {
  color: var(--c-primary);
}

.chip--on {
  background: var(--c-primary);
  border-color: var(--c-primary);
  color: #fff;
}

.chip em {
  margin-left: 4px;
  font-style: normal;
  font-size: 11px;
  opacity: 0.72;
}

/* 结果头 */
.result-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin: 20px 0 12px;
  flex-wrap: wrap;
}

.result-head__title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.result-head__count {
  font-size: 12px;
  color: var(--c-text-muted);
}

.result-head__summary {
  font-size: 12px;
  color: var(--c-primary);
}

/* 表格 */
.tablewrap {
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.utable {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.utable th {
  padding: 12px 14px;
  text-align: left;
  font-weight: 500;
  color: var(--c-text-muted);
  background: #fafafa;
  border-bottom: 1px solid #f2f2f2;
}

.utable td {
  padding: 12px 14px;
  border-bottom: 1px solid #f7f7f7;
  color: var(--c-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.utable tr:last-child td {
  border-bottom: none;
}

.utable tbody tr:hover {
  background: #fffafb;
}

.ucat {
  color: var(--c-primary);
  font-size: 12px;
}

.ubook {
  color: var(--c-text);
  font-weight: 500;
}

.ubook:hover {
  color: var(--c-primary);
}

.uch {
  color: var(--c-text-secondary);
  font-size: 12px;
}

.uch:hover {
  color: var(--c-primary);
}

.uch--none {
  color: var(--c-text-muted);
}

.col-cat {
  width: 110px;
}

.col-author {
  width: 110px;
}

.col-num {
  width: 90px;
  color: var(--c-accent);
}

.col-time {
  width: 110px;
}

/* 分页 */
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin: 24px 0 8px;
  flex-wrap: wrap;
}

.pager__btn,
.pager__num,
.pager__go {
  min-width: 32px;
  height: 30px;
  padding: 0 10px;
  border: 1px solid var(--c-border-strong);
  border-radius: var(--radius-sm);
  background: #fff;
  font-size: 13px;
  color: var(--c-text-secondary);
}

.pager__btn:hover,
.pager__num:hover {
  border-color: var(--c-primary);
  color: var(--c-primary);
}

.pager__num--on {
  background: var(--c-primary);
  border-color: var(--c-primary);
  color: #fff;
}

.pager__btn[disabled] {
  opacity: 0.45;
  cursor: not-allowed;
}

.pager__gap {
  padding: 0 2px;
  color: var(--c-text-muted);
}

.pager__jump {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: 10px;
  font-size: 12px;
  color: var(--c-text-muted);
}

.pager__jump input {
  width: 46px;
  height: 30px;
  padding: 0 6px;
  border: 1px solid var(--c-border-strong);
  border-radius: var(--radius-sm);
  text-align: center;
  font-size: 13px;
}

.pager__go {
  background: var(--c-primary-soft);
  border-color: var(--c-primary-soft);
  color: var(--c-primary);
}

@media (max-width: 768px) {
  .filters__label {
    width: 100%;
    line-height: 1.6;
  }
  .filters__row {
    flex-direction: column;
    gap: 8px;
  }
  .col-author,
  .col-time {
    display: none;
  }
}
</style>