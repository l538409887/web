<script setup>
import { onMounted, ref } from 'vue'
import { getBooks, getMonthlyRank } from '@/api'
import EmptyState from '@/components/EmptyState.vue'

const loading = ref(true)
const active = ref('click')

const defs = [
  { key: 'click', label: '点击榜', field: 'click_count', tip: '累计点击量' },
  { key: 'collect', label: '收藏榜', field: 'collect_count', tip: '被加入书架次数' },
  { key: 'watermelon', label: '推荐榜', field: 'watermelon_count', tip: '读者投喂西瓜数' },
  { key: 'subscribe', label: '订阅榜', field: 'revenue_coin', tip: '付费作品累计收入（软妹币）' },
  { key: 'comment', label: '吐槽榜', field: 'paragraph_comment_count', tip: '间贴（段落评论）总数' },
  { key: 'new', label: '新书榜', field: null, tip: '最近上架作品' }
]

const ranks = ref({})
const monthly = ref([])

function formatCount(value) {
  const num = Number(value || 0)
  if (num >= 10000) return `${(num / 10000).toFixed(1)}万`
  return String(num)
}

function metric(book, def) {
  if (!def.field) return (book.last_update_at || '').slice(0, 10)
  return formatCount(book[def.field])
}

function hueOf(text) {
  let h = 7
  for (const ch of text || '') h = (h * 31 + ch.charCodeAt(0)) % 360
  return h
}

function coverStyle(book) {
  const h = hueOf(book.title)
  return {
    background: `linear-gradient(140deg, hsl(${h}, 40%, 52%), hsl(${(h + 40) % 360}, 42%, 36%))`
  }
}

function scrollTo(key) {
  active.value = key
  const el = document.getElementById(`rank-${key}`)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

onMounted(async () => {
  loading.value = true
  try {
    const results = await Promise.all([
      ...defs.map((def) => getBooks({ sort: def.key, page: 1, size: 10 })),
      getMonthlyRank(10)
    ])
    const map = {}
    defs.forEach((def, index) => {
      map[def.key] = results[index].list
    })
    ranks.value = map
    monthly.value = results[defs.length] || []
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="container rank">
    <div v-if="loading" class="skeleton" style="height: 420px; margin-top: 20px"></div>

    <div v-else class="rank__layout">
      <aside class="rank__side">
        <h2 class="rank__side-title">小说排行榜</h2>
        <nav class="rank__nav">
          <router-link
            v-for="def in defs"
            :key="def.key"
            class="rank__navitem"
            :to="`/rank/${def.key}`"
          >
            {{ def.label }}
          </router-link>
          <router-link class="rank__navitem" to="/rank/monthly">更新榜</router-link>
        </nav>
        <p class="rank__note">
          点击榜单名查看完整名单；列表为总榜，按累计数据排序。
        </p>
      </aside>

      <div class="rank__grid">
        <section
          v-for="def in defs"
          :id="`rank-${def.key}`"
          :key="def.key"
          class="rcard"
        >
          <div class="rcard__head">
            <h3 class="rcard__title">{{ def.label }}</h3>
            <router-link class="rcard__more" :to="`/rank/${def.key}`">完整榜单 ›</router-link>
          </div>

          <template v-if="(ranks[def.key] || []).length">
            <div class="no1">
              <div class="no1__info">
                <span class="no1__badge">NO.1</span>
                <router-link class="no1__title" :to="`/book/${ranks[def.key][0].id}`">
                  {{ ranks[def.key][0].title }}
                </router-link>
                <p class="no1__author">{{ ranks[def.key][0].author?.nickname }}</p>
                <p class="no1__val">{{ metric(ranks[def.key][0], def) }}</p>
              </div>
              <router-link
                class="no1__cover"
                :style="coverStyle(ranks[def.key][0])"
                :to="`/book/${ranks[def.key][0].id}`"
              >
                <img
                  v-if="ranks[def.key][0].cover"
                  :src="ranks[def.key][0].cover"
                  :alt="ranks[def.key][0].title"
                />
                <span v-else>{{ ranks[def.key][0].title.slice(0, 2) }}</span>
              </router-link>
            </div>

            <ol class="rlist">
              <li
                v-for="(book, index) in ranks[def.key].slice(1)"
                :key="book.id"
                class="rlist__item"
              >
                <span class="rlist__idx">{{ index + 2 }}</span>
                <span class="rlist__cat">[{{ book.category?.name }}]</span>
                <router-link class="rlist__name" :to="`/book/${book.id}`">
                  {{ book.title }}
                </router-link>
                <span class="rlist__val">{{ metric(book, def) }}</span>
              </li>
            </ol>
          </template>

          <EmptyState v-else text="暂无数据" />
        </section>

        <!-- 更新榜 -->
        <section id="rank-monthly" class="rcard">
          <div class="rcard__head">
            <h3 class="rcard__title">更新榜</h3>
            <router-link class="rcard__more" to="/rank/monthly">完整榜单 ›</router-link>
          </div>

          <template v-if="monthly.length">
            <div class="no1">
              <div class="no1__info">
                <span class="no1__badge">NO.1</span>
                <router-link class="no1__title" :to="`/book/${monthly[0].book.id}`">
                  {{ monthly[0].book.title }}
                </router-link>
                <p class="no1__author">{{ monthly[0].book.author?.nickname }}</p>
                <p class="no1__val">{{ monthly[0].words }} 字</p>
              </div>
              <router-link
                class="no1__cover"
                :style="coverStyle(monthly[0].book)"
                :to="`/book/${monthly[0].book.id}`"
              >
                <img
                  v-if="monthly[0].book.cover"
                  :src="monthly[0].book.cover"
                  :alt="monthly[0].book.title"
                />
                <span v-else>{{ monthly[0].book.title.slice(0, 2) }}</span>
              </router-link>
            </div>

            <ol class="rlist">
              <li v-for="item in monthly.slice(1)" :key="item.book.id" class="rlist__item">
                <span class="rlist__idx">{{ item.rank }}</span>
                <span class="rlist__cat">[{{ item.book.category?.name }}]</span>
                <router-link class="rlist__name" :to="`/book/${item.book.id}`">
                  {{ item.book.title }}
                </router-link>
                <span class="rlist__val">{{ formatCount(item.words) }}</span>
              </li>
            </ol>
          </template>

          <EmptyState v-else text="本月还没有更新" />
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rank {
  padding-top: 20px;
}

.rank__layout {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 20px;
}

.rank__side {
  position: sticky;
  top: 130px;
  align-self: start;
  padding: 16px 0;
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.rank__side-title {
  margin: 0 16px 12px;
  font-size: 16px;
  font-weight: 600;
}

.rank__nav {
  display: flex;
  flex-direction: column;
}

.rank__navitem {
  padding: 11px 16px;
  font-size: 14px;
  color: var(--c-text-secondary);
  border-left: 3px solid transparent;
}

.rank__navitem:hover {
  color: var(--c-primary);
  background: #fffafb;
}

.rank__navitem--on {
  color: var(--c-primary);
  font-weight: 600;
  border-left-color: var(--c-primary);
  background: var(--c-primary-soft);
}

.rank__note {
  margin: 14px 16px 0;
  padding-top: 12px;
  border-top: 1px dashed var(--c-border);
  font-size: 12px;
  line-height: 1.7;
  color: var(--c-text-muted);
}

.rank__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  align-content: start;
}

.rcard {
  padding: 18px;
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  scroll-margin-top: 130px;
}

.rcard__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 14px;
}

.rcard__title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  white-space: nowrap;
}

.rcard__more {
  font-size: 12px;
  color: var(--c-text-muted);
  white-space: nowrap;
}

.rcard__more:hover {
  color: var(--c-primary);
}

.rcard__tag {
  font-size: 11px;
  color: var(--c-text-muted);
  text-align: right;
}

.no1 {
  display: flex;
  gap: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid #f2f2f2;
}

.no1__info {
  flex: 1;
  min-width: 0;
}

.no1__badge {
  display: inline-block;
  padding: 0 8px;
  border-radius: 3px;
  background: var(--c-primary);
  color: #fff;
  font-size: 11px;
  line-height: 19px;
  font-weight: 600;
}

.no1__title {
  margin: 8px 0 4px;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.no1__title:hover {
  color: var(--c-primary);
}

.no1__author {
  margin: 0;
  font-size: 12px;
  color: var(--c-text-muted);
}

.no1__val {
  margin: 8px 0 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--c-primary);
}

.no1__cover {
  width: 62px;
  height: 84px;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 1px;
  color: rgba(255, 255, 255, 0.92);
  font-family: 'Songti SC', 'Noto Serif SC', serif;
}

.no1__cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.rlist {
  margin: 0;
  padding: 6px 0 0;
  list-style: none;
}

.rlist__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 0;
  border-bottom: 1px dashed #f4f4f4;
}

.rlist__item:last-child {
  border-bottom: none;
}

.rlist__idx {
  width: 16px;
  font-size: 12px;
  color: var(--c-text-muted);
  font-weight: 600;
  flex-shrink: 0;
}

.rlist__cat {
  font-size: 12px;
  color: var(--c-primary);
  flex-shrink: 0;
}

.rlist__name {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rlist__name:hover {
  color: var(--c-primary);
}

.rlist__val {
  margin-left: auto;
  font-size: 12px;
  color: var(--c-accent);
  flex-shrink: 0;
}

@media (max-width: 900px) {
  .rank__layout {
    grid-template-columns: 1fr;
  }
  .rank__side {
    position: static;
  }
  .rank__nav {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 8px;
    padding: 0 16px;
  }
  .rank__navitem {
    border-left: none;
    border-radius: 16px;
    border: 1px solid var(--c-border);
    padding: 5px 14px;
    font-size: 13px;
  }
}
</style>