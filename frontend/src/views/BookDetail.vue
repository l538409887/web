<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  addShelf,
  feedWatermelon,
  followAuthor,
  getAuthor,
  getBook,
  getChapters,
  purchaseBook,
  purchaseChapters,
  unfollowAuthor
} from '@/api'
import { confirmDialog } from '@/composables/useConfirm'
import { toast } from '@/utils/toast'
import { useUserStore } from '@/stores/user'
import EmptyState from '@/components/EmptyState.vue'
import CommentSection from '@/components/CommentSection.vue'

const route = useRoute()
const router = useRouter()
const user = useUserStore()

const book = ref(null)
const authorInfo = ref(null)
const following = ref(false)
const chapters = ref([])
const total = ref(0)
const expanded = ref(false)
const loading = ref(true)
const failed = ref(false)
const buying = ref(false)
const feeding = ref(false)

const shownChapters = computed(() => (expanded.value ? chapters.value : chapters.value.slice(0, 20)))

const FREE_PREVIEW = 3

const subOpen = ref(false)
const selected = ref([])
const latestCount = ref(10)
const paying = ref(false)

// 可订阅 = 付费作品中「第 4 章之后」且「当前未解锁」的章节
const purchasable = computed(() =>
  chapters.value.filter((c) => c.chapter_no > FREE_PREVIEW && c.locked)
)

const isAllSelected = computed(
  () => purchasable.value.length > 0 && selected.value.length === purchasable.value.length
)

const selectedSum = computed(() =>
  purchasable.value
    .filter((c) => selected.value.includes(c.id))
    .reduce((sum, c) => sum + (c.price_coin || 0), 0)
)

const paidAmount = computed(() =>
  chapters.value
    .filter((c) => !c.locked && c.chapter_no > FREE_PREVIEW)
    .reduce((sum, c) => sum + (c.price_coin || 0), 0)
)

const wholePrice = computed(() =>
  Math.max(0, (book.value?.price_coin || 0) - paidAmount.value)
)

// 全选时按整本价结算，比逐章相加便宜
const totalCoin = computed(() => (isAllSelected.value ? wholePrice.value : selectedSum.value))

function openSubscribe() {
  if (!user.isLogin) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  selected.value = []
  subOpen.value = true
}

function selectAll() {
  selected.value = purchasable.value.map((c) => c.id)
}

function clearAll() {
  selected.value = []
}

function selectLatest() {
  const count = Math.max(1, Number(latestCount.value) || 1)
  const newest = [...purchasable.value].sort((a, b) => b.chapter_no - a.chapter_no)
  selected.value = newest.slice(0, count).map((c) => c.id)
}

async function confirmSubscribe() {
  if (!selected.value.length) return
  const ids = [...selected.value]
  const useWhole = isAllSelected.value
  const confirmed = await confirmDialog({
    title: useWhole ? '订阅整本？' : `订阅 ${ids.length} 章？`,
    message: `将扣除 ${totalCoin.value} 软妹币，订阅后永久可读。`,
    confirmText: '确认订阅',
    danger: false
  })
  if (!confirmed) return

  paying.value = true
  try {
    if (useWhole) {
      await purchaseBook(book.value.id)
      book.value.is_purchased = true
      chapters.value = chapters.value.map((c) => ({ ...c, locked: false }))
    } else {
      await purchaseChapters(book.value.id, ids)
      const bought = new Set(ids)
      chapters.value = chapters.value.map((c) =>
        bought.has(c.id) ? { ...c, locked: false } : c
      )
    }
    selected.value = []
    subOpen.value = false
    toast('订阅成功')
  } catch {
    /* 拦截器已提示 */
  } finally {
    paying.value = false
  }
}

const firstChapterId = computed(() => chapters.value[0]?.id || null)
const startChapterId = computed(() => book.value?.last_chapter_id || firstChapterId.value)

async function load() {
  loading.value = true
  failed.value = false
  try {
    const [detail, chapterPage] = await Promise.all([
      getBook(route.params.id),
      getChapters(route.params.id, { size: 500 })
    ])
    book.value = detail
    chapters.value = chapterPage.list
    total.value = chapterPage.total

    if (detail.author?.id) {
      try {
        authorInfo.value = await getAuthor(detail.author.id)
        following.value = Boolean(authorInfo.value.is_followed)
      } catch {
        authorInfo.value = null
      }
    }
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

function startRead() {
  if (!startChapterId.value) {
    toast('这本书还没有章节')
    return
  }
  router.push(`/read/${startChapterId.value}`)
}

async function onAddShelf() {
  if (!user.isLogin) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  if (book.value.is_collected) return
  try {
    await addShelf(book.value.id)
    book.value.is_collected = true
    toast('已加入书架')
  } catch {
    book.value.is_collected = true
  }
}

async function onPurchase() {
  if (!user.isLogin) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  const confirmed = await confirmDialog({
    title: '购买这本书？',
    message: `将扣除 ${book.value.price_coin} 软妹币，购买后可阅读全部章节。`,
    confirmText: '购买',
    danger: false
  })
  if (!confirmed) return
  buying.value = true
  try {
    const res = await purchaseBook(book.value.id)
    book.value.is_purchased = true
    chapters.value = chapters.value.map((c) => ({ ...c, locked: false }))
    toast(`购买成功，扣除 ${res.coin} 软妹币`)
  } catch {
    /* 拦截器已提示 */
  } finally {
    buying.value = false
  }
}

async function toggleFollow() {
  if (!user.isLogin) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  const id = book.value.author?.id
  if (!id) return
  try {
    if (following.value) {
      await unfollowAuthor(id)
      following.value = false
      toast('已取消关注')
    } else {
      await followAuthor(id)
      following.value = true
      toast('关注成功，可在个人中心查看')
    }
  } catch {
    /* 拦截器已提示 */
  }
}

async function onFeed() {
  if (!user.isLogin) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  feeding.value = true
  try {
    const res = await feedWatermelon(book.value.id, 1)
    book.value.watermelon_count = res.book_watermelon
    toast(
      `投喂成功，剩余西瓜 ${res.watermelon_left} 个 · 今天还能喂 ${res.remain_today} 个`
    )
  } catch {
    /* 拦截器已提示 */
  } finally {
    feeding.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="container">
    <div v-if="loading" class="skeleton" style="height: 260px; margin: 28px 0"></div>
    <EmptyState v-else-if="failed" text="书籍不存在或已下架" action-text="回首页" to="/" />

    <template v-else-if="book">
      <section class="detail">
        <div class="detail__cover">
          <img v-if="book.cover" :src="book.cover" :alt="book.title" />
          <span v-else class="detail__initial">{{ book.title.slice(0, 2) }}</span>
        </div>

        <div class="detail__info">
          <h1 class="detail__title">
            {{ book.title }}
            <span class="tag" :class="{ 'tag--done': book.status === 1 }">
              {{ book.status === 1 ? '已完结' : '连载中' }}
            </span>
            <span v-if="book.is_paid" class="tag tag--paid">
              {{ book.is_purchased ? '已购买' : `付费 · ${book.price_coin} 软妹币` }}
            </span>
          </h1>
          <p class="detail__meta">
            <router-link class="detail__author" :to="`/author/${book.author?.id}`">
              {{ book.author?.nickname }}
            </router-link>
            <button class="detail__follow" type="button" @click="toggleFollow">
              {{ following ? '已关注' : '+ 关注' }}
            </button>
            · {{ book.category?.name }} · {{ book.word_count }} 字 ·
            {{ book.chapter_count }} 章
          </p>
          <div class="detail__tags">
            <span v-for="tag in book.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>
          <p class="detail__stat">
            评分 {{ book.score }} · 收藏 {{ book.collect_count }} · 点击 {{ book.click_count }}
          </p>
          <div class="detail__actions">
            <button class="btn btn--primary" type="button" @click="startRead">开始阅读</button>
            <button
              class="btn"
              :class="{ 'btn--accent': !book.is_collected }"
              type="button"
              :disabled="book.is_collected"
              @click="onAddShelf"
            >
              {{ book.is_collected ? '已在书架' : '加入书架' }}
            </button>
            <button
              v-if="book.is_paid && !book.is_purchased"
              class="btn btn--buy"
              type="button"
              @click="openSubscribe"
            >
              订阅
            </button>
            <button class="btn btn--feed" type="button" :disabled="feeding" @click="onFeed">
              🍉 投喂 {{ book.watermelon_count || 0 }}
            </button>
          </div>
        </div>
      </section>

      <section class="block">
        <h2 class="section__title">简介</h2>
        <p class="intro">{{ book.intro }}</p>
      </section>

      <section class="block">
        <div class="section__head">
          <h2 class="section__title">目录</h2>
          <span class="section__sub">
            <em v-if="book.is_paid && !book.is_purchased" class="payhint">
              付费作品 · 前 {{ FREE_PREVIEW }} 章可免费试读
            </em>
            共 {{ total }} 章
            <a v-if="chapters.length > 20" class="expand" href="#" @click.prevent="expanded = !expanded">
              {{ expanded ? '收起' : '查看全部' }}
            </a>
          </span>
        </div>
        <ul class="chapters">
          <li
            v-for="chapter in shownChapters"
            :key="chapter.id"
            class="chapters__item"
            :class="{ 'chapters__item--locked': chapter.locked }"
          >
            <router-link
              :to="`/read/${chapter.id}`"
              :class="{ 'chapters__lock': chapter.locked }"
            >
              {{ chapter.title }}
              <span v-if="chapter.locked" class="chapters__icon">🔒</span>
            </router-link>
          </li>
        </ul>
      </section>

      <CommentSection :book-id="book.id" />
    </template>
  </div>

  <Teleport to="body">
    <div v-if="subOpen" class="sub-mask" @click.self="subOpen = false">
      <div class="sub">
        <header class="sub__head">
          <div>
            <p class="sub__title">订阅《{{ book?.title }}》</p>
            <p class="sub__desc">
              前 {{ FREE_PREVIEW }} 章免费，其余每千字 5 软妹币
            </p>
          </div>
          <button class="sub__close" type="button" @click="subOpen = false">✕</button>
        </header>

        <div class="sub__tools">
          <button class="sub__tool" type="button" @click="selectAll">全选</button>
          <button class="sub__tool" type="button" @click="clearAll">清空</button>
          <span class="sub__latest">
            订阅最新
            <input
              v-model="latestCount"
              type="number"
              min="1"
              :max="purchasable.length || 1"
            />
            章
            <button class="sub__apply" type="button" @click="selectLatest">应用</button>
          </span>
        </div>

        <div class="sub__list">
          <label
            v-for="chapter in purchasable"
            :key="chapter.id"
            class="sub__item"
            :class="{ 'sub__item--on': selected.includes(chapter.id) }"
          >
            <input v-model="selected" type="checkbox" :value="chapter.id" />
            <span class="sub__no">第 {{ chapter.chapter_no }} 章</span>
            <span class="sub__name">{{ chapter.title }}</span>
            <span class="sub__price">{{ chapter.price_coin }} 软妹币</span>
          </label>
          <p v-if="!purchasable.length" class="sub__empty">所有章节都已订阅</p>
        </div>

        <footer class="sub__foot">
          <div class="sub__sum">
            已选 <b>{{ selected.length }}</b> 章 · 合计
            <em>{{ totalCoin }}</em> 软妹币
            <span v-if="isAllSelected" class="sub__badge">全选享整本价</span>
          </div>
          <button
            class="btn btn--buy"
            type="button"
            :disabled="!selected.length || paying"
            @click="confirmSubscribe"
          >
            {{ paying ? '处理中…' : '确认订阅' }}
          </button>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.detail {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 32px;
  margin: 32px 0;
  padding: 28px;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
}

.detail__cover {
  aspect-ratio: 3 / 4;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--c-primary), #d93e73);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-card);
}

.detail__initial {
  font-size: 38px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.92);
  letter-spacing: 3px;
  font-family: 'Songti SC', 'Noto Serif SC', serif;
}

.detail__title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 10px;
  font-size: 26px;
}

.detail__meta {
  margin: 0 0 12px;
  color: var(--c-text-secondary);
  font-size: 13px;
}

.detail__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.detail__stat {
  margin: 0 0 20px;
  font-size: 13px;
  color: var(--c-text-muted);
}

.detail__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.btn--buy {
  background: var(--c-accent);
  border-color: var(--c-accent);
  color: #fff;
}

.btn--buy:hover {
  background: var(--c-accent-light);
  border-color: var(--c-accent-light);
  color: #fff;
}

.btn--feed:hover {
  border-color: var(--c-primary);
  color: var(--c-primary);
}

.detail__author {
  color: var(--c-primary);
}

.detail__author:hover {
  text-decoration: underline;
}

.detail__follow {
  margin: 0 6px;
  padding: 1px 9px;
  border: 1px solid var(--c-primary);
  border-radius: 10px;
  background: transparent;
  font-size: 11px;
  color: var(--c-primary);
  vertical-align: 1px;
}

.detail__follow:hover {
  background: var(--c-primary);
  color: #fff;
}

.tag--paid {
  background: #fff4e6;
  color: var(--c-accent);
}

.block {
  margin: 28px 0;
}

.intro {
  margin: 0;
  padding: 20px;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  color: var(--c-text-secondary);
  line-height: 1.9;
  white-space: pre-wrap;
}

.expand {
  margin-left: 10px;
  color: var(--c-primary);
}

.chapters {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 2px 16px;
  margin: 0;
  padding: 8px 16px;
  list-style: none;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  max-height: 520px;
  overflow-y: auto;
}

/* ---------- 订阅弹窗 ---------- */
.sub-mask {
  position: fixed;
  inset: 0;
  z-index: 400;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(0, 0, 0, 0.45);
}

.sub {
  display: flex;
  flex-direction: column;
  width: 560px;
  max-width: 100%;
  max-height: 86vh;
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.22);
  overflow: hidden;
}

.sub__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 20px 14px;
  border-bottom: 1px solid #f2f2f2;
}

.sub__title {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
}

.sub__desc {
  margin: 0;
  font-size: 12px;
  color: var(--c-text-muted);
}

.sub__close {
  border: none;
  background: transparent;
  font-size: 16px;
  color: #999;
  line-height: 1;
}

.sub__tools {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  background: #fffafb;
  border-bottom: 1px solid #f6eef1;
}

.sub__tool {
  padding: 4px 12px;
  border: 1px solid var(--c-border-strong);
  border-radius: 14px;
  background: #fff;
  font-size: 12px;
  color: var(--c-text-secondary);
}

.sub__tool:hover {
  border-color: var(--c-primary);
  color: var(--c-primary);
}

.sub__latest {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--c-text-secondary);
}

.sub__latest input {
  width: 54px;
  height: 26px;
  padding: 0 6px;
  border: 1px solid var(--c-border-strong);
  border-radius: var(--radius-sm);
  text-align: center;
  font-size: 12px;
}

.sub__apply {
  padding: 4px 12px;
  border: none;
  border-radius: 14px;
  background: var(--c-primary);
  color: #fff;
  font-size: 12px;
}

.sub__list {
  flex: 1;
  overflow-y: auto;
  padding: 6px 12px;
}

.sub__item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  border-bottom: 1px dashed #f5f5f5;
}

.sub__item:hover {
  background: #fffafb;
}

.sub__item--on {
  background: var(--c-primary-soft);
}

.sub__item input {
  flex-shrink: 0;
  accent-color: var(--c-primary);
}

.sub__no {
  flex-shrink: 0;
  width: 70px;
  font-size: 12px;
  color: var(--c-text-muted);
}

.sub__name {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  color: var(--c-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sub__price {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--c-accent);
}

.sub__empty {
  margin: 40px 0;
  text-align: center;
  font-size: 13px;
  color: var(--c-text-muted);
}

.sub__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 20px;
  border-top: 1px solid #f2f2f2;
}

.sub__sum {
  font-size: 13px;
  color: var(--c-text-secondary);
}

.sub__sum em {
  font-style: normal;
  font-size: 17px;
  font-weight: 700;
  color: var(--c-accent);
}

.sub__badge {
  margin-left: 8px;
  padding: 1px 7px;
  border-radius: 3px;
  background: #fff4e6;
  color: var(--c-accent);
  font-size: 11px;
}

.chapters__item--locked {
  background: #fcfcfc;
}

.chapters__item {
  border-bottom: 1px dashed var(--c-border);
}

.payhint {
  margin-right: 10px;
  padding: 1px 8px;
  border-radius: 3px;
  background: #fff4e6;
  color: var(--c-accent);
  font-style: normal;
  font-size: 11px;
}

.chapters__icon {
  margin-left: 4px;
  font-size: 11px;
  opacity: 0.7;
}

.chapters__lock {
  color: var(--c-text-muted) !important;
}

.chapters__item a {
  display: block;
  padding: 9px 0;
  font-size: 14px;
  color: var(--c-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chapters__item a:hover {
  color: var(--c-primary);
}

@media (max-width: 768px) {
  .detail {
    grid-template-columns: 120px 1fr;
    gap: 18px;
    padding: 18px;
  }
  .detail__title {
    font-size: 20px;
  }
  .chapters {
    grid-template-columns: 1fr;
  }
}
</style>
