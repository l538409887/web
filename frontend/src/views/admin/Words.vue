<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createSensitiveWord,
  deleteSensitiveWord,
  getSensitiveWords,
  testSensitiveWords,
  updateSensitiveWord
} from '@/api/admin'
import { confirmDialog } from '@/composables/useConfirm'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ keyword: '', level: null, page: 1, size: 20 })

const dialog = ref(false)
const form = reactive({ word: '', level: 'review', category: '其他' })
const saving = ref(false)

const testText = ref('')
const testResult = ref(null)
const testing = ref(false)

const LEVEL = {
  block: { text: '直接拦截', type: 'danger' },
  review: { text: '转人工', type: 'warning' }
}
const levelOf = (v) => LEVEL[v] || LEVEL.review
const categories = ['广告', '辱骂', '违禁', '其他']

async function load() {
  loading.value = true
  try {
    const params = { page: query.page, size: query.size }
    if (query.keyword) params.keyword = query.keyword
    if (query.level) params.level = query.level
    const data = await getSensitiveWords(params)
    list.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function search() {
  query.page = 1
  load()
}

function openCreate() {
  form.word = ''
  form.level = 'review'
  form.category = '其他'
  dialog.value = true
}

async function save() {
  if (!form.word.trim()) return ElMessage.warning('请填写敏感词')
  saving.value = true
  try {
    await createSensitiveWord({ ...form, word: form.word.trim() })
    ElMessage.success('已添加')
    dialog.value = false
    await load()
  } catch {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}

async function toggle(row) {
  try {
    await updateSensitiveWord(row.id, { is_active: !row.is_active })
    row.is_active = !row.is_active
    ElMessage.success(row.is_active ? '已启用' : '已停用')
  } catch {
    /* 拦截器已提示 */
  }
}

async function changeLevel(row, level) {
  try {
    await updateSensitiveWord(row.id, { level })
    row.level = level
    ElMessage.success('已修改')
  } catch {
    /* 拦截器已提示 */
  }
}

async function remove(row) {
  const ok = await confirmDialog({
    title: '删除这个词？',
    message: `「${row.word}」删除后将不再参与过滤。`,
    confirmText: '删除'
  })
  if (!ok) return
  try {
    await deleteSensitiveWord(row.id)
    ElMessage.success('已删除')
    await load()
  } catch {
    /* 拦截器已提示 */
  }
}

async function runTest() {
  if (!testText.value.trim()) return ElMessage.warning('请输入要检测的文本')
  testing.value = true
  try {
    testResult.value = await testSensitiveWords(testText.value)
  } catch {
    /* 拦截器已提示 */
  } finally {
    testing.value = false
  }
}

onMounted(load)
</script>

<template>
  <el-card shadow="never" class="panel">
    <div class="bar">
      <el-input
        v-model="query.keyword"
        placeholder="搜索敏感词"
        clearable
        style="width: 200px"
        @keyup.enter="search"
      />
      <el-select v-model="query.level" placeholder="全部级别" clearable style="width: 140px">
        <el-option label="直接拦截" value="block" />
        <el-option label="转人工" value="review" />
      </el-select>
      <el-button type="primary" @click="search">查询</el-button>
      <el-button type="success" @click="openCreate">新增敏感词</el-button>
      <span class="bar__tip">拦截级：发布时直接拒绝；转人工级：放行但进入待审核队列</span>
    </div>

    <div class="tester">
      <el-input
        v-model="testText"
        placeholder="粘贴一段文本，测试会被如何判定"
        style="flex: 1"
        @keyup.enter="runTest"
      />
      <el-button :loading="testing" @click="runTest">检测</el-button>
      <span v-if="testResult" class="tester__result">
        拦截词：{{ testResult.blocked.length ? testResult.blocked.join('、') : '无' }}
        ｜ 转人工词：{{ testResult.review.length ? testResult.review.join('、') : '无' }}
      </span>
    </div>

    <el-table v-loading="loading" :data="list" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="word" label="敏感词" min-width="160" />
      <el-table-column label="级别" width="150">
        <template #default="{ row }">
          <el-select
            :model-value="row.level"
            size="small"
            @change="(v) => changeLevel(row, v)"
          >
            <el-option label="直接拦截" value="block" />
            <el-option label="转人工" value="review" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column prop="category" label="分类" width="100" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link :type="row.is_active ? 'warning' : 'success'" @click="toggle(row)">
            {{ row.is_active ? '停用' : '启用' }}
          </el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="pager"
      layout="total, prev, pager, next"
      :total="total"
      :page-size="query.size"
      :current-page="query.page"
      @current-change="(p) => { query.page = p; load() }"
    />

    <el-dialog v-model="dialog" title="新增敏感词" width="460px">
      <el-form label-width="70px">
        <el-form-item label="词">
          <el-input v-model="form.word" maxlength="50" placeholder="支持中文/英文/数字" />
        </el-form-item>
        <el-form-item label="级别">
          <el-radio-group v-model="form.level">
            <el-radio value="block">直接拦截</el-radio>
            <el-radio value="review">转人工</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" style="width: 100%">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
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
  gap: 10px;
  margin-bottom: 12px;
}

.bar__tip {
  margin-left: auto;
  font-size: 12px;
  color: #a8a39a;
}

.tester {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding: 12px 14px;
  background: #fafafa;
  border: 1px dashed #e0dbd2;
  border-radius: 8px;
}

.tester__result {
  font-size: 12px;
  color: #7a7a7a;
  white-space: nowrap;
}

.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
