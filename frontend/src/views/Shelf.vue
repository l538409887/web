<script setup>
import { onMounted, ref } from 'vue'
import { getShelf } from '@/api'
import EmptyState from '@/components/EmptyState.vue'

const loading = ref(true)
const list = ref([])
const total = ref(0)

async function load() {
  loading.value = true
  try {
    const data = await getShelf({ page: 1, size: 20 })
    list.value = data.list
    total.value = data.total
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="container">
    <div class="head">
      <h1 class="section__title">我的书架</h1>
      <span class="section__sub">共 {{ total }} 本</span>
    </div>

    <div v-if="loading" class="skeleton" style="height: 200px"></div>

    <EmptyState
      v-else-if="!list.length"
      text="书架还是空的，去挑几本喜欢的书吧"
      action-text="去首页看看"
      to="/"
    />

    <ul v-else class="shelf">
      <li v-for="item in list" :key="item.book.id" class="shelf__item">
        <router-link class="shelf__cover" :to="`/book/${item.book.id}`">
          <img v-if="item.book.cover" :src="item.book.cover" :alt="item.book.title" />
          <template v-else>{{ item.book.title.slice(0, 2) }}</template>
          <span v-if="item.has_update" class="shelf__dot"></span>
        </router-link>

        <div class="shelf__main">
          <div class="shelf__title-row">
            <router-link class="shelf__title" :to="`/book/${item.book.id}`">
              {{ item.book.title }}
            </router-link>
            <span v-if="item.is_top" class="tag">置顶</span>
          </div>
          <p class="shelf__meta">
            {{ item.book.author?.nickname }} · 最新 {{ item.book.last_chapter_title || '暂无章节' }}
          </p>
          <p class="shelf__progress">
            <template v-if="item.last_read">
              读到第 {{ item.last_read.chapter_no }} 章 · {{ item.last_read.progress }}%
            </template>
            <template v-else>尚未开始阅读</template>
          </p>
        </div>

        <div class="shelf__actions">
          <router-link
            v-if="item.last_read"
            class="btn btn--primary"
            :to="`/read/${item.last_read.chapter_id}`"
          >
            继续阅读
          </router-link>
          <router-link v-else class="btn btn--primary" :to="`/book/${item.book.id}`">
            开始阅读
          </router-link>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin: 28px 0 20px;
}

.shelf {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.shelf__item {
  display: grid;
  grid-template-columns: 64px 1fr auto;
  align-items: center;
  gap: 18px;
  padding: 16px 20px;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
}

.shelf__item:hover {
  border-color: var(--c-primary-light);
}

.shelf__cover {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 3 / 4;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--c-primary), #d93e73);
  color: rgba(255, 255, 255, 0.92);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 1px;
  font-family: 'Songti SC', 'Noto Serif SC', serif;
}

.shelf__dot {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--c-accent);
}

.shelf__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.shelf__title {
  font-size: 16px;
  font-weight: 600;
}

.shelf__meta,
.shelf__progress {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--c-text-muted);
}

.shelf__progress {
  color: var(--c-primary);
}

@media (max-width: 640px) {
  .shelf__item {
    grid-template-columns: 52px 1fr;
  }
  .shelf__actions {
    grid-column: 1 / -1;
  }
}
</style>