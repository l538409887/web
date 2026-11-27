<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
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
import ChapterImporter from '@/components/ChapterImporter.vue'

const route = useRoute()
const bookId = route.params.id

const loading = ref(false)
const list = ref([])
const total = ref(0)
const bookTitle = ref('')

const dialogVisible = ref(false)
const editing = ref(null)
const form = reactive({ title: '', content: '' })
const saving = ref(false)

const importVisible = ref(false)

async function load() {
  loading.value = true
  try {
    const data = await getMyChapters(bookId, { page: 1, size: 500 })
    list.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function loadBookTitle() {
  const data = await getMyBooks({ page: 1, size: 50 })
  const found = data.list.find((item) => String(item.id) === String(bookId))
  bookTitle.value = found?.title || ''
}

function openCreate() {
  editing.value = null
  form.title = ''
  form.content = ''
  dialogVisible.value = true
}

async function openEdit(row) {
  const detail = await getMyChapter(row.id)
  editing.value = detail
  form.title = detail.title
  form.content = detail.content
  dialogVisible.value = true
}

async function submit() {
  if (!form.title.trim()) {
    ElMessage.warning('请填写章节标题')
    return
  }
  if (!form.content.trim()) {
    ElMessage.warning('请填写正文')
    return
  }
  saving.value = true
  try {
    if (editing.value) {
      await updateChapter(editing.value.id, {
        title: form.title.trim(),
        content: form.content
      })
      ElMessage.success('已保存')
    } else {
      await createChapter(bookId, {
        title: form.title.trim(),
        content: form.content
      })
      ElMessage.success('章节已发布')
    }
    dialogVisible.value = false
    await load()
  } catch {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}

async function remove(row) {
  const confirmed = await confirmDialog({
    title: '删除这一章？',
    message: `「${row.title}」将被隐藏，前台不再可见。`,
    confirmText: '删除'
  })
  if (!confirmed) return
  try {
    await deleteChapter(row.id)
    ElMessage.success('已删除')
    await load()
  } catch {
    /* 拦截器已提示 */
  }
}


onMounted(() => {
  loadBookTitle()
  load()
})
</script>

<template>
  <el-card shadow="never" class="panel">
    <div class="bar">
      <div class="bar__left">
        <span class="bar__title">{{ bookTitle || '作品章节' }}</span>
        <span class="bar__count">共 {{ total }} 章</span>
      </div>
      <div class="bar__right">
        <el-button @click="importVisible = true">批量导入</el-button>
        <el-button type="primary" @click="openCreate">新增章节</el-button>
      </div>
    </div>

    <el-table v-loading="loading" :data="list" border stripe>
      <el-table-column prop="chapter_no" label="序号" width="80" />
      <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
      <el-table-column prop="word_count" label="字数" width="90" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
            {{ row.status === 1 ? '正常' : '已隐藏' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="row.status === 1" link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="editing ? `编辑：${editing.title}` : '新增章节'"
      width="720px"
    >
      <el-form label-width="70px">
        <el-form-item label="标题">
          <el-input v-model="form.title" maxlength="200" placeholder="例如：第一章 初入山门" />
        </el-form-item>
        <el-form-item label="正文">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="14"
            placeholder="段落之间空一行即可，前端会按空行分段渲染"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>

    <ChapterImporter
      v-model="importVisible"
      :book-id="bookId"
      :book-title="bookTitle"
      scope="author"
      @done="load"
    />
  </el-card>
</template>

<style scoped>
.panel {
  border: 1px solid #e8e3da;
  border-radius: 8px;
}

.bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 12px;
  flex-wrap: wrap;
}

.bar__left {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.bar__title {
  font-size: 15px;
  font-weight: 600;
  color: #2b2b2b;
}

.bar__count {
  font-size: 12px;
  color: #a8a39a;
}

.bar__right {
  display: flex;
  gap: 10px;
}

.tip {
  margin: 0 0 12px;
  font-size: 13px;
  color: #7a7a7a;
}
</style>