<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getBooks, getHome, getNotices } from '@/api'
import BookCard from '@/components/BookCard.vue'
import HomeCarousel from '@/components/HomeCarousel.vue'
import HomeRankPanel from '@/components/HomeRankPanel.vue'
import SectionStrip from '@/components/SectionStrip.vue'
import NoticePanel from '@/components/NoticePanel.vue'
import EmptyState from '@/components/EmptyState.vue'
import logo from '@/assets/logo.png'

const route = useRoute()

const loading = ref(true)
const home = ref(null)
const results = ref(null)
const active = ref(0)

const keyword = computed(() => (route.query.keyword || '').toString())

const banners = computed(() => home.value?.banners || [])
const notices = computed(() => home.value?.notices || [])
const sections = computed(() => home.value?.sections || {})
const featured = computed(() => sections.value.featured || [])
const choicest = computed(() => sections.value.choicest || [])
const rising = computed(() => sections.value.rising || [])

const current = computed(() => featured.value[active.value] || featured.value[0] || null)

const choicestCards = computed(() => choicest.value.slice(0, 3))
const choicestGrid = computed(() => choicest.value.slice(3, 11))

const clickRank = computed(() => home.value?.ranks?.click || [])
const subscribeRank = computed(() => home.value?.ranks?.subscribe || [])
const newRank = computed(() => home.value?.ranks?.new || [])

function formatCount(value) {
  const num = Number(value || 0)
  if (num >= 10000) return `${(num / 10000).toFixed(1)}万`
  return String(num)
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

// 扇形堆叠：离当前选中越远，越小、越倾斜、越靠后
function fanStyle(index) {
  const offset = index - active.value
  const abs = Math.abs(offset)
  return {
    transform: `translate(calc(-50% + ${offset * 58}px), ${abs * 10}px) rotate(${offset * 5}deg) scale(${1 - abs * 0.09})`,
    zIndex: 20 - abs,
    opacity: abs > 2 ? 0 : 1
  }
}

async function load() {
  loading.value = true
  try {
    if (keyword.value) {
      results.value = await getBooks({ keyword: keyword.value, page: 1, size: 20 })
      home.value = null
    } else {
      const [homeData, noticeList] = await Promise.all([getHome(), getNotices(5)])
      home.value = { ...homeData, notices: noticeList }
      results.value = null
      active.value = 0
    }
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

watch(() => route.query.keyword, load, { immediate: true })
</script>

<template>
  <div class="container home">
    <div v-if="loading" class="home__loading">
      <div class="skeleton" style="height: 340px"></div>
      <div class="skeleton" style="height: 220px; margin-top: 20px"></div>
    </div>

    <template v-else-if="keyword">
      <div class="result-head">
        <h2 class="result-head__title">搜索「{{ keyword }}」</h2>
        <span class="result-head__count">共 {{ results?.total || 0 }} 本</span>
      </div>
      <div v-if="results?.list?.length" class="grid-books">
        <BookCard v-for="item in results.list" :key="item.id" :book="item" show-meta />
      </div>
      <EmptyState v-else text="没有找到相关书籍，换个关键词试试" action-text="回首页" to="/" />
    </template>

    <template v-else-if="home">
      <section class="hero">
        <HomeCarousel :items="banners" />
        <NoticePanel :items="notices" />
      </section>

      <!-- 好书精选 -->
      <section class="row">
        <div class="row__main">
          <div class="sec__head">
            <img class="sec__icon" :src="logo" alt="" />
            <h2 class="sec__title">好书精选</h2>
            <span class="sec__sub">编辑逐本读过才放上来</span>
            <router-link class="sec__more" :to="{ path: '/search', query: { sort: 'collect' } }">
              更多 ›
            </router-link>
          </div>

          <div v-if="current" class="showcase">
            <div class="showcase__stage">
              <button
                v-for="(book, index) in featured"
                :key="book.id"
                class="showcase__cover"
                :style="[coverStyle(book), fanStyle(index)]"
                type="button"
                @click="active = index"
              >
                <img v-if="book.cover" :src="book.cover" :alt="book.title" />
                <span v-else>{{ book.title.slice(0, 2) }}</span>
              </button>
            </div>

            <div class="showcase__info">
              <h3 class="showcase__title">{{ current.title }}</h3>
              <p class="showcase__author">{{ current.author?.nickname }} 著</p>
              <p class="showcase__intro">{{ current.intro }}</p>
              <div class="showcase__foot">
                <router-link class="btn btn--primary" :to="`/book/${current.id}`">
                  书籍详情
                </router-link>
                <span class="showcase__meta">
                  {{ current.category?.name }} · {{ formatCount(current.word_count) }} 字
                </span>
              </div>
              <div class="showcase__dots">
                <button
                  v-for="(book, index) in featured"
                  :key="book.id"
                  class="showcase__dot"
                  :class="{ 'showcase__dot--on': active === index }"
                  type="button"
                  @click="active = index"
                ></button>
              </div>
            </div>
          </div>

          <div class="hcards">
            <router-link
              v-for="book in choicestCards"
              :key="book.id"
              class="hcard"
              :to="`/book/${book.id}`"
            >
              <div class="hcard__cover" :style="coverStyle(book)">
                <img v-if="book.cover" :src="book.cover" :alt="book.title" />
                <span v-else class="hcard__init">{{ book.title.slice(0, 2) }}</span>
              </div>
              <div class="hcard__info">
                <h3 class="hcard__title">{{ book.title }}</h3>
                <p class="hcard__author">{{ book.author?.nickname }} 著</p>
                <p class="hcard__intro">{{ book.intro }}</p>
                <span class="hcard__read">立即阅读 ›</span>
              </div>
            </router-link>
          </div>
        </div>

        <HomeRankPanel
          title="周点击榜"
          subtitle="本书周人气"
          :items="clickRank"
          field="click_count"
        />
      </section>

      <SectionStrip title="本周力推" subtitle="编辑逐本读过，才敢放上来" art="/banners/b4.jpg" />

      <!-- 精品力荐 -->
      <section class="row">
        <div class="row__main">
          <div class="sec__head">
            <img class="sec__icon" :src="logo" alt="" />
            <h2 class="sec__title">精品力荐</h2>
            <span class="sec__sub">被最多人收进书架的作品</span>
            <router-link class="sec__more" :to="{ path: '/search', query: { sort: 'collect' } }">
              更多 ›
            </router-link>
          </div>

          <div class="grid4">
            <router-link
              v-for="book in choicestGrid"
              :key="book.id"
              class="gcard"
              :to="`/book/${book.id}`"
            >
              <div class="gcard__cover" :style="coverStyle(book)">
                <img v-if="book.cover" :src="book.cover" :alt="book.title" />
                <span v-else>{{ book.title.slice(0, 2) }}</span>
              </div>
              <p class="gcard__title">{{ book.title }}</p>
              <p class="gcard__meta">
                {{ formatCount(book.word_count) }} 字 | {{ book.category?.name }}
              </p>
            </router-link>
          </div>
        </div>

        <HomeRankPanel
          title="订阅榜"
          subtitle="付费作品收入"
          :items="subscribeRank"
          field="revenue_coin"
        />
      </section>

      <SectionStrip title="新书上架" subtitle="每天都有新的故事开始" art="/banners/b5.jpg" />

      <!-- 新秀小说 -->
      <section class="row">
        <div class="row__main">
          <div class="sec__head">
            <img class="sec__icon" :src="logo" alt="" />
            <h2 class="sec__title">新秀小说</h2>
            <span class="sec__sub">刚上架的新作品</span>
            <router-link class="sec__more" :to="{ path: '/search', query: { sort: 'new' } }">
              更多 ›
            </router-link>
          </div>

          <div class="grid6">
            <router-link
              v-for="book in rising"
              :key="book.id"
              class="gcard gcard--sm"
              :to="`/book/${book.id}`"
            >
              <div class="gcard__cover" :style="coverStyle(book)">
                <img v-if="book.cover" :src="book.cover" :alt="book.title" />
                <span v-else>{{ book.title.slice(0, 2) }}</span>
              </div>
              <p class="gcard__title">{{ book.title }}</p>
              <p class="gcard__meta">
                {{ formatCount(book.word_count) }} 字 | {{ book.category?.name }}
              </p>
            </router-link>
          </div>
        </div>

        <HomeRankPanel
          title="新书榜"
          subtitle="最新上架"
          :items="newRank"
          field="created_at"
          time
        />
      </section>

      <!-- 最近更新 -->
      <section class="sec">
        <div class="sec__head">
          <h2 class="sec__title">最近更新</h2>
          <span class="sec__sub">按更新时间排序</span>
          <router-link class="sec__more" to="/rank">更多 ›</router-link>
        </div>

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
              <tr v-for="book in home.latest" :key="book.id">
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
      </section>
    </template>
  </div>
</template>

<style scoped>
.home {
  padding-top: 20px;
}

.result-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin: 8px 0 18px;
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

/* ---------- 首屏：轮播 + 资讯栏 ---------- */
.hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
  align-items: stretch;
}

/* ---------- 区块行：左侧内容 + 右侧榜单 ---------- */
.row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
  margin-top: 26px;
  align-items: start;
}

.sec__head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.sec__icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
}

.sec__title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
}

.sec__sub {
  font-size: 12px;
  color: var(--c-text-muted);
}

.sec__more {
  margin-left: auto;
  padding: 3px 10px;
  border: 1px solid var(--c-border-strong);
  border-radius: 4px;
  font-size: 12px;
  color: var(--c-text-secondary);
}

.sec__more:hover {
  border-color: var(--c-primary);
  color: var(--c-primary);
}

/* ---------- 扇形轮展 ---------- */
.showcase {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 24px 20px;
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.showcase__stage {
  position: relative;
  height: 250px;
}

.showcase__cover {
  position: absolute;
  left: 50%;
  bottom: 12px;
  width: 128px;
  height: 178px;
  padding: 0;
  border: none;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.22);
  transition: transform 0.36s cubic-bezier(0.22, 0.61, 0.36, 1), opacity 0.3s ease;
  transform-origin: bottom center;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 2px;
  color: rgba(255, 255, 255, 0.92);
  font-family: 'Songti SC', 'Noto Serif SC', serif;
}

.showcase__cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.showcase__info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.showcase__title {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 700;
  line-height: 1.4;
}

.showcase__author {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--c-primary);
}

.showcase__intro {
  margin: 0 0 18px;
  font-size: 13px;
  line-height: 1.9;
  color: var(--c-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.showcase__foot {
  display: flex;
  align-items: center;
  gap: 14px;
}

.showcase__meta {
  font-size: 12px;
  color: var(--c-text-muted);
}

.showcase__dots {
  display: flex;
  gap: 7px;
  margin-top: 20px;
}

.showcase__dot {
  width: 7px;
  height: 7px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: #e6e6e6;
}

.showcase__dot--on {
  width: 18px;
  border-radius: 4px;
  background: var(--c-primary);
}

/* ---------- 横向小卡 ---------- */
.hcards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 14px;
}

.hcard {
  display: flex;
  gap: 12px;
  padding: 14px;
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  transition: box-shadow 0.16s ease, transform 0.16s ease;
}

.hcard:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover);
}

.hcard__cover {
  width: 76px;
  height: 102px;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hcard__cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hcard__init {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 2px;
  color: rgba(255, 255, 255, 0.92);
  font-family: 'Songti SC', 'Noto Serif SC', serif;
}

.hcard__info {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.hcard__title {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hcard:hover .hcard__title {
  color: var(--c-primary);
}

.hcard__author {
  margin: 0 0 6px;
  font-size: 12px;
  color: var(--c-primary);
}

.hcard__intro {
  margin: 0 0 8px;
  font-size: 12px;
  line-height: 1.75;
  color: var(--c-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hcard__read {
  margin-top: auto;
  font-size: 12px;
  color: var(--c-accent);
}

/* ---------- 封面网格 ---------- */
.grid4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 16px;
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.grid6 {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  padding: 16px;
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.gcard {
  display: block;
  min-width: 0;
}

.gcard__cover {
  width: 100%;
  aspect-ratio: 3 / 4;
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
  transition: transform 0.18s ease;
}

.gcard:hover .gcard__cover {
  transform: translateY(-3px);
}

.gcard__cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.gcard__title {
  margin: 8px 0 4px;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.gcard:hover .gcard__title {
  color: var(--c-primary);
}

.gcard__meta {
  margin: 0;
  font-size: 11px;
  color: var(--c-text-muted);
}

.gcard--sm .gcard__title {
  font-size: 12px;
}

/* ---------- 最近更新 ---------- */
.sec {
  margin-top: 26px;
}

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
  padding: 11px 14px;
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

@media (max-width: 1200px) {
  .grid6 {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 1100px) {
  .hero {
    grid-template-columns: 1fr;
  }
  .row {
    grid-template-columns: 1fr;
  }
  .hcards {
    grid-template-columns: repeat(2, 1fr);
  }
  .showcase {
    grid-template-columns: 1fr;
  }
  .showcase__stage {
    height: 210px;
  }
}

@media (max-width: 768px) {
  .hcards,
  .grid4 {
    grid-template-columns: repeat(2, 1fr);
  }
  .grid6 {
    grid-template-columns: repeat(3, 1fr);
  }
  .col-author,
  .col-time {
    display: none;
  }
  .sec__sub {
    display: none;
  }
}
</style>
