<script setup>
import { ref } from 'vue'

defineProps({
  items: { type: Array, default: () => [] }
})

const active = ref(null)

function catColor(category) {
  if (category === '活动') return '#ffd666'
  if (category === '更新') return '#69c0ff'
  return '#ff85a8'
}

function formatTime(value) {
  return (value || '').replace('T', ' ').slice(0, 10)
}

function open(item) {
  active.value = item
}

function close() {
  active.value = null
}
</script>

<template>
  <aside class="np">
    <div class="np__head">
      <h2 class="np__title">最新活动</h2>
      <span class="np__hint">平台公告</span>
    </div>

    <ul v-if="items.length" class="np__list">
      <li v-for="item in items" :key="item.id" class="np__item" @click="open(item)">
        <span class="np__cat" :style="{ color: catColor(item.category) }">
          {{ item.category }}
        </span>
        <span class="np__text">{{ item.title }}</span>
      </li>
    </ul>
    <p v-else class="np__empty">暂无公告</p>

    <Teleport to="body">
      <div v-if="active" class="ntc-mask" @click.self="close">
        <div class="ntc">
          <header class="ntc__head">
            <div>
              <span class="ntc__cat" :style="{ background: catColor(active.category) }">
                {{ active.category }}
              </span>
              <h3 class="ntc__title">{{ active.title }}</h3>
              <p class="ntc__time">{{ formatTime(active.created_at) }}</p>
            </div>
            <button class="ntc__close" type="button" @click="close">✕</button>
          </header>
          <div class="ntc__body">{{ active.content || '暂无详细内容。' }}</div>
        </div>
      </div>
    </Teleport>
  </aside>
</template>

<style scoped>
.np {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 18px 20px;
  background: #1c1c1f;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.np__head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.09);
}

.np__title {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
}

.np__hint {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.32);
}

.np__list {
  flex: 1;
  margin: 0;
  padding: 4px 0 0;
  list-style: none;
  overflow: hidden;
}

.np__item {
  display: flex;
  gap: 8px;
  padding: 9px 0;
  cursor: pointer;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.07);
}

.np__item:last-child {
  border-bottom: none;
}

.np__item:hover .np__text {
  color: #ff85a8;
}

.np__cat {
  flex-shrink: 0;
  font-size: 11px;
  line-height: 1.7;
  opacity: 0.9;
}

.np__text {
  font-size: 13px;
  line-height: 1.65;
  color: rgba(255, 255, 255, 0.82);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: color 0.15s ease;
}

.np__empty {
  margin: 30px 0;
  text-align: center;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.3);
}

/* 弹窗 */
.ntc-mask {
  position: fixed;
  inset: 0;
  z-index: 400;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(0, 0, 0, 0.45);
}

.ntc {
  width: 520px;
  max-width: 100%;
  max-height: 76vh;
  overflow-y: auto;
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.24);
}

.ntc__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 20px 22px 14px;
  border-bottom: 1px solid #f2f2f2;
}

.ntc__cat {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 3px;
  font-size: 11px;
  color: #2b2b2b;
}

.ntc__title {
  margin: 8px 0 4px;
  font-size: 18px;
  font-weight: 600;
}

.ntc__time {
  margin: 0;
  font-size: 12px;
  color: var(--c-text-muted);
}

.ntc__close {
  border: none;
  background: transparent;
  font-size: 15px;
  color: #999;
}

.ntc__body {
  padding: 18px 22px 24px;
  font-size: 14px;
  line-height: 2;
  color: var(--c-text-secondary);
  white-space: pre-wrap;
}
</style>
