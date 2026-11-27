<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  addParagraphComment,
  getChapter,
  getParagraphComments,
  postHistory,
  purchaseBook,
  purchaseChapters,
  reactParagraph
} from '@/api'
import { useReaderStore } from '@/stores/reader'
import { useUserStore } from '@/stores/user'
import { toast } from '@/utils/toast'
import EmptyState from '@/components/EmptyState.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import ReportDialog from '@/components/ReportDialog.vue'

const route = useRoute()
const router = useRouter()
const reader = useReaderStore()
const user = useUserStore()

const chapter = ref(null)
const loading = ref(true)
const failed = ref(false)
const showSettings = ref(false)
let reportTimer = null

const paraMap = ref({})
const paraTotal = ref(0)
const panelOpen = ref(false)
const activeIndex = ref(0)
const draft = ref('')
const sending = ref(false)
const buying = ref(false)
const replyTarget = ref(null)
const highlightId = ref(0)
const reportOpen = ref(false)
const reportId = ref(0)
const reportPreview = ref('')

function openReport(comment) {
  if (!requireLogin()) return
  reportId.value = comment.id
  reportPreview.value = comment.content.slice(0, 60)
  reportOpen.value = true
}

const paragraphs = computed(() => {
  if (!chapter.value?.content) return []
  return chapter.value.content
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
})

const activeList = computed(() => paraMap.value[activeIndex.value] || [])

const activeCount = computed(() =>
  activeList.value.reduce((sum, item) => sum + 1 + (item.replies?.length || 0), 0)
)

const themes = [
  { key: 'white', label: '白', color: '#FFFFFF' },
  { key: 'sepia', label: '米黄', color: '#F5EFE3' },
  { key: 'green', label: '护眼', color: '#D8E6D5' },
  { key: 'dark', label: '夜间', color: '#1A1A1A' }
]

function countOf(index) {
  const items = paraMap.value[index] || []
  return items.reduce((sum, item) => sum + 1 + (item.replies?.length || 0), 0)
}

async function loadParaComments(chapterId) {
  try {
    const data = await getParagraphComments(chapterId)
    paraMap.value = data.grouped || {}
    paraTotal.value = data.total || 0
  } catch {
    paraMap.value = {}
    paraTotal.value = 0
  }
}

async function load(id) {
  loading.value = true
  failed.value = false
  chapter.value = null
  panelOpen.value = false
  draft.value = ''
  replyTarget.value = null
  highlightId.value = 0
  try {
    chapter.value = await getChapter(id)
    window.scrollTo({ top: 0, behavior: 'auto' })
    if (!chapter.value.locked) {
      await loadParaComments(chapter.value.id)
      scheduleReport()
      applyDeepLink()
    }
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}

// 从「我的间贴」跳转过来时，自动打开对应段落的浮层并高亮那条间贴
function applyDeepLink() {
  const para = route.query.para
  if (para === undefined || para === null || para === '') return
  const index = Number(para)
  if (!Number.isInteger(index) || index < 0) return

  activeIndex.value = index
  panelOpen.value = true
  highlightId.value = Number(route.query.cid || 0)

  nextTick(() => {
    const el = document.querySelector('.pcm--hl')
    if (el) el.scrollIntoView({ block: 'center', behavior: 'smooth' })
  })
}

function scheduleReport() {
  clearTimeout(reportTimer)
  if (!user.isLogin) return
  reportTimer = setTimeout(reportProgress, 3000)
}

function reportProgress() {
  if (!user.isLogin || !chapter.value || chapter.value.locked) return
  const doc = document.documentElement
  const scrollable = doc.scrollHeight - window.innerHeight
  const raw = scrollable > 0 ? Math.round((window.scrollY / scrollable) * 100) : 100
  postHistory({
    book_id: chapter.value.book_id,
    chapter_id: chapter.value.id,
    progress: Math.min(100, Math.max(0, raw))
  }).catch(() => {})
}

function goChapter(id) {
  if (!id) return
  reportProgress()
  router.push(`/read/${id}`)
}

function backToBook() {
  if (chapter.value) router.push(`/book/${chapter.value.book_id}`)
  else router.push('/')
}

function onKeydown(event) {
  if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') return
  if (event.key === 'Escape') {
    if (panelOpen.value) closePanel()
    else backToBook()
    return
  }
  if (panelOpen.value) return
  if (event.key === 'ArrowLeft') goChapter(chapter.value?.prev_id)
  else if (event.key === 'ArrowRight') goChapter(chapter.value?.next_id)
}

function changeFont(delta) {
  reader.setFontSize(reader.settings.fontSize + delta)
}

function openPanel(index) {
  activeIndex.value = index
  panelOpen.value = true
  draft.value = ''
  replyTarget.value = null
}

function closePanel() {
  panelOpen.value = false
  replyTarget.value = null
}

function startReply(comment) {
  if (!requireLogin()) return
  replyTarget.value = comment
  draft.value = ''
}

function cancelReply() {
  replyTarget.value = null
  draft.value = ''
}

function requireLogin() {
  if (user.isLogin) return true
  router.push({ path: '/login', query: { redirect: route.fullPath } })
  return false
}

async function submitComment() {
  if (!requireLogin()) return
  const text = draft.value.trim()
  if (!text) {
    toast('说点什么吧')
    return
  }
  sending.value = true
  try {
    await addParagraphComment({
      book_id: chapter.value.book_id,
      chapter_id: chapter.value.id,
      paragraph_index: activeIndex.value,
      content: text,
      parent_id: replyTarget.value?.id || null
    })
    const wasReply = Boolean(replyTarget.value)
    draft.value = ''
    replyTarget.value = null
    await loadParaComments(chapter.value.id)
    toast(wasReply ? '回复成功' : '已发表')
  } catch {
    /* 拦截器已提示 */
  } finally {
    sending.value = false
  }
}

async function react(comment, type) {
  if (!requireLogin()) return
  try {
    await reactParagraph(comment.id, type)
    await loadParaComments(chapter.value.id)
  } catch {
    /* 拦截器已提示 */
  }
}

async function buyChapter() {
  if (!requireLogin()) return
  buying.value = true
  try {
    const res = await purchaseChapters(chapter.value.book_id, [chapter.value.id])
    toast(`已购买本章，扣 ${res.coin} 软妹币`)
    await load(route.params.chapterId)
  } catch {
    /* 拦截器已提示 */
  } finally {
    buying.value = false
  }
}

async function buy() {
  if (!requireLogin()) return
  buying.value = true
  try {
    const res = await purchaseBook(chapter.value.book_id)
    toast(`购买成功，扣 ${res.coin} 软妹币`)
    await load(route.params.chapterId)
  } catch {
    /* 拦截器已提示 */
  } finally {
    buying.value = false
  }
}

watch(
  () => reader.settings,
  () => reader.applyTheme(),
  { deep: true }
)

watch(
  () => route.params.chapterId,
  (id) => {
    if (id) load(id)
  }
)

onMounted(() => {
  reader.applyTheme()
  window.addEventListener('keydown', onKeydown)
  load(route.params.chapterId)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  clearTimeout(reportTimer)
  reportProgress()
})
</script>

<template>
  <div class="reader">
    <header class="reader__bar">
      <button class="reader__back" type="button" @click="backToBook">← 目录</button>
      <span class="reader__book">{{ chapter?.book_title }}</span>
      <span v-if="paraTotal" class="reader__cnt">本章 {{ paraTotal }} 条间贴</span>
      <div class="reader__tools">
        <button class="reader__tool" type="button" @click="showSettings = !showSettings">
          Aa
        </button>
      </div>
    </header>

    <div v-if="showSettings" class="settings">
      <div class="settings__row">
        <span class="settings__label">字号</span>
        <button class="settings__btn" type="button" @click="changeFont(-2)">A−</button>
        <span class="settings__value">{{ reader.settings.fontSize }}px</span>
        <button class="settings__btn" type="button" @click="changeFont(2)">A+</button>
      </div>
      <div class="settings__row">
        <span class="settings__label">背景</span>
        <button
          v-for="theme in themes"
          :key="theme.key"
          class="settings__swatch"
          :class="{ 'settings__swatch--active': reader.settings.theme === theme.key }"
          :style="{ background: theme.color }"
          type="button"
          @click="reader.setTheme(theme.key)"
        >
          {{ theme.label }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="reader__body">
      <div class="skeleton" style="height: 24px; width: 40%; margin: 0 auto 24px"></div>
      <div class="skeleton" style="height: 320px"></div>
    </div>

    <EmptyState
      v-else-if="failed"
      text="章节不存在或已被下架"
      action-text="返回书籍详情"
      :to="chapter ? `/book/${chapter.book_id}` : '/'"
    />

    <!-- 付费锁定 -->
    <div v-else-if="chapter?.locked" class="locked">
      <div class="locked__card">
        <p class="locked__icon">🔒</p>
        <h2 class="locked__title">本章为付费内容</h2>
        <p class="locked__desc">
          《{{ chapter.book_title }}》前 3 章可免费试读，购买后可阅读全部章节。
        </p>
        <p class="locked__price">{{ chapter.chapter_price }} 软妹币<small> / 本章</small></p>
        <p class="locked__whole">整本购买 {{ chapter.price_coin }} 软妹币</p>
        <div class="locked__actions">
          <button class="btn btn--primary" type="button" :disabled="buying" @click="buyChapter">
            购买本章
          </button>
          <button class="btn btn--buy" type="button" :disabled="buying" @click="buy">
            购买全本
          </button>
        </div>
        <p class="locked__foot">
          <router-link :to="`/book/${chapter.book_id}`">返回目录查看其他章节</router-link>
        </p>
      </div>
    </div>

    <article v-else-if="chapter" class="reader__body">
      <h1 class="reader__title">{{ chapter.title }}</h1>
      <p class="reader__meta">
        第 {{ chapter.chapter_no }} 章 · {{ chapter.word_count }} 字
      </p>

      <div class="reader__content">
        <div v-for="(para, index) in paragraphs" :key="index" class="para">
          <p class="para__text">{{ para }}</p>
          <button
            v-if="countOf(index)"
            class="para__badge"
            type="button"
            @click="openPanel(index)"
          >
            {{ countOf(index) }}
          </button>
          <button
            v-else
            class="para__badge para__badge--empty"
            type="button"
            @click="openPanel(index)"
          >
            +
          </button>
        </div>
      </div>

      <nav class="reader__nav">
        <button class="btn" type="button" :disabled="!chapter.prev_id" @click="goChapter(chapter.prev_id)">
          上一章
        </button>
        <span class="reader__pos">{{ chapter.chapter_no }} / {{ chapter.book_title }}</span>
        <button class="btn" type="button" :disabled="!chapter.next_id" @click="goChapter(chapter.next_id)">
          下一章
        </button>
      </nav>
    </article>
  </div>

  <!-- 间贴浮层 -->
  <Teleport to="body">
    <div v-if="panelOpen" class="pc-mask" @click.self="closePanel"></div>
    <aside class="pc" :class="{ 'pc--open': panelOpen }">
      <header class="pc__head">
        <span class="pc__title">第 {{ activeIndex + 1 }} 段 · {{ activeCount }} 条间贴</span>
        <button class="pc__close" type="button" @click="closePanel">✕</button>
      </header>

      <div class="pc__body">
        <p v-if="!activeList.length" class="pc__empty">这一段还没有人吐槽，来第一个</p>
        <div
          v-for="item in activeList"
          :key="item.id"
          class="pcm"
          :class="{ 'pcm--hl': highlightId === item.id }"
        >
          <UserAvatar :user="item.user" :size="28" />
          <div class="pcm__main">
            <p class="pcm__name">{{ item.user.nickname || item.user.username }}</p>
            <p class="pcm__text">{{ item.content }}</p>
            <div class="pcm__ops">
              <button class="pcm__op" type="button" @click="react(item, 1)">
                👍 {{ item.like_count }}
              </button>
              <button class="pcm__op" type="button" @click="react(item, 2)">
                👎 {{ item.dislike_count }}
              </button>
              <button class="pcm__op" type="button" @click="startReply(item)">回复</button>
              <button class="pcm__op pcm__op--report" type="button" @click="openReport(item)">
                举报
              </button>
            </div>

            <div v-if="item.replies?.length" class="pcrlist">
              <div
                v-for="reply in item.replies"
                :key="reply.id"
                class="pcr"
                :class="{ 'pcm--hl': highlightId === reply.id }"
              >
                <span class="pcr__name">{{ reply.user.nickname || reply.user.username }}</span>
                <span class="pcr__text">{{ reply.content }}</span>
                <div class="pcr__ops">
                  <button class="pcm__op" type="button" @click="react(reply, 1)">
                    👍 {{ reply.like_count }}
                  </button>
                  <button class="pcm__op pcm__op--report" type="button" @click="openReport(reply)">
                    举报
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="pc__foot">
        <div v-if="replyTarget" class="pc__replyto">
          <span>回复 @{{ replyTarget.user.nickname || replyTarget.user.username }}</span>
          <button type="button" @click="cancelReply">取消</button>
        </div>
        <textarea
          v-model="draft"
          class="pc__input"
          rows="3"
          maxlength="300"
          :placeholder="replyTarget ? '写下你的回复…' : '针对这一段说点什么…'"
        ></textarea>
        <div class="pc__send">
          <span class="pc__count">{{ draft.length }}/300</span>
          <button class="btn btn--primary" type="button" :disabled="sending" @click="submitComment">
            {{ sending ? '提交中…' : replyTarget ? '回复' : '发表' }}
          </button>
        </div>
      </div>
    </aside>
  </Teleport>

  <ReportDialog
    v-model="reportOpen"
    target-type="paragraph_comment"
    :target-id="reportId"
    :preview="reportPreview"
    @submitted="loadParaComments(chapter.id)"
  />
</template>

<style scoped>
.reader {
  min-height: 100vh;
  background: var(--reader-bg);
  color: var(--reader-text);
  transition: background 0.2s ease, color 0.2s ease;
}

.reader__bar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 16px;
  height: 52px;
  padding: 0 24px;
  background: var(--reader-bg);
  border-bottom: 1px solid var(--reader-border);
}

.reader__back,
.reader__tool {
  border: none;
  background: transparent;
  color: inherit;
  font-size: 14px;
  opacity: 0.75;
}

.reader__back:hover,
.reader__tool:hover {
  opacity: 1;
}

.reader__book {
  flex: 1;
  font-size: 13px;
  opacity: 0.6;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reader__cnt {
  font-size: 12px;
  opacity: 0.55;
}

.settings {
  position: sticky;
  top: 52px;
  z-index: 9;
  padding: 12px 24px;
  background: var(--reader-bg);
  border-bottom: 1px solid var(--reader-border);
}

.settings__row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.settings__row:last-child {
  margin-bottom: 0;
}

.settings__label {
  width: 36px;
  font-size: 13px;
  opacity: 0.6;
}

.settings__btn {
  padding: 4px 12px;
  border: 1px solid var(--reader-border);
  border-radius: 4px;
  background: transparent;
  color: inherit;
  font-size: 13px;
}

.settings__value {
  min-width: 46px;
  font-size: 13px;
  text-align: center;
  opacity: 0.7;
}

.settings__swatch {
  width: 56px;
  height: 30px;
  border: 1px solid var(--reader-border);
  border-radius: 4px;
  color: #666;
  font-size: 12px;
}

.settings__swatch--active {
  outline: 2px solid var(--c-primary);
  outline-offset: 1px;
}

.reader__body {
  max-width: 720px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}

.reader__title {
  margin: 0 0 8px;
  font-size: 26px;
  font-weight: 600;
  font-family: 'Songti SC', 'Noto Serif SC', serif;
}

.reader__meta {
  margin: 0 0 32px;
  font-size: 13px;
  opacity: 0.5;
}

.reader__content {
  font-family: 'Songti SC', 'Source Han Serif SC', 'SimSun', serif;
  font-size: var(--reader-font-size);
  line-height: var(--reader-line-height);
}

.para {
  position: relative;
  padding-right: 34px;
}

.para__text {
  margin: 0 0 1.1em;
}

.para__badge {
  position: absolute;
  right: 0;
  top: 2px;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border: none;
  border-radius: 11px;
  background: var(--c-primary-soft);
  color: var(--c-primary);
  font-size: 11px;
  font-family: -apple-system, sans-serif;
  line-height: 22px;
  opacity: 0.85;
  transition: opacity 0.15s ease;
}

.para__badge:hover {
  opacity: 1;
  background: var(--c-primary);
  color: #fff;
}

.para__badge--empty {
  opacity: 0;
  background: transparent;
  color: var(--c-text-muted);
  border: 1px dashed var(--reader-border);
}

.para:hover .para__badge--empty {
  opacity: 0.7;
}

.reader__nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 56px;
  padding-top: 24px;
  border-top: 1px solid var(--reader-border);
}

.reader__nav .btn {
  background: transparent;
  color: inherit;
  border-color: var(--reader-border);
}

.reader__pos {
  font-size: 12px;
  opacity: 0.5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 付费锁定 */
.locked {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  padding: 40px 20px;
}

.locked__card {
  max-width: 420px;
  padding: 36px 32px;
  text-align: center;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.locked__icon {
  margin: 0 0 12px;
  font-size: 34px;
}

.locked__title {
  margin: 0 0 10px;
  font-size: 20px;
  color: var(--c-text);
}

.locked__desc {
  margin: 0 0 14px;
  font-size: 13px;
  line-height: 1.8;
  color: var(--c-text-secondary);
}

.locked__price {
  margin: 0 0 22px;
  font-size: 24px;
  font-weight: 700;
  color: var(--c-primary);
}

.locked__whole {
  margin: -8px 0 18px;
  font-size: 12px;
  color: var(--c-text-muted);
}

.locked__price small {
  font-size: 12px;
  font-weight: 400;
  color: var(--c-text-muted);
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

.locked__foot {
  margin: 16px 0 0;
  font-size: 12px;
}

.locked__foot a {
  color: var(--c-text-muted);
}

.locked__foot a:hover {
  color: var(--c-primary);
}

.locked__actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

/* 间贴面板 */
.pc-mask {
  position: fixed;
  inset: 0;
  z-index: 300;
  background: rgba(0, 0, 0, 0.35);
}

.pc {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 301;
  width: 380px;
  max-width: 92vw;
  display: flex;
  flex-direction: column;
  background: #fff;
  box-shadow: -8px 0 32px rgba(0, 0, 0, 0.12);
  transform: translateX(100%);
  transition: transform 0.25s ease;
}

.pc--open {
  transform: translateX(0);
}

.pc__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 16px;
  border-bottom: 1px solid #f2f2f2;
}

.pc__title {
  font-size: 14px;
  font-weight: 600;
}

.pc__close {
  border: none;
  background: transparent;
  font-size: 15px;
  color: #999;
}

.pc__body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}

.pc__empty {
  margin: 40px 0;
  text-align: center;
  font-size: 13px;
  color: #a8a39a;
}

.pcm {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px dashed #f4f4f4;
}

.pcm__main {
  flex: 1;
  min-width: 0;
}

.pcm__name {
  margin: 0 0 3px;
  font-size: 12px;
  color: #999;
}

.pcm__text {
  margin: 0 0 6px;
  font-size: 13px;
  line-height: 1.7;
  color: #333;
  word-break: break-word;
}

.pcm__ops {
  display: flex;
  gap: 14px;
}

.pcm__op {
  border: none;
  background: transparent;
  padding: 0;
  font-size: 12px;
  color: #999;
}

.pcm__op:hover {
  color: var(--c-primary);
}

.pcm__op--report:hover {
  color: var(--c-danger);
}

/* 楼层高亮（从「我的间贴」跳转过来时） */
.pcm--hl {
  animation: pcFlash 1.6s ease;
  border-radius: 6px;
}

@keyframes pcFlash {
  0%,
  100% {
    background: transparent;
  }
  30% {
    background: var(--c-primary-soft);
  }
}

/* 回复列表 */
.pcrlist {
  margin-top: 8px;
  padding-left: 10px;
  border-left: 2px solid #f2f2f2;
}

.pcr {
  padding: 6px 0;
  border-bottom: 1px dashed #f7f7f7;
}

.pcr:last-child {
  border-bottom: none;
}

.pcr__name {
  margin-right: 6px;
  font-size: 12px;
  color: var(--c-primary);
}

.pcr__text {
  font-size: 13px;
  line-height: 1.7;
  color: #444;
  word-break: break-word;
}

.pcr__ops {
  display: flex;
  gap: 12px;
  margin-top: 3px;
}

.pc__replyto {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  background: var(--c-primary-soft);
  font-size: 12px;
  color: var(--c-primary);
}

.pc__replyto button {
  border: none;
  background: transparent;
  font-size: 12px;
  color: var(--c-primary);
  opacity: 0.75;
}

.pc__foot {
  padding: 12px 16px 16px;
  border-top: 1px solid #f2f2f2;
}

.pc__input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--c-border);
  border-radius: 6px;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.7;
  resize: none;
}

.pc__send {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.pc__count {
  font-size: 12px;
  color: #a8a39a;
}

@media (max-width: 640px) {
  .reader__body {
    padding: 24px 18px 60px;
  }
  .reader__title {
    font-size: 21px;
  }
  .para {
    padding-right: 28px;
  }
}
</style>