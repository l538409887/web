<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  book: { type: Object, required: true },
  showMeta: { type: Boolean, default: false }
})

const failed = ref(false)

const hue = computed(() => {
  let h = 7
  for (const ch of props.book.title || '') h = (h * 31 + ch.charCodeAt(0)) % 360
  return h
})

const coverStyle = computed(() => ({
  background: `linear-gradient(140deg, hsl(${hue.value}, 38%, 46%), hsl(${(hue.value + 42) % 360}, 40%, 32%))`
}))

const initial = computed(() => (props.book.title || '书').slice(0, 2))
const statusText = computed(() => (props.book.status === 1 ? '完结' : '连载'))
</script>

<template>
  <router-link class="bc" :to="`/book/${book.id}`">
    <div class="bc__cover" :style="coverStyle">
      <img
        v-if="book.cover && !failed"
        :src="book.cover"
        :alt="book.title"
        loading="lazy"
        @error="failed = true"
      />
      <span v-else class="bc__init">{{ initial }}</span>
      <span class="bc__status" :class="{ 'bc__status--done': book.status === 1 }">
        {{ statusText }}
      </span>
    </div>
    <div class="bc__body">
      <h3 class="bc__title">{{ book.title }}</h3>
      <p class="bc__author">{{ book.author?.nickname }}</p>
      <p v-if="showMeta" class="bc__meta">
        {{ book.category?.name }} · {{ book.word_count }} 字
      </p>
    </div>
  </router-link>
</template>

<style scoped>
.bc {
  display: block;
}

.bc__cover {
  position: relative;
  aspect-ratio: 3 / 4;
  border-radius: var(--radius-sm);
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bc:hover .bc__cover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-hover);
}

.bc__cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.bc__init {
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 3px;
  color: rgba(255, 255, 255, 0.92);
  font-family: 'Songti SC', 'Noto Serif SC', serif;
}

.bc__status {
  position: absolute;
  left: 0;
  bottom: 0;
  padding: 1px 6px;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 11px;
  line-height: 16px;
  border-radius: 0 4px 0 0;
}

.bc__status--done {
  background: rgba(63, 143, 91, 0.9);
}

.bc__body {
  padding-top: 8px;
}

.bc__title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.bc:hover .bc__title {
  color: var(--c-primary);
}

.bc__author {
  margin: 3px 0 0;
  font-size: 12px;
  color: var(--c-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bc__meta {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--c-text-muted);
}
</style>