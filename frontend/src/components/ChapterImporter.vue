<script setup>
import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { importChapters as adminImport, previewChapters as adminPreview } from '@/api/admin'
import { importMyChapters, previewMyChapters } from '@/api/author'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  bookId: { type: [Number, String], default: null },
  bookTitle: { type: String, default: '' },
  scope: { type: String, default: 'author' }
})

const emit = defineEmits(['update:modelValue', 'done'])

const text = ref('')
const fileName = ref('')
const previewing = ref(false)
const importing = ref(false)
const preview = ref(null)
const previewDirty = ref(false)

const charCount = computed(() => text.value.replace(/\s/g, '').length)

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

function decodeBuffer(buffer) {
  const bytes = new Uint8Array(buffer)
  const utf8 = new TextDecoder('utf-8', { fatal: false }).decode(bytes)
  if (utf8.includes('\uFFFD')) {
    try {
      return new TextDecoder('gbk').decode(bytes)
    } catch {
      return utf8
    }
  }
  return utf8
}

async function onFileChange(event) {
  const file = event.target.files && event.target.files[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.warning('文件不能超过 5MB')
    event.target.value = ''
    return
  }
  const buffer = await file.arrayBuffer()
  text.value = decodeBuffer(buffer)
  fileName.value = file.name
  preview.value = null
  previewDirty.value = true
  ElMessage.success(`已读取 ${file.name}`)
  event.target.value = ''
}

function onTextInput() {
  previewDirty.value = true
}

function clearAll() {
  text.value = ''
  fileName.value = ''
  preview.value = null
  previewDirty.value = false
}

async function handleClose(done) {
  if (!text.value.trim()) {
    done()
    return
  }
  try {
    await ElMessageBox.confirm('当前内容还没有导入，关闭后会丢失。', '确认关闭？', {
      confirmButtonText: '关闭',
      cancelButtonText: '继续编辑',
      type: 'warning'
    })
    done()
  } catch {
    /* 用户选择继续编辑 */
  }
}

async function doPreview() {
  if (!text.value.trim()) {
    ElMessage.warning('请先粘贴或上传章节内容')
    return
  }
  if (!props.bookId) {
    ElMessage.warning('缺少目标书籍')
    return
  }
  previewing.value = true
  try {
    const fn = props.scope === 'admin' ? adminPreview : previewMyChapters
    preview.value = await fn(props.bookId, text.value)
    previewDirty.value = false
    if (!preview.value.count) {
      ElMessage.warning('没有解析到章节，请确认内容里有「第X章」这样的标题行')
    }
  } catch {
    /* 拦截器已提示 */
  } finally {
    previewing.value = false
  }
}

async function doImport() {
  if (!text.value.trim()) {
    ElMessage.warning('请先粘贴或上传章节内容')
    return
  }
  if (!props.bookId) {
    ElMessage.warning('缺少目标书籍')
    return
  }
  importing.value = true
  try {
    const fn = props.scope === 'admin' ? adminImport : importMyChapters
    const res = await fn(props.bookId, text.value)
    ElMessage.success(`已导入 ${res.imported} 章`)
    clearAll()
    visible.value = false
    emit('done')
  } catch {
    /* 拦截器已提示 */
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <el-dialog
    v-model="visible"
    :before-close="handleClose"
    :title="`导入章节${bookTitle ? ' · ' + bookTitle : ''}`"
    width="820px"
    top="6vh"
  >
    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="支持上传 .txt 文件或直接粘贴；系统按「第X章」自动切分，找不到标题时整段作为一章。"
      class="importer__alert"
    />

    <div class="importer__bar">
      <label class="importer__file">
        <input type="file" accept=".txt,text/plain" @change="onFileChange" />
        <span class="btn">选择 .txt 文件</span>
      </label>
      <span v-if="fileName" class="importer__name">{{ fileName }}</span>
      <span class="importer__stat">{{ charCount }} 字</span>
      <el-button v-if="text" link type="danger" @click="clearAll">清空</el-button>
    </div>

    <el-input
      v-model="text"
      type="textarea"
      :rows="11"
      resize="vertical"
      placeholder="第一章 初入江湖&#10;　　正文内容……&#10;&#10;第二章 风起&#10;　　正文内容……"
      @input="onTextInput"
    />

    <div v-if="preview && !previewDirty" class="importer__preview">
      <div class="importer__preview-head">
        预计切分为 <b>{{ preview.count }}</b> 章
      </div>
      <el-table :data="preview.items" size="small" border max-height="220">
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="title" label="章节标题" min-width="240" show-overflow-tooltip />
        <el-table-column prop="word_count" label="字数" width="100" />
      </el-table>
    </div>

    <template #footer>
      <div class="importer__footer">
        <el-button :loading="previewing" @click="doPreview">预览分章</el-button>
        <span class="importer__spacer"></span>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="doImport">确认导入</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.importer__alert {
  margin-bottom: 14px;
}

.importer__bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.importer__file input {
  display: none;
}

.importer__file .btn {
  border: 1px solid var(--c-border, #e8e3da);
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  background: #fff;
}

.importer__file .btn:hover {
  border-color: #ff7da6;
  color: var(--c-primary);
}

.importer__name {
  font-size: 12px;
  color: #7a7a7a;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.importer__stat {
  margin-left: auto;
  font-size: 12px;
  color: #a8a39a;
}

.importer__preview {
  margin-top: 14px;
}

.importer__preview-head {
  margin-bottom: 8px;
  font-size: 13px;
  color: #7a7a7a;
}

.importer__preview-head b {
  color: var(--c-primary);
  font-size: 15px;
}

.importer__footer {
  display: flex;
  align-items: center;
  gap: 10px;
}

.importer__spacer {
  flex: 1;
}
</style>