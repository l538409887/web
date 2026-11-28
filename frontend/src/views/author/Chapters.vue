<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  createChapter,
  deleteChapter,
  getMyBooks,
  getMyChapter,
  getMyChapters,
  updateChapter
} from '@/api/author'
import { confirmDialog } from '@/composables/useConfirm'

const route = useRoute()
const router = useRouter()
const bookId = Number(route.params.id)

const loading = ref(false)
const saving = ref(false)
const book = ref(null)
const chapters = ref([])

const editing = ref(null)
const form = reactive({ title: '', content: '' })

const AUDIT = {
  0: { text: '草稿', type: 'info' },
  1: { text: '待审核', type: 'warning' },
  2: { text: '已通过', type: 'success' },
  3: { text: '未通过', type: 'danger' }
}
const auditOf = (v) => AUDIT[v] || AUDIT[1]

const nextNo = computed(() => {
  const max = chapters.value.reduce((acc, c) => Math.max(acc, c.chapter_no), 0)
  return editing.value ? editing.value.chapter_no : max + 1
})

const titlePlaceholder = computed(
  () => `留空则自动命名为「第${nextNo.value}章」`
)

async function loadAll() {
  loading.value = true
  try {
    const [bookData, chapterData] = await Promise.all([
      getMyBooks({ page: 1, size: 100 }),
      getMyChapters(bookId, { page: 1, size: 500 })
    ])
    book.value = (bookData.list || []).find((item) => item.id === bookId) || null
    chapters.value = chapterData.list
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}

function startCreate() {
  editing.value = null
  form.title = ''
  form.content = ''
}

async function startEdit(chapter) {
  editing.value = chapter
  form.title = chapter.title || ''
  form.content = ''
  try {
    const detail = await getMyChapter(chapter.id)
    if (editing.value && editing.value.id === chapter.id) {
      form.content = detail.content || ''
      form.title = detail.title || ''
    }
  } catch {
    /* 拦截器已提示 */
  }
}

async function save(draft) {
  if (!form.content.trim()) {
    ElMessage.warning(draft ? '草稿也要写点内容' : '正文不能为空')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateChapter(editing.value.id, {
        title: form.title,
        content: form.content,
        action: draft ? 'draft' : 'submit'
      })
      ElMessage.success(draft ? '已暂存为草稿' : '已提交审核')
      await loadAll()
    } else {
      const res = await createChapter(bookId, {
        title: form.title,
        content: form.content,
        draft
      })
      ElMessage.success(draft ? `已暂存「${res.title}」` : `已提交「${res.title}」`)
      await loadAll()
      const created = chapters.value.find((c) => c.id === res.id)
      if (created) {
        editing.value = created
        form.title = created.title
      }
    }
  } catch {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}

async function removeChapter(chapter) {
  const ok = await confirmDialog({
    title: '删除这一章？',
    message: `「${chapter.title}」将被隐藏，前台不再展示，数据保留可追溯。`,
    confirmText: '删除'
  })
  if (!ok) return
  try {
    await deleteChapter(chapter.id)
    ElMessage.success('已删除')
    if (editing.value && editing.value.id === chapter.id) startCreate()
    await loadAll()
  } catch {
    /* 拦截器已提示 */
  }
}

onMounted(loadAll)
</script>

<template>
  <el-card v-loading="loading" shadow="never" class="panel">
    <div class="bar">
      <div class="bar__left">
        <el-button link @click="router.push('/author/books')">← 返回作品列表</el-button>
        <span class="bar__title">{{ book?.title || '作品' }}</span>
        <el-tag v-if="book" size="small" effect="plain">
          {{ book.chapter_count }} 章 / {{ book.word_count }} 字
        </el-tag>
      </div>
      <el-button type="primary" @click="startCreate">新建章节</el-button>
    </div>

    <div class="layout">
      <!-- 左：章节列表 -->
      <aside class="list">
        <div class="list__head">
          <span>全部章节</span>
          <span class="list__count">{{ chapters.length }}</span>
        </div>
        <ul class="chs">
          <li
            v-for="ch in chapters"
            :key="ch.id"
            class="chs__item"
            :class="{ 'chs__item--on': editing?.id === ch.id }"
            @click="startEdit(ch)"
          >
            <span class="chs__no">{{ ch.chapter_no }}</span>
            <span class="chs__title">{{ ch.title }}</span>
            <el-tag :type="auditOf(ch.audit_status).type" size="small" effect="plain">
              {{ auditOf(ch.audit_status).text }}
            </el-tag>
            <el-button
              class="chs__del"
              link
              type="danger"
              @click.stop="removeChapter(ch)"
            >
              删除
            </el-button>
          </li>
          <li v-if="!chapters.length" class="chs__empty">还没有章节，点右上角新建</li>
        </ul>
      </aside>

      <!-- 右：章节名 + 正文 -->
      <section class="editor">
        <div class="editor__head">
          <span class="editor__mode">
            {{ editing ? `编辑：第${editing.chapter_no}章` : '新建章节' }}
          </span>
          <el-tag v-if="editing" :type="auditOf(editing.audit_status).type" size="small">
            {{ auditOf(editing.audit_status).text }}
          </el-tag>
        </div>

        <div class="editor__row">
          <label class="editor__label">章节名</label>
          <el-input v-model="form.title" :placeholder="titlePlaceholder" maxlength="200" />
        </div>

        <div class="editor__body">
          <label class="editor__label">正文</label>
          <div class="editor__area">
            <el-input
              v-model="form.content"
              type="textarea"
              :rows="18"
              resize="vertical"
              placeholder="在此粘贴或撰写正文，段落用换行分隔"
            />
            <div class="editor__meta">{{ form.content.length }} 字符 · 支持从文档直接粘贴</div>
          </div>
        </div>

        <div class="editor__foot">
          <el-button :loading="saving" @click="save(true)">暂存草稿</el-button>
          <el-button type="primary" :loading="saving" @click="save(false)">提交审核</el-button>
          <span class="editor__tip">草稿不校验敏感词、不进审核队列；提交后由管理员审核。</span>
        </div>
      </section>
    </div>
  </el-card>
</template>

<style scoped>
.panel {
  border: 1px solid var(--c-border);
  border-radius: 10px;
}

.bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--c-border);
  margin-bottom: 16px;
}

.bar__left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.bar__title {
  font-size: 16px;
  font-weight: 700;
  color: var(--c-text);
}

.layout {
  display: flex;
  gap: 18px;
  align-items: flex-start;
}

.list {
  width: 320px;
  flex-shrink: 0;
  border: 1px solid var(--c-border);
  border-radius: 8px;
  overflow: hidden;
}

.list__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: #fafafa;
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text);
}

.list__count {
  font-weight: 400;
  color: var(--c-text-muted);
}

.chs {
  margin: 0;
  padding: 4px 0;
  list-style: none;
  max-height: 580px;
  overflow-y: auto;
}

.chs__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  font-size: 13px;
  cursor: pointer;
  border-left: 2px solid transparent;
}

.chs__item:hover {
  background: #fff8fa;
}

.chs__item:hover .chs__del {
  opacity: 1;
}

.chs__item--on {
  background: #fff2f6;
  border-left-color: var(--c-primary);
}

.chs__no {
  width: 22px;
  color: var(--c-text-muted);
  font-size: 12px;
  text-align: right;
}

.chs__title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--c-text);
}

.chs__del {
  opacity: 0;
  transition: opacity 0.15s ease;
}

.chs__empty {
  padding: 14px 12px;
  font-size: 12px;
  color: var(--c-text-muted);
}

.editor {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.editor__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.editor__mode {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text);
}

.editor__row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.editor__label {
  width: 64px;
  flex-shrink: 0;
  font-size: 13px;
  color: var(--c-text-secondary);
}

.editor__body {
  display: flex;
  gap: 12px;
}

.editor__area {
  flex: 1;
}

.editor__meta {
  margin-top: 6px;
  font-size: 12px;
  color: var(--c-text-muted);
}

.editor__foot {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 10px;
  border-top: 1px dashed var(--c-border);
}

.editor__tip {
  font-size: 12px;
  color: var(--c-text-muted);
}

@media (max-width: 1100px) {
  .layout {
    flex-direction: column;
  }

  .list {
    width: 100%;
  }
}
</style>
