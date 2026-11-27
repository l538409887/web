<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createBook, getAdminBooks, getAdminUsers, getCategories, updateBookStatus } from '@/api/admin'
import { confirmDialog } from '@/composables/useConfirm'
import ChapterImporter from '@/components/ChapterImporter.vue'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ keyword: '', audit_status: null, page: 1, size: 10 })

const categories = ref([])
const authors = ref([])

const createVisible = ref(false)
const createForm = reactive({
  title: '',
  author_id: null,
  category_id: null,
  intro: '',
  status: 0
})

const importVisible = ref(false)
const importTarget = ref(null)


const AUDIT = {
  0: { text: '未提交', type: 'info' },
  1: { text: '待审核', type: 'warning' },
  2: { text: '审核通过', type: 'success' },
  3: { text: '审核未通过', type: 'danger' }
}
const SHELF = {
  0: { text: '未上架', type: 'info' },
  1: { text: '上架审核中', type: 'warning' },
  2: { text: '已上架', type: 'success' },
  3: { text: '上架未通过', type: 'danger' }
}
const auditOf = (v) => AUDIT[v] || AUDIT[0]
const shelfOf = (v) => SHELF[v] || SHELF[0]

async function load() {
  loading.value = true
  try {
    const params = { keyword: query.keyword || undefined, page: query.page, size: query.size }
    if (query.audit_status !== null) params.audit_status = query.audit_status
    const data = await getAdminBooks(params)
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

async function openCreate() {
  if (!categories.value.length) {
    categories.value = await getCategories()
  }
  if (!authors.value.length) {
    const data = await getAdminUsers({ role: 'author', size: 50 })
    authors.value = data.list
  }
  createForm.title = ''
  createForm.author_id = authors.value[0]?.id || null
  createForm.category_id = categories.value[0]?.id || null
  createForm.intro = ''
  createForm.status = 0
  createVisible.value = true
}

async function submitCreate() {
  if (!createForm.title.trim()) return ElMessage.warning('请填写书名')
  if (!createForm.author_id) return ElMessage.warning('请选择作者')
  if (!createForm.category_id) return ElMessage.warning('请选择分类')
  if (!createForm.intro.trim()) return ElMessage.warning('请填写简介')

  try {
    const res = await createBook({
      title: createForm.title.trim(),
      author_id: createForm.author_id,
      category_id: createForm.category_id,
      intro: createForm.intro.trim(),
      status: createForm.status
    })
    ElMessage.success('已创建，可继续导入章节')
    createVisible.value = false
    await load()
    openImport({ id: res.id, title: createForm.title.trim() })
  } catch {
    /* 拦截器已提示 */
  }
}

function openImport(row) {
  importTarget.value = row
  importText.value = ''
  importVisible.value = true
}


async function setAudit(row, value) {
  const isReject = value === 3
  if (isReject) {
    const ok = await confirmDialog({
      title: '驳回这本书？',
      message: '驳回后作者会看到「审核未通过」，作品不会出现在前台。',
      confirmText: '驳回'
    })
    if (!ok) return
  }
  try {
    await updateBookStatus(row.id, { audit_status: value })
    row.audit_status = value
    ElMessage.success(isReject ? '已驳回' : '审核通过')
  } catch {
    /* 拦截器已提示 */
  }
}

async function setShelf(row, value) {
  const isOff = value !== 2
  if (isOff) {
    const ok = await confirmDialog({
      title: '下架这本书？',
      message: '下架后前台将无法搜索和阅读，可随时重新上架。',
      confirmText: '下架'
    })
    if (!ok) return
  }
  try {
    await updateBookStatus(row.id, { shelf_status: value })
    row.shelf_status = value
    ElMessage.success(value === 2 ? '已上架' : '已下架')
  } catch {
    /* 拦截器已提示 */
  }
}

async function toggleRecommend(row, value) {
  try {
    await updateBookStatus(row.id, { is_recommend: value })
    row.is_recommend = value
    ElMessage.success(value ? '已加入推荐位' : '已取消推荐')
  } catch {
    /* 拦截器已提示 */
  }
}

onMounted(load)
</script>

<template>
  <el-card shadow="never" class="panel">
    <div class="bar">
      <div class="bar__left">
        <el-input
          v-model="query.keyword"
          placeholder="搜索书名"
          clearable
          style="width: 220px"
          @keyup.enter="search"
        />
        <el-select v-model="query.audit_status" placeholder="全部审核状态" clearable style="width: 150px">
          <el-option label="未提交" :value="0" />
          <el-option label="待审核" :value="1" />
          <el-option label="审核通过" :value="2" />
          <el-option label="审核未通过" :value="3" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
      </div>
      <el-button type="success" @click="openCreate">新增书籍</el-button>
    </div>

    <el-table v-loading="loading" :data="list" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="书名" min-width="150" show-overflow-tooltip />
      <el-table-column label="分类" width="110">
        <template #default="{ row }">{{ row.category?.name }}</template>
      </el-table-column>
      <el-table-column label="作者" width="110">
        <template #default="{ row }">{{ row.author?.nickname }}</template>
      </el-table-column>
      <el-table-column label="章节/字数" width="130">
        <template #default="{ row }">{{ row.chapter_count }} 章 / {{ row.word_count }} 字</template>
      </el-table-column>
      <el-table-column label="审核状态" width="110">
        <template #default="{ row }">
          <el-tag :type="auditOf(row.audit_status).type" size="small">
            {{ auditOf(row.audit_status).text }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="上架状态" width="110">
        <template #default="{ row }">
          <el-tag :type="shelfOf(row.shelf_status).type" size="small" effect="plain">
            {{ shelfOf(row.shelf_status).text }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="推荐位" width="90">
        <template #default="{ row }">
          <el-switch
            :model-value="row.is_recommend"
            @change="(value) => toggleRecommend(row, value)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openImport(row)">导入</el-button>
          <template v-if="row.audit_status === 1">
            <el-button link type="success" @click="setAudit(row, 2)">通过</el-button>
            <el-button link type="danger" @click="setAudit(row, 3)">驳回</el-button>
          </template>
          <template v-if="row.audit_status === 2">
            <el-button
              v-if="row.shelf_status !== 2"
              link
              type="success"
              @click="setShelf(row, 2)"
            >
              上架
            </el-button>
            <el-button v-else link type="danger" @click="setShelf(row, 0)">下架</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="pager"
      layout="total, prev, pager, next"
      :total="total"
      :page-size="query.size"
      :current-page="query.page"
      @current-change="(page) => { query.page = page; load() }"
    />

    <el-dialog v-model="createVisible" title="新增书籍" width="560px">
      <el-form label-width="90px">
        <el-form-item label="书名">
          <el-input v-model="createForm.title" maxlength="100" />
        </el-form-item>
        <el-form-item label="作者">
          <el-select v-model="createForm.author_id" style="width: 100%">
            <el-option
              v-for="author in authors"
              :key="author.id"
              :label="author.nickname || author.username"
              :value="author.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="createForm.category_id" style="width: 100%">
            <el-option
              v-for="cat in categories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="createForm.status">
            <el-radio :value="0">连载中</el-radio>
            <el-radio :value="1">已完结</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="createForm.intro" type="textarea" :rows="4" maxlength="2000" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>

    <ChapterImporter
      v-model="importVisible"
      :book-id="importTarget?.id"
      :book-title="importTarget?.title"
      scope="admin"
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
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.bar__left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.pager {
  margin-top: 16px;
  justify-content: flex-end;
}

.tip {
  margin: 0 0 12px;
  font-size: 13px;
  color: #7a7a7a;
}
</style>