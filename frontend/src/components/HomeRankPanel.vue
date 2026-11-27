<script setup>
const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  items: { type: Array, default: () => [] },
  field: { type: String, default: 'click_count' },
  time: { type: Boolean, default: false },
  more: { type: String, default: '/rank' }
})

function formatCount(value) {
  if (props.time) return String(value || '').slice(0, 10)
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
    background: `linear-gradient(140deg, hsl(${h}, 42%, 52%), hsl(${(h + 40) % 360}, 44%, 36%))`
  }
}
</script>

<template>
  <aside class="panel">
    <div class="panel__head">
      <div>
        <h2 class="panel__title">{{ title }}</h2>
        <p v-if="subtitle" class="panel__sub">{{ subtitle }}</p>
      </div>
      <router-link class="panel__more" :to="more">更多 ›</router-link>
    </div>

    <template v-if="items.length">
      <div class="no1">
        <div class="no1__info">
          <span class="no1__badge">NO.1</span>
          <router-link class="no1__title" :to="`/book/${items[0].id}`">
            {{ items[0].title }}
          </router-link>
          <p class="no1__author">{{ items[0].author?.nickname }}</p>
        </div>
        <router-link class="no1__cover" :style="coverStyle(items[0])" :to="`/book/${items[0].id}`">
          <img v-if="items[0].cover" :src="items[0].cover" :alt="items[0].title" />
          <span v-else>{{ items[0].title.slice(0, 2) }}</span>
        </router-link>
      </div>
      <p class="no1__val">{{ formatCount(items[0][field]) }}</p>

      <ol class="plist">
        <li v-for="(book, index) in items.slice(1, 10)" :key="book.id" class="plist__item">
          <span class="plist__idx">{{ index + 2 }}</span>
          <span class="plist__cat">[{{ book.category?.name }}]</span>
          <router-link class="plist__name" :to="`/book/${book.id}`">{{ book.title }}</router-link>
          <span class="plist__val">{{ formatCount(book[field]) }}</span>
        </li>
      </ol>
    </template>
  </aside>
</template>

<style scoped>
.panel {
  background: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: 16px;
}

.panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f4f4f4;
}

.panel__title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
}

.panel__sub {
  margin: 3px 0 0;
  font-size: 12px;
  color: var(--c-text-muted);
}

.panel__more {
  font-size: 12px;
  color: var(--c-text-muted);
  white-space: nowrap;
}

.panel__more:hover {
  color: var(--c-primary);
}

.no1 {
  display: flex;
  gap: 12px;
  padding: 12px 0 6px;
}

.no1__info {
  flex: 1;
  min-width: 0;
}

.no1__badge {
  display: inline-block;
  padding: 0 7px;
  border-radius: 3px;
  background: var(--c-primary);
  color: #fff;
  font-size: 11px;
  line-height: 18px;
  font-weight: 600;
}

.no1__title {
  display: block;
  margin: 7px 0 4px;
  font-size: 14px;
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
  color: var(--c-primary);
}

.no1__cover {
  width: 54px;
  height: 72px;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
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

.no1__val {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 700;
  color: var(--c-danger);
}

.plist {
  margin: 0;
  padding: 0;
  list-style: none;
  border-top: 1px dashed #f4f4f4;
}

.plist__item {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 8px 0;
  border-bottom: 1px dashed #f7f7f7;
}

.plist__item:last-child {
  border-bottom: none;
}

.plist__idx {
  width: 15px;
  flex-shrink: 0;
  font-size: 12px;
  color: var(--c-text-muted);
  font-weight: 600;
}

.plist__cat {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--c-primary);
}

.plist__name {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plist__name:hover {
  color: var(--c-primary);
}

.plist__val {
  margin-left: auto;
  flex-shrink: 0;
  font-size: 12px;
  color: var(--c-accent);
}
</style>
