<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  items: { type: Array, default: () => [] },
  interval: { type: Number, default: 4500 }
})

const router = useRouter()
const index = ref(0)
let timer = null

const count = computed(() => props.items.length)

function hueOf(text) {
  let h = 7
  for (const ch of text || '') h = (h * 31 + ch.charCodeAt(0)) % 360
  return h
}

// 首页轮播用的插画（放到 frontend/public/banners/ 下，按顺序循环使用）
const ART = [
  '/banners/b1.jpg',
  '/banners/b2.jpg',
  '/banners/b3.jpg',
  '/banners/b4.jpg',
  '/banners/b5.jpg'
]

// 插画按原尺寸展示（源图只有 378px 宽，放大铺满必糊），
// 所以底图改用渐变色块，插画作为一张小卡片放在右侧
function artOf(idx) {
  if (!ART.length) return ''
  return ART[idx % ART.length]
}

function washStyle(book) {
  const h = hueOf(book.title)
  return {
    background: `linear-gradient(115deg, hsl(${h}, 34%, 18%) 0%, hsl(${(h + 24) % 360}, 42%, 30%) 58%, hsl(${(h + 52) % 360}, 38%, 22%) 100%)`
  }
}

function go(i) {
  if (!count.value) return
  index.value = (i + count.value) % count.value
}

function next() {
  go(index.value + 1)
}

function prev() {
  go(index.value - 1)
}

function start() {
  stop()
  if (count.value > 1) timer = setInterval(next, props.interval)
}

function stop() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

function openBook(book) {
  if (book.last_chapter_id) router.push(`/read/${book.last_chapter_id}`)
  else router.push(`/book/${book.id}`)
}

watch(count, (value) => {
  if (value > 0 && index.value >= value) index.value = 0
  start()
})

onMounted(start)
onBeforeUnmount(stop)
</script>

<template>
  <div
    v-if="count"
    class="car"
    @mouseenter="stop"
    @mouseleave="start"
  >
    <div class="car__viewport">
      <div class="car__track" :style="{ transform: `translateX(-${index * 100}%)` }">
        <div v-for="(book, i) in items" :key="book.id" class="car__slide">
          <div class="car__wash" :style="washStyle(book)"></div>
          <div class="car__art">
            <img :src="artOf(i)" :alt="book.title" />
          </div>

          <div class="car__content">
            <p class="car__eyebrow">
              {{ book.category?.name }} · {{ book.status === 1 ? '已完结' : '连载中' }}
            </p>
            <h2 class="car__title">{{ book.title }}</h2>
            <p class="car__intro">{{ book.intro }}</p>
            <div class="car__foot">
              <button class="car__cta" type="button" @click="openBook(book)">立即阅读</button>
              <span class="car__author">{{ book.author?.nickname }} 著</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <button class="car__arrow car__arrow--prev" type="button" @click="prev">‹</button>
    <button class="car__arrow car__arrow--next" type="button" @click="next">›</button>

    <div class="car__dots">
      <button
        v-for="(book, i) in items"
        :key="book.id"
        class="car__dot"
        :class="{ 'car__dot--on': i === index }"
        type="button"
        :aria-label="`第 ${i + 1} 张`"
        @click="go(i)"
      ></button>
    </div>
  </div>
</template>

<style scoped>
.car {
  position: relative;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.08);
  background: #f1f1f3;
}

.car__viewport {
  overflow: hidden;
}

.car__track {
  display: flex;
  transition: transform 0.55s cubic-bezier(0.25, 0.8, 0.25, 1);
  will-change: transform;
}

.car__slide {
  position: relative;
  flex: 0 0 100%;
  height: 340px;
}

.car__wash {
  position: absolute;
  inset: 0;
}

.car__art {
  position: absolute;
  top: 50%;
  right: 40px;
  width: 380px;
  height: 240px;
  transform: translateY(-50%);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 14px 34px rgba(0, 0, 0, 0.36);
}

.car__art img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.car__content {
  position: absolute;
  left: 44px;
  bottom: 40px;
  right: 452px;
  color: #fff;
}

.car__eyebrow {
  margin: 0 0 10px;
  font-size: 13px;
  letter-spacing: 1px;
  opacity: 0.85;
}

.car__title {
  margin: 0 0 12px;
  font-size: 32px;
  font-weight: 700;
  letter-spacing: 2px;
  font-family: 'Songti SC', 'Noto Serif SC', serif;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
}

.car__intro {
  margin: 0 0 22px;
  max-width: 560px;
  font-size: 14px;
  line-height: 1.85;
  opacity: 0.92;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.car__foot {
  display: flex;
  align-items: center;
  gap: 16px;
}

.car__cta {
  padding: 9px 26px;
  border: none;
  border-radius: 20px;
  background: var(--c-primary);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.16s ease;
}

.car__cta:hover {
  background: var(--c-primary-light);
}

.car__author {
  font-size: 13px;
  opacity: 0.8;
}

.car__arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.32);
  color: #fff;
  font-size: 20px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease, background 0.2s ease;
}

.car:hover .car__arrow {
  opacity: 1;
}

.car__arrow:hover {
  background: var(--c-primary);
}

.car__arrow--prev {
  left: 16px;
}

.car__arrow--next {
  right: 16px;
}

.car__dots {
  position: absolute;
  left: 44px;
  bottom: 18px;
  display: flex;
  gap: 7px;
}

.car__dot {
  width: 7px;
  height: 7px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.45);
  transition: all 0.2s ease;
}

.car__dot--on {
  width: 18px;
  border-radius: 4px;
  background: #fff;
}

@media (max-width: 1080px) {
  .car__art {
    width: 268px;
    height: 170px;
    right: 22px;
  }
  .car__content {
    right: 312px;
  }
}

@media (max-width: 768px) {
  .car__slide {
    height: 200px;
  }
  .car__art {
    display: none;
  }
  .car__content {
    left: 18px;
    right: 18px;
    bottom: 26px;
  }
  .car__title {
    font-size: 20px;
  }
  .car__intro {
    -webkit-line-clamp: 2;
    margin-bottom: 14px;
  }
  .car__dots {
    left: 18px;
    bottom: 12px;
  }
  .car__arrow {
    display: none;
  }
}
</style>