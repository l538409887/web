<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import {
  changePassword,
  deleteComment,
  getHistory,
  getMyComments,
  updateProfile,
  uploadImage
} from '@/api'
import { useUserStore } from '@/stores/user'
import { useReaderStore } from '@/stores/reader'
import { confirmDialog } from '@/composables/useConfirm'
import EmptyState from '@/components/EmptyState.vue'
import WalletPanel from '@/components/WalletPanel.vue'
import MyParagraphComments from '@/components/MyParagraphComments.vue'
import MyFollows from '@/components/MyFollows.vue'

const router = useRouter()
const user = useUserStore()
const reader = useReaderStore()

const tab = ref('profile')
const saving = ref(false)
const uploading = ref(false)
const form = reactive({ nickname: '', bio: '' })

const pwd = reactive({ old: '', new: '', confirm: '' })
const pwdSaving = ref(false)

const historyLoading = ref(false)
const historyList = ref([])

const commentLoading = ref(false)
const commentList = ref([])
const commentTotal = ref(0)
const commentPage = ref(1)
const commentSize = 10

const profile = computed(() => user.profile || {})
const initial = computed(() => (profile.value.nickname || profile.value.username || '读').slice(0, 1))

const roleLabel = computed(() => {
  const map = { reader: '读者', author: '作者', admin: '管理员' }
  return map[profile.value.role] || '读者'
})

const themes = [
  { key: 'white', label: '白', color: '#FFFFFF' },
  { key: 'sepia', label: '米黄', color: '#F5EFE3' },
  { key: 'green', label: '护眼', color: '#D8E6D5' },
  { key: 'dark', label: '夜间', color: '#1A1A1A' }
]

function fillForm() {
  form.nickname = profile.value.nickname || ''
  form.bio = profile.value.bio || ''
}

async function saveProfile() {
  if (!form.nickname.trim()) {
    ElMessage.warning('昵称不能为空')
    return
  }
  saving.value = true
  try {
    await updateProfile({ nickname: form.nickname.trim(), bio: form.bio.trim() })
    await user.fetchMe()
    fillForm()
    ElMessage.success('资料已保存')
  } catch {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}

async function onAvatarChange(event) {
  const file = event.target.files && event.target.files[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件')
    event.target.value = ''
    return
  }
  uploading.value = true
  try {
    const res = await uploadImage(file, 'avatar')
    await updateProfile({ avatar: res.url })
    await user.fetchMe()
    ElMessage.success('头像已更新')
  } catch {
    /* 拦截器已提示 */
  } finally {
    uploading.value = false
    event.target.value = ''
  }
}

async function savePassword() {
  if (!pwd.old || !pwd.new) {
    ElMessage.warning('请填写原密码和新密码')
    return
  }
  if (pwd.new.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  if (pwd.new !== pwd.confirm) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  pwdSaving.value = true
  try {
    await changePassword({ old_password: pwd.old, new_password: pwd.new })
    ElMessage.success('密码已修改，请重新登录')
    await user.doLogout()
    router.push('/login')
  } catch {
    /* 拦截器已提示 */
  } finally {
    pwdSaving.value = false
  }
}

async function loadHistory() {
  historyLoading.value = true
  try {
    const data = await getHistory(20)
    historyList.value = data.list
  } finally {
    historyLoading.value = false
  }
}

async function loadComments() {
  commentLoading.value = true
  try {
    const data = await getMyComments({ page: commentPage.value, size: commentSize })
    commentList.value = data.list
    commentTotal.value = data.total
  } finally {
    commentLoading.value = false
  }
}

async function removeComment(row) {
  const confirmed = await confirmDialog({
    title: '删除这条评论？',
    message: row.chapter_title ? '删除后不可恢复。' : '删除后，其下回复也会一并隐藏，且不可恢复。',
    confirmText: '删除'
  })
  if (!confirmed) return
  try {
    await deleteComment(row.id)
    ElMessage.success('已删除')
    await loadComments()
  } catch {
    /* 拦截器已提示 */
  }
}

function onTabChange(name) {
  if (name === 'history' && !historyList.value.length) loadHistory()
  if (name === 'comments' && !commentList.value.length) loadComments()
}

onMounted(async () => {
  if (!user.profile) await user.fetchMe()
  fillForm()
  reader.applyTheme()
})
</script>

<template>
  <div class="container user">
    <div class="user__hero">
      <label class="user__avatar">
        <input type="file" accept="image/*" @change="onAvatarChange" />
        <img v-if="profile.avatar" :src="profile.avatar" :alt="profile.nickname" />
        <span v-else class="user__avatar-text">{{ initial }}</span>
        <span class="user__avatar-mask">{{ uploading ? '上传中…' : '更换' }}</span>
      </label>

      <div class="user__intro">
        <h1 class="user__name">{{ profile.nickname || profile.username }}</h1>
        <p class="user__meta">
          {{ profile.username }}
          <el-tag size="small" effect="plain">{{ roleLabel }}</el-tag>
          <span v-if="profile.email">· {{ profile.email }}</span>
        </p>
        <p v-if="profile.bio" class="user__bio">{{ profile.bio }}</p>
      </div>
    </div>

    <el-tabs v-model="tab" class="user__tabs" @tab-change="onTabChange">
      <el-tab-pane label="资料" name="profile">
        <el-form label-width="90px" class="user__form">
          <el-form-item label="昵称">
            <el-input v-model="form.nickname" maxlength="20" show-word-limit />
          </el-form-item>
          <el-form-item label="个性简介">
            <el-input v-model="form.bio" type="textarea" :rows="3" maxlength="120" show-word-limit />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="saving" @click="saveProfile">保存资料</el-button>
          </el-form-item>
        </el-form>

        <el-descriptions :column="2" border class="user__info">
          <el-descriptions-item label="用户名">{{ profile.username }}</el-descriptions-item>
          <el-descriptions-item label="账号角色">{{ roleLabel }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ profile.email || '未绑定' }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ profile.created_at }}</el-descriptions-item>
          <el-descriptions-item label="最后登录" :span="2">
            {{ profile.last_login_at || '—' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>

      <el-tab-pane label="账号安全" name="security">
        <el-form label-width="90px" class="user__form">
          <el-form-item label="原密码">
            <el-input v-model="pwd.old" type="password" autocomplete="current-password" show-password />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="pwd.new" type="password" autocomplete="new-password" show-password placeholder="至少 6 位" />
          </el-form-item>
          <el-form-item label="确认新密码">
            <el-input v-model="pwd.confirm" type="password" autocomplete="new-password" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="pwdSaving" @click="savePassword">修改密码</el-button>
            <span class="user__hint">修改成功后需要重新登录</span>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="我的关注" name="follows">
        <MyFollows />
      </el-tab-pane>

      <el-tab-pane label="我的间贴" name="paragraphs">
        <MyParagraphComments />
      </el-tab-pane>

      <el-tab-pane label="钱包" name="wallet">
        <WalletPanel />
      </el-tab-pane>

      <el-tab-pane label="阅读设置" name="reader">
        <div class="reader-set">
          <div class="reader-set__row">
            <span class="reader-set__label">字号</span>
            <el-slider
              :model-value="reader.settings.fontSize"
              :min="14"
              :max="24"
              :step="2"
              show-stops
              @update:model-value="(v) => reader.setFontSize(v)"
            />
            <span class="reader-set__value">{{ reader.settings.fontSize }}px</span>
          </div>

          <div class="reader-set__row">
            <span class="reader-set__label">行距</span>
            <el-slider
              :model-value="reader.settings.lineHeight * 10"
              :min="16"
              :max="24"
              :step="2"
              show-stops
              @update:model-value="(v) => reader.setLineHeight(v / 10)"
            />
            <span class="reader-set__value">{{ reader.settings.lineHeight.toFixed(1) }}</span>
          </div>

          <div class="reader-set__row">
            <span class="reader-set__label">背景</span>
            <div class="reader-set__themes">
              <button
                v-for="theme in themes"
                :key="theme.key"
                class="reader-set__theme"
                :class="{ 'reader-set__theme--active': reader.settings.theme === theme.key }"
                :style="{ background: theme.color }"
                type="button"
                @click="reader.setTheme(theme.key)"
              >
                {{ theme.label }}
              </button>
            </div>
          </div>

          <div class="reader-set__preview">
            <p class="reader-set__preview-label">预览效果</p>
            <p class="reader-set__preview-text">
              　　少年提剑下山，山门在身后缓缓合上。他知道，这一走，未必还能回来。
              江湖上的消息总比风跑得快，三天之内，半个中原都知道了那个名字。
            </p>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="阅读记录" name="history">
        <div v-loading="historyLoading">
          <EmptyState
            v-if="!historyLoading && !historyList.length"
            text="还没有阅读记录"
            action-text="去首页看看"
            to="/"
          />
          <ul v-else class="history">
            <li v-for="item in historyList" :key="item.book.id" class="history__item">
              <router-link class="history__cover" :to="`/book/${item.book.id}`">
                {{ item.book.title.slice(0, 2) }}
              </router-link>
              <div class="history__main">
                <router-link class="history__title" :to="`/book/${item.book.id}`">
                  {{ item.book.title }}
                </router-link>
                <p class="history__meta">
                  读到 第 {{ item.chapter.chapter_no }} 章 · {{ item.progress }}% ·
                  {{ item.updated_at }}
                </p>
              </div>
              <router-link class="btn btn--primary" :to="`/read/${item.chapter.id}`">
                继续阅读
              </router-link>
            </li>
          </ul>
        </div>
      </el-tab-pane>

      <el-tab-pane label="我的评论" name="comments">
        <div v-loading="commentLoading">
          <EmptyState
            v-if="!commentLoading && !commentList.length"
            text="还没有发表过评论"
            action-text="去逛逛"
            to="/"
          />
          <ul v-else class="comments">
            <li v-for="item in commentList" :key="item.id" class="comments__item">
              <div class="comments__top">
                <router-link class="comments__where" :to="`/book/${item.book_id}`">
                  {{ item.book_title }}
                </router-link>
                <span v-if="item.chapter_title" class="comments__chapter">
                  · {{ item.chapter_title }}
                </span>
                <el-tag v-if="item.status === 2" type="info" size="small">已隐藏</el-tag>
                <span class="comments__time">{{ item.created_at }}</span>
              </div>
              <p class="comments__text">{{ item.content }}</p>
              <div class="comments__ops">
                <el-button v-if="item.status !== 2" link type="danger" @click="removeComment(item)">
                  删除
                </el-button>
              </div>
            </li>
          </ul>

          <el-pagination
            v-if="commentTotal > commentSize"
            class="comments__pager"
            layout="prev, pager, next"
            :total="commentTotal"
            :page-size="commentSize"
            :current-page="commentPage"
            @current-change="(p) => { commentPage = p; loadComments() }"
          />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.user {
  padding-top: 28px;
  padding-bottom: 48px;
}

.user__hero {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  margin-bottom: 12px;
}

.user__avatar {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  background: linear-gradient(135deg, var(--c-primary), #d93e73);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user__avatar input {
  display: none;
}

.user__avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user__avatar-text {
  font-size: 26px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
}

.user__avatar-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.16s ease;
}

.user__avatar:hover .user__avatar-mask {
  opacity: 1;
}

.user__intro {
  min-width: 0;
}

.user__name {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 600;
}

.user__meta {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--c-text-muted);
  flex-wrap: wrap;
}

.user__bio {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--c-text-secondary);
}

.user__tabs :deep(.el-tabs__item) {
  font-size: 14px;
}

.user__form {
  max-width: 460px;
  margin-top: 16px;
}

.user__info {
  margin-top: 8px;
  max-width: 720px;
}

.user__hint {
  margin-left: 12px;
  font-size: 12px;
  color: var(--c-text-muted);
}

.reader-set {
  max-width: 560px;
  margin-top: 16px;
}

.reader-set__row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
}

.reader-set__label {
  width: 44px;
  font-size: 13px;
  color: var(--c-text-secondary);
  flex-shrink: 0;
}

.reader-set__row .el-slider {
  flex: 1;
}

.reader-set__value {
  width: 54px;
  text-align: right;
  font-size: 13px;
  color: var(--c-text-muted);
}

.reader-set__themes {
  display: flex;
  gap: 10px;
}

.reader-set__theme {
  width: 60px;
  height: 34px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: #666;
}

.reader-set__theme--active {
  outline: 2px solid var(--c-accent);
  outline-offset: 1px;
}

.reader-set__preview {
  margin-top: 8px;
  padding: 18px 20px;
  border-radius: var(--radius-md);
  background: var(--reader-bg);
  border: 1px solid var(--reader-border);
}

.reader-set__preview-label {
  margin: 0 0 10px;
  font-size: 12px;
  color: #a8a39a;
}

.reader-set__preview-text {
  margin: 0;
  font-family: 'Songti SC', 'Noto Serif SC', 'SimSun', serif;
  font-size: var(--reader-font-size);
  line-height: var(--reader-line-height);
  color: var(--reader-text);
}

.history {
  margin: 16px 0 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.history__item {
  display: grid;
  grid-template-columns: 48px 1fr auto;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
}

.history__cover {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 64px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--c-primary), #d93e73);
  color: rgba(255, 255, 255, 0.92);
  font-size: 13px;
  font-weight: 600;
  font-family: 'Songti SC', 'Noto Serif SC', serif;
}

.history__title {
  font-size: 15px;
  font-weight: 600;
}

.history__title:hover {
  color: var(--c-primary);
}

.history__meta {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--c-text-muted);
}

.comments {
  margin: 16px 0 0;
  padding: 0;
  list-style: none;
}

.comments__item {
  padding: 16px 0;
  border-bottom: 1px solid var(--c-border);
}

.comments__top {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.comments__where {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-primary);
}

.comments__chapter {
  font-size: 12px;
  color: var(--c-text-muted);
}

.comments__time {
  margin-left: auto;
  font-size: 12px;
  color: var(--c-text-muted);
}

.comments__text {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.75;
  color: var(--c-text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}

.comments__ops {
  margin-top: 6px;
}

.comments__pager {
  margin-top: 16px;
  justify-content: flex-end;
}

@media (max-width: 640px) {
  .history__item {
    grid-template-columns: 48px 1fr;
  }
  .history__item .btn {
    grid-column: 1 / -1;
  }
}
</style>