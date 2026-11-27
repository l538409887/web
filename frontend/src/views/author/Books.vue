<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  applyAuthor,
  applyMyBookShelf,
  createMyBook,
  getMyBooks,
  submitMyBook,
  updateMyBook
} from '@/api/author'
import { getCategories } from '@/api/admin'
import ChapterImporter from '@/components/ChapterImporter.vue'
import { useUserStore } from '@/stores/user'

const user = useUserStore()
const isAuthor = computed(() => ['author', 'admin'].includes(user.role))

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const categories = ref([])

const dialogVisible = ref(false)
const editing = ref(null)
const form = reactive({ title: '', category_id: null, intro: '', status: 0 })

const importVisible = ref(false)
const importTarget = ref(null)
const applying = ref(false)
const busyId = ref(0)

// 审核四态：0 未提交 / 1 待审核 / 2 通过 / 3 未通过
const AUDIT = {
  0: { text: '未提交', type: 'info' },
  1: { text: '待审核', type: 'warning' },
  2: { text: '审核通过', type: 'success' },
  3: { text: '审核未通过', type: 'danger' }
}

// 上架四态：0 未上架 / 1 上架审核中 / 2 已上架 / 3 上架未通过
const SHELF = {
  0: { text: '未上架', type: 'info' },
  1: { text: '上架审核中', type: 'warning' },
  2: { text: '已上架', type: 'success' },
  3: { text: '上架未通过', type: 'danger' }
}

const auditOf = (v) => AUDIT[v] || AUDIT[0]
const shelfOf = (v) => SHELF[v] || SHELF[0]

/** 能否提交审核：还没提交，或被驳回 */
const canSubmit = (row) => row.audit_status === 0 || row.audit_status === 3
/** 能否申请上架：内容审核通过，且还没上架/没在申请中 */
const canApplyShelf = (row) =>
  row.audit_status === 2 && (row.shelf_status === 0 || row.shelf_status === 3)

async function load() {
  if (!isAuthor.value) return
  loading.value = true
  try {
    const data = await getMyBooks({ page: page.value, size: pageSize })
    list.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function apply() {
  applying.value = true
  try {
    await applyAuthor()
    await user.fetchMe()
    ElMessage.success('已成为作者，可以开始创作了')
    await load()
  } catch {
    /* 拦截器已提示 */
  } finally {
    applying.value = false
  }
}

async function ensureCategories() {
  if (!categories.value.length) categories.value = await getCategories()
}

async function openCreate() {
  await ensureCategories()
  editing.value = null
  form.title = ''
  form.category_id = categories.value[0]?.id || null
  form.intro = ''
  form.status = 0
  dialogVisible.value = true
}

async function openEdit(row) {
  await ensureCategories()
  editing.value = row
  form.title = row.title
  form.category_id = row.category?.id || null
  form.intro = row.intro || ''
  form.status = row.status
  dialogVisible.value = true
}

async function submit() {
  if (!form.title.trim()) return ElMessage.warning('请填写书名')
  if (!form.category_id) return ElMessage.warning('请选择分类')
  if (!form.intro.trim()) return ElMessage.warning('请填写简介')

  const payload = {
    title: form.title.trim(),
    category_id: form.category_id,
    intro: form.intro.trim(),
    status: form.status
  }
  try {
    if (editing.value) {
      await updateMyBook(editing.value.id, payload)
      ElMessage.success('已保存')
      dialogVisible.value = false
      await load()
    } else {
      const res = await createMyBook(payload)
      ElMessage.success('作品已创建，状态为「未提交」，请提交审核')
      dialogVisible.value = false
      await load()
      openImport({ id: res.id, title: payload.title })
      return
    }
  } catch {
    /* 拦截器已提示 */
  }
}

async function doSubmit(row) {
  busyId.value = row.id
  try {
    await submitMyBook(row.id)
    row.audit_status = 1
    ElMessage.success('已提交审核，请等待管理员处理')
  } catch {
    /* 拦截器已提示 */
  } finally {
    busyId.value = 0
  }
}

async function doApplyShelf(row) {
  busyId.value = row.id
  try {
    await applyMyBookShelf(row.id)
    row.shelf_status = 1
    ElMessage.success('上架申请已提交')
  } catch {
    /* 拦截器已提示 */
  } finally {
    busyId.value = 0
  }
}

function openImport(row) {
  importTarget.value = row
  importVisible.value = true
}

onMounted(load)
</script>

<template>
  <div v-if="!isAuthor" class="apply">
    <el-card shadow="never" class="apply__card">
      <h2 class="apply__title">成为作者</h2>
      <p class="apply__desc">
        成为作者后可以创建作品、发布章节、查看统计数据。当前为自助开通，
        正式环境应改为提交申请、由管理员审核。
      </p>
      <el-button type="primary" :loading="applying" @click="apply">申请成为作者</el-button>
    </el-card>
  </div>

  <el-card v-else shadow="never" class="panel">
    <div class="bar">
      <span class="bar__title">我的作品（{{ total }}）</span>
      <el-button type="primary" @click="openCreate">新建作品</el-button>
    </div>

    <el-alert type="info" :closable="false" class="flow">
      <template #title>
        发布流程：新建作品（未提交）→ <b>提交审核</b> → 管理员审核 → 审核通过后
        <b>申请上架</b> → 管理员上架 → 前台可见
      </template>
    </el-alert>

    <el-table v-loading="loading" :data="list" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="书名" min-width="150" show-overflow-tooltip />
      <el-table-column label="分类" width="110">
        <template #default="{ row }">{{ row.category?.name }}</template>
      </el-table-column>
      <el-table-column label="章节/字数" width="140">
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
      <el-table-column label="操作" width="330" fixed="right">
        <template #default="{ row }">
          <router-link :to="`/author/books/${row.id}/chapters`">
            <el-button link type="primary">章节</el-button>
          </router-link>
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="success" @click="openImport(row)">导入</el-button>
          <el-button
            v-if="canSubmit(row)"
            link
            type="warning"
            :disabled="busyId === row.id"
            @click="doSubmit(row)"
          >
            提交审核
          </el-button>
          <el-button
            v-if="canApplyShelf(row)"
            link
            type="primary"
            :disabled="busyId === row.id"
            @click="doApplyShelf(row)"
          >
            申请上架
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="pager"
      layout="total, prev, pager, next"
      :total="total"
      :page-size="pageSize"
      :current-page="page"
      @current-change="(p) => { page = p; load() }"
    />

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑作品' : '新建作品'" width="560px">
      <el-form label-width="90px">
        <el-form-item label="书名">
          <el-input v-model="form.title" maxlength="100" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category_id" style="width: 100%">
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="0">连载中</el-radio>
            <el-radio :value="1">已完结</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.intro" type="textarea" :rows="4" maxlength="2000" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>

    <ChapterImporter
      v-model="importVisible"
      :book-id="importTarget?.id"
      :book-title="importTarget?.title"
      scope="author"
      @done="load"
    />
  </el-card>
</template>

<style scoped>
.apply {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

.apply__card {
  max-width: 520px;
  border: 1px solid #e8e3da;
  border-radius: 8px;
  text-align: center;
}

.apply__title {
  margin: 0 0 12px;
  font-size: 20px;
  color: var(--c-primary);
}

.apply__desc {
  margin: 0 0 24px;
  font-size: 13px;
  line-height: 1.9;
  color: #7a7a7a;
}

.panel {
  border: 1px solid #e8e3da;
  border-radius: 8px;
}

.bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.bar__title {
  font-size: 14px;
  font-weight: 600;
  color: #2b2b2b;
}

.flow {
  margin-bottom: 14px;
}

.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
