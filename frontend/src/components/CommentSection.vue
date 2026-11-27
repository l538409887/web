<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createComment, deleteComment, getBookComments, getChapterComments } from '@/api'
import { useUserStore } from '@/stores/user'
import { toast } from '@/utils/toast'
import { confirmDialog } from '@/composables/useConfirm'
import UserAvatar from '@/components/UserAvatar.vue'

const props = defineProps({
  bookId: { type: [Number, String], required: true },
  chapterId: { type: [Number, String], default: null }
})

const route = useRoute()
const router = useRouter()
const user = useUserStore()

const list = ref([])
const total = ref(0)
const loading = ref(true)
const submitting = ref(false)
const content = ref('')
const replyTarget = ref(null)
const replyText = ref('')
const replySubmitting = ref(false)

const title = computed(() => (props.chapterId ? '本章评论' : '书评区'))

function requireLogin() {
  if (user.isLogin) return true
  router.push({ path: '/login', query: { redirect: route.fullPath } })
  return false
}

async function load() {
  loading.value = true
  try {
    const params = { page: 1, size: 20 }
    const data = props.chapterId
      ? await getChapterComments(props.chapterId, params)
      : await getBookComments(props.bookId, params)
    list.value = data.list
    total.value = data.total
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!requireLogin()) return
  const text = content.value.trim()
  if (!text) {
    toast('说点什么吧')
    return
  }
  if (text.length > 500) {
    toast('评论最多 500 字')
    return
  }
  submitting.value = true
  try {
    await createComment({
      book_id: Number(props.bookId),
      chapter_id: props.chapterId ? Number(props.chapterId) : null,
      content: text
    })
    content.value = ''
    toast('发布成功')
    await load()
  } catch {
    /* 拦截器已提示 */
  } finally {
    submitting.value = false
  }
}

function openReply(item) {
  if (!requireLogin()) return
  replyTarget.value = replyTarget.value === item.id ? null : item.id
  replyText.value = ''
}

async function submitReply(parent) {
  const text = replyText.value.trim()
  if (!text) {
    toast('回复内容不能为空')
    return
  }
  replySubmitting.value = true
  try {
    await createComment({
      book_id: Number(props.bookId),
      chapter_id: props.chapterId ? Number(props.chapterId) : null,
      parent_id: parent.id,
      content: text
    })
    replyTarget.value = null
    replyText.value = ''
    toast('回复成功')
    await load()
  } catch {
    /* 拦截器已提示 */
  } finally {
    replySubmitting.value = false
  }
}

async function remove(item) {
  const isReply = Boolean(item.parent_id)
  const confirmed = await confirmDialog({
    title: isReply ? '删除这条回复？' : '删除这条评论？',
    message: isReply
      ? '删除后不可恢复。'
      : '删除后，这条评论下的所有回复也会一并隐藏，且不可恢复。',
    confirmText: '删除'
  })
  if (!confirmed) return

  try {
    await deleteComment(item.id)
    toast('已删除')
    await load()
  } catch {
    /* 拦截器已提示 */
  }
}

function canDelete(item) {
  return user.isLogin && (user.profile?.id === item.user.id || user.profile?.role === 'admin')
}

watch(() => [props.bookId, props.chapterId], () => load(), { immediate: true })
</script>

<template>
  <section class="comments">
    <div class="comments__head">
      <h2 class="section__title">{{ title }}</h2>
      <span class="section__sub">{{ total }} 条</span>
    </div>

    <div class="editor">
      <textarea
        v-model="content"
        class="editor__input"
        rows="3"
        maxlength="500"
        :placeholder="user.isLogin ? '说说你的看法…' : '登录后可以发表评论'"
      ></textarea>
      <div class="editor__bar">
        <span class="editor__count">{{ content.length }} / 500</span>
        <button class="btn btn--primary" type="button" :disabled="submitting" @click="submit">
          {{ submitting ? '发布中…' : '发表' }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="skeleton" style="height: 120px"></div>

    <p v-else-if="!list.length" class="comments__empty">还没有评论，来做第一个吧</p>

    <ul v-else class="c-list">
      <li v-for="item in list" :key="item.id" class="c-item">
        <UserAvatar :user="item.user" :size="36" />
        <div class="c-item__body">
          <div class="c-item__top">
            <span class="c-item__name">{{ item.user.nickname }}</span>
            <span class="c-item__time">{{ item.created_at }}</span>
          </div>
          <p class="c-item__text">{{ item.content }}</p>

          <div class="c-item__ops">
            <button class="c-link" type="button" @click="openReply(item)">回复</button>
            <button v-if="canDelete(item)" class="c-link c-link--danger" type="button" @click="remove(item)">
              删除
            </button>
          </div>

          <div v-if="replyTarget === item.id" class="c-reply-box">
            <textarea
              v-model="replyText"
              class="editor__input"
              rows="2"
              maxlength="500"
              :placeholder="`回复 ${item.user.nickname}`"
            ></textarea>
            <div class="editor__bar">
              <span></span>
              <button class="btn btn--primary" type="button" :disabled="replySubmitting" @click="submitReply(item)">
                回复
              </button>
            </div>
          </div>

          <ul v-if="item.replies.length" class="c-replies">
            <li v-for="reply in item.replies" :key="reply.id" class="c-reply">
              <span class="c-reply__name">{{ reply.user.nickname }}</span>
              <span class="c-reply__text">{{ reply.content }}</span>
              <span class="c-reply__time">{{ reply.created_at }}</span>
              <button v-if="canDelete(reply)" class="c-link c-link--danger" type="button" @click="remove(reply)">
                删除
              </button>
            </li>
          </ul>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.comments {
  margin: 32px 0;
  padding: 24px;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
}

.comments__head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 16px;
}

.comments__empty {
  margin: 24px 0;
  text-align: center;
  color: var(--c-text-muted);
  font-size: 13px;
}

.editor {
  margin-bottom: 24px;
}

.editor__input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  background: var(--c-bg);
  font-family: inherit;
  font-size: 14px;
  line-height: 1.7;
  resize: vertical;
}

.editor__input:focus {
  background: #fff;
  border-color: var(--c-primary-light);
  outline: none;
}

.editor__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.editor__count {
  font-size: 12px;
  color: var(--c-text-muted);
}

.c-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.c-item {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  border-top: 1px solid var(--c-border);
}


.c-item__body {
  flex: 1;
  min-width: 0;
}

.c-item__top {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.c-item__name {
  font-size: 14px;
  font-weight: 600;
}

.c-item__time {
  font-size: 12px;
  color: var(--c-text-muted);
}

.c-item__text {
  margin: 6px 0 0;
  font-size: 14px;
  line-height: 1.75;
  color: var(--c-text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}

.c-item__ops {
  display: flex;
  gap: 14px;
  margin-top: 8px;
}

.c-link {
  border: none;
  background: transparent;
  padding: 0;
  font-size: 12px;
  color: var(--c-text-muted);
}

.c-link:hover {
  color: var(--c-primary);
}

.c-link--danger:hover {
  color: var(--c-danger);
}

.c-reply-box {
  margin-top: 10px;
}

.c-replies {
  margin: 12px 0 0;
  padding: 10px 14px;
  list-style: none;
  background: var(--c-bg);
  border-radius: var(--radius-sm);
}

.c-reply {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 4px 0;
  font-size: 13px;
  flex-wrap: wrap;
}

.c-reply__name {
  color: var(--c-primary);
  font-weight: 500;
}

.c-reply__text {
  color: var(--c-text-secondary);
  flex: 1;
  min-width: 0;
  word-break: break-word;
}

.c-reply__time {
  font-size: 11px;
  color: var(--c-text-muted);
}
</style>