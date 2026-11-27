<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import {
  changePassword,
  deleteComment,
  getAuthor,
  getHistory,
  getMyComments,
  getMyFollows,
  getShelf,
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
import MyNotices from '@/components/MyNotices.vue'

const router = useRouter()
const route = useRoute()
const user = useUserStore()
const reader = useReaderStore()

const VALID_TABS = [
  'profile',
  'security',
  'notices',
  'follows',
  'paragraphs',
  'wallet',
  'reader',
  'history',
  'comments'
]
const tab = ref(VALID_TABS.includes(route.query.tab) ? route.query.tab : 'profile')
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

// 顶部数据条：书架 / 足迹 / 关注 / 粉丝
const stats = reactive({ shelf: 0, history: 0, follows: 0, fans: 0 })

const profile = computed(() => user.profile || {})
const initial = computed(() => (profile.value.nickname || profile.value.username || '读').slice(0, 1))

const roleLabel = computed(() => {
  const map = { reader: '读者', author: '作者', admin: '管理员' }
  return map[profile.value.role] || '读者'
})

/** 书龄：按注册时间算天数 */
const ageDays = computed(() => {
  const created = profile.value.created_at
  if (!created) return 0
  const start = new Date(String(created).replace(' ', 'T'))
  if (Number.isNaN(start.getTime())) return 0
  return Math.max(0, Math.floor((Date.now() - start.getTime()) / 86400000))
})

const ageLabel = computed(() => {
  const days = ageDays.value
  if (!days) return '今天加入'
  if (days < 30) return `书龄 ${days} 天`
  if (days < 365) return `书龄 ${Math.floor(days / 30)} 个月`
  return `书龄 ${(days / 365).toFixed(1)} 年`
})

// 左侧导航：与猫站一致，第一项「我的书架」直接跳到独立书架页
const NAV = [
  { key: 'shelf', icon: '📚', label: '我的书架', to: '/shelf' },
  { key: 'notices', icon: '✉️', label: '我的消息' },
  { key: 'comments', icon: '⭐', label: '我的书评' },
  { key: 'paragraphs', icon: '💭', label: '我的间贴' },
  { key: 'wallet', icon: '👛', label: '钱包君' },
  { key: 'follows', icon: '👥', label: '我的关注' },
  { key: 'history', icon: '🕘', label: '阅读记录' },
  { key: 'reader', icon: '⚙️', label: '阅读设置' },
  { key: 'profile', icon: '🙂', label: '基本资料' },
  { key: 'security', icon: '🔒', label: '账号安全' }
]

const CURRENT_TITLE = {
  profile: '基本资料',
  security: '账号安全',
  notices: '我的消息',
  follows: '我的关注',
  paragraphs: '我的间贴',
  wallet: '钱包君',
  reader: '阅读设置',
  history: '阅读记录',
  comments: '我的书评'
}

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

async function loadStats() {
  try {
    const [shelf, history, follows] = await Promise.all([
      getShelf({ page: 1, size: 1 }),
      getHistory(50),
      getMyFollows({ page: 1, size: 1 })
    ])
    stats.shelf = shelf.total || 0
    stats.history = (history.list || []).length
    stats.follows = follows.total || 0

    // 粉丝数只有作者/管理员才有意义
    if (['author', 'admin'].includes(profile.value.role) && profile.value.id) {
      const author = await getAuthor(profile.value.id)
      stats.fans = author.follower_count || 0
    } else {
      stats.fans = 0
    }
  } catch {
    /* 统计失败不影响页面 */
  }
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

function switchTab(name) {
  if (!VALID_TABS.includes(name)) return
  tab.value = name
  onTabChange(name)
}

function onTabChange(name) {
  if (name === 'history' && !historyList.value.length) loadHistory()
  if (name === 'comments' && !commentList.value.length) loadComments()
}

async function doLogout() {
  await user.doLogout()
  router.push('/')
}

onMounted(async () => {
  if (!user.profile) await user.fetchMe()
  fillForm()
  reader.applyTheme()
  loadStats()
  onTabChange(tab.value)
})
</script>

<template>
  <div class="container uc">
    <!-- 顶部深色头图：昵称 / 角色 / 快捷按钮 / 数据条 / 头像压边 -->
    <section class="hero">
      <h1 class="hero__name">{{ profile.nickname || profile.username }}</h1>
      <p class="hero__sub">{{ roleLabel }} · {{ ageLabel }} · {{ profile.username }}</p>

      <div class="hero__btns">
        <button class="hero__btn hero__btn--primary" type="button" @click="switchTab('wallet')">
          充值
        </button>
        <button class="hero__btn hero__btn--ghost" type="button" @click="doLogout">退出</button>
      </div>

      <div class="hero__stats">
        <button class="stat" type="button" @click="router.push('/shelf')">
          <span class="stat__num">{{ stats.shelf }}</span>
          <span class="stat__label">书架</span>
        </button>
        <button class="stat" type="button" @click="switchTab('history')">
          <span class="stat__num">{{ stats.history }}</span>
          <span class="stat__label">足迹</span>
        </button>
        <button class="stat" type="button" @click="switchTab('follows')">
          <span class="stat__num">{{ stats.follows }}</span>
          <span class="stat__label">关注</span>
        </button>
        <button class="stat" type="button" @click="switchTab('follows')">
          <span class="stat__num">{{ stats.fans }}</span>
          <span class="stat__label">粉丝</span>
        </button>
      </div>

      <label class="hero__avatar">
        <input type="file" accept="image/*" @change="onAvatarChange" />
        <img v-if="profile.avatar" :src="profile.avatar" :alt="profile.nickname" />
        <span v-else class="hero__avatar-text">{{ initial }}</span>
        <span class="hero__avatar-mask">{{ uploading ? '上传中…' : '更换' }}</span>
      </label>
    </section>

    <div class="uc__body">
      <!-- 左侧竖导航 -->
      <aside class="side">
        <nav class="side__nav">
          <component
            :is="item.to ? 'router-link' : 'button'"
            v-for="item in NAV"
            :key="item.key"
            :to="item.to"
            class="side__item"
            :class="{ 'side__item--on': !item.to && tab === item.key }"
            @click="!item.to && switchTab(item.key)"
          >
            <span class="side__ico">{{ item.icon }}</span>
            <span class="side__label">{{ item.label }}</span>
          </component>
        </nav>

        <div class="side__recent">
          <h3 class="side__recent-title">最近阅读</h3>
          <ul v-if="historyList.length" class="side__recent-list">
            <li v-for="item in historyList.slice(0, 3)" :key="item.book.id">
              <router-link :to="`/read/${item.chapter.id}`">{{ item.book.title }}</router-link>
            </li>
          </ul>
          <p v-else class="side__recent-empty">暂无阅读记录</p>
        </div>
      </aside>

      <!-- 右侧内容区 -->
      <main class="main">
        <h2 class="main__title">{{ CURRENT_TITLE[tab] }}</h2>

        <!-- 基本资料 -->
        <div v-if="tab === 'profile'" class="pane">
          <el-form label-width="90px" class="form">
            <el-form-item label="昵称">
              <el-input v-model="form.nickname" maxlength="20" show-word-limit />
            </el-form-item>
            <el-form-item label="个性简介">
              <el-input
                v-model="form.bio"
                type="textarea"
                :rows="3"
                maxlength="120"
                show-word-limit
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="saveProfile">保存资料</el-button>
            </el-form-item>
          </el-form>

          <el-descriptions :column="2" border class="desc">
            <el-descriptions-item label="账户名">{{ profile.username }}</el-descriptions-item>
            <el-descriptions-item label="账号角色">{{ roleLabel }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ profile.email || '未绑定' }}</el-descriptions-item>
            <el-descriptions-item label="注册时间">{{ profile.created_at }}</el-descriptions-item>
            <el-descriptions-item label="最后登录" :span="2">
              {{ profile.last_login_at || '—' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 账号安全 -->
        <div v-else-if="tab === 'security'" class="pane">
          <el-form label-width="90px" class="form">
            <el-form-item label="原密码">
              <el-input
                v-model="pwd.old"
                type="password"
                autocomplete="current-password"
                show-password
              />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input
                v-model="pwd.new"
                type="password"
                autocomplete="new-password"
                show-password
                placeholder="至少 6 位"
              />
            </el-form-item>
            <el-form-item label="确认新密码">
              <el-input
                v-model="pwd.confirm"
                type="password"
                autocomplete="new-password"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="pwdSaving" @click="savePassword">
                修改密码
              </el-button>
              <span class="hint">修改成功后需要重新登录</span>
            </el-form-item>
          </el-form>
        </div>

        <MyNotices v-else-if="tab === 'notices'" />
        <MyFollows v-else-if="tab === 'follows'" />
        <MyParagraphComments v-else-if="tab === 'paragraphs'" />
        <WalletPanel v-else-if="tab === 'wallet'" />

        <!-- 阅读设置 -->
        <div v-else-if="tab === 'reader'" class="pane">
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
        </div>

        <!-- 阅读记录 -->
        <div v-else-if="tab === 'history'" v-loading="historyLoading" class="pane">
          <EmptyState
            v-if="!historyLoading && !historyList.length"
            text="还没有阅读记录"
            action-text="去首页看看"
            to="/"
          />
          <ul v-else class="rowlist">
            <li v-for="item in historyList" :key="item.book.id" class="rowlist__item">
              <router-link class="rowlist__thumb" :to="`/book/${item.book.id}`">
                {{ item.book.title.slice(0, 2) }}
              </router-link>
              <div class="rowlist__main">
                <router-link class="rowlist__title" :to="`/book/${item.book.id}`">
                  {{ item.book.title }}
                </router-link>
                <p class="rowlist__meta">
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

        <!-- 我的书评 -->
        <div v-else-if="tab === 'comments'" v-loading="commentLoading" class="pane">
          <EmptyState
            v-if="!commentLoading && !commentList.length"
            text="还没有发表过书评"
            action-text="去逛逛"
            to="/"
          />
          <ul v-else class="rowlist">
            <li v-for="item in commentList" :key="item.id" class="rowlist__item rowlist__item--col">
              <div class="rowlist__top">
                <router-link class="rowlist__where" :to="`/book/${item.book_id}`">
                  {{ item.book_title }}
                </router-link>
                <span v-if="item.chapter_title" class="rowlist__chapter">
                  · {{ item.chapter_title }}
                </span>
                <el-tag v-if="item.status === 2" type="info" size="small">已隐藏</el-tag>
                <span class="rowlist__time">{{ item.created_at }}</span>
              </div>
              <p class="rowlist__text">{{ item.content }}</p>
              <div class="rowlist__ops">
                <el-button
                  v-if="item.status !== 2"
                  link
                  type="danger"
                  @click="removeComment(item)"
                >
                  删除
                </el-button>
              </div>
            </li>
          </ul>

          <el-pagination
            v-if="commentTotal > commentSize"
            class="pager"
            layout="prev, pager, next"
            :total="commentTotal"
            :page-size="commentSize"
            :current-page="commentPage"
            @current-change="(p) => { commentPage = p; loadComments() }"
          />
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.uc {
  padding: 18px 0 48px;
}

/* ---------------- 顶部头图 ---------------- */
.hero {
  position: relative;
  padding: 30px 0 52px;
  border-radius: 14px;
  background: linear-gradient(135deg, #2c2431 0%, #201b26 52%, #2d2333 100%);
  text-align: center;
  color: #fff;
  overflow: visible;
}

/* 细点阵纹理，替代猫站的猫爪暗纹 */
.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 14px;
  background-image: radial-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-size: 18px 18px;
  pointer-events: none;
}

.hero__name {
  position: relative;
  margin: 0;
  font-size: 27px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.hero__sub {
  position: relative;
  margin: 7px 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
}

.hero__btns {
  position: relative;
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 18px;
}

.hero__btn {
  min-width: 104px;
  height: 34px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.hero__btn--primary {
  border: 1px solid var(--c-primary);
  background: var(--c-primary);
  color: #fff;
}

.hero__btn--primary:hover {
  filter: brightness(1.06);
}

.hero__btn--ghost {
  border: 1px solid rgba(255, 255, 255, 0.45);
  background: transparent;
  color: #fff;
}

.hero__btn--ghost:hover {
  border-color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.hero__stats {
  position: relative;
  display: flex;
  justify-content: center;
  margin-top: 22px;
}

.stat {
  width: 118px;
  border: none;
  background: transparent;
  color: #fff;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
}

.stat__num {
  font-size: 21px;
  font-weight: 600;
  line-height: 1.1;
}

.stat__label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.stat:hover .stat__label {
  color: rgba(255, 255, 255, 0.8);
}

.hero__avatar {
  position: absolute;
  left: 50%;
  bottom: -44px;
  width: 88px;
  height: 88px;
  margin-left: -44px;
  border: 3px solid #fff;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.14);
  overflow: hidden;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero__avatar input {
  display: none;
}

.hero__avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero__avatar-text {
  font-size: 30px;
  color: var(--c-primary);
  font-weight: 600;
}

.hero__avatar-mask {
  position: absolute;
  inset: auto 0 0;
  height: 26px;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 11px;
  line-height: 26px;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.hero__avatar:hover .hero__avatar-mask {
  opacity: 1;
}

/* ---------------- 主体：左导航 + 内容 ---------------- */
.uc__body {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-top: 58px;
}

.side {
  width: 196px;
  flex-shrink: 0;
}

.side__nav {
  padding: 8px;
  background: #fff;
  border: 1px solid var(--c-border);
  border-radius: 12px;
}

.side__item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  height: 46px;
  padding: 0 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  font-size: 14px;
  color: #5a5560;
  text-align: left;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.side__item:hover {
  background: #faf7f9;
  color: var(--c-text);
}

.side__item--on {
  background: #fff4f8;
  color: var(--c-primary);
  font-weight: 600;
}

.side__ico {
  width: 18px;
  text-align: center;
  font-size: 14px;
}

.side__recent {
  margin-top: 14px;
  padding: 16px;
  background: #fff;
  border: 1px solid var(--c-border);
  border-radius: 12px;
}

.side__recent-title {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 700;
  color: var(--c-text);
}

.side__recent-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.side__recent-list li {
  padding: 6px 0;
  font-size: 13px;
  border-bottom: 1px dashed var(--c-border);
}

.side__recent-list li:last-child {
  border-bottom: none;
}

.side__recent-list a {
  color: var(--c-text-secondary);
  text-decoration: none;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.side__recent-list a:hover {
  color: var(--c-primary);
}

.side__recent-empty {
  margin: 0;
  font-size: 13px;
  color: var(--c-text-muted);
}

.main {
  flex: 1;
  min-width: 0;
  padding: 20px 24px 28px;
  background: #fff;
  border: 1px solid var(--c-border);
  border-radius: 12px;
}

.main__title {
  margin: 0 0 18px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--c-border);
  font-size: 17px;
  font-weight: 700;
  color: var(--c-text);
}

.pane {
  min-height: 200px;
}

.form {
  max-width: 520px;
}

.desc {
  margin-top: 22px;
}

.hint {
  margin-left: 12px;
  font-size: 12px;
  color: var(--c-text-muted);
}

/* ---------------- 列表（阅读记录 / 书评）---------------- */
.rowlist {
  margin: 0;
  padding: 0;
  list-style: none;
}

.rowlist__item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 0;
  border-bottom: 1px solid var(--c-border);
}

.rowlist__item:last-child {
  border-bottom: none;
}

.rowlist__item--col {
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
}

.rowlist__thumb {
  width: 44px;
  height: 58px;
  flex-shrink: 0;
  border-radius: 4px;
  background: linear-gradient(140deg, #f3a6bd, #d9718f);
  color: #fff;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
}

.rowlist__main {
  flex: 1;
  min-width: 0;
}

.rowlist__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text);
  text-decoration: none;
}

.rowlist__title:hover {
  color: var(--c-primary);
}

.rowlist__meta {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--c-text-muted);
}

.rowlist__top {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.rowlist__where {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text);
  text-decoration: none;
}

.rowlist__where:hover {
  color: var(--c-primary);
}

.rowlist__chapter,
.rowlist__time {
  font-size: 12px;
  color: var(--c-text-muted);
}

.rowlist__time {
  margin-left: auto;
}

.rowlist__text {
  margin: 0;
  font-size: 13px;
  line-height: 1.8;
  color: var(--c-text-secondary);
}

.rowlist__ops {
  display: flex;
  justify-content: flex-end;
}

.pager {
  margin-top: 16px;
  justify-content: flex-end;
}

/* ---------------- 阅读设置 ---------------- */
.reader-set {
  max-width: 560px;
}

.reader-set__row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px dashed var(--c-border);
}

.reader-set__label {
  width: 44px;
  flex-shrink: 0;
  font-size: 13px;
  color: var(--c-text-secondary);
}

.reader-set__row :deep(.el-slider) {
  flex: 1;
}

.reader-set__value {
  width: 52px;
  text-align: right;
  font-size: 13px;
  color: var(--c-primary);
}

.reader-set__themes {
  display: flex;
  gap: 8px;
}

.reader-set__theme {
  width: 56px;
  height: 32px;
  border: 1px solid var(--c-border-strong);
  border-radius: 4px;
  font-size: 12px;
  color: #555;
  cursor: pointer;
}

.reader-set__theme--active {
  border-color: var(--c-primary);
  box-shadow: 0 0 0 2px rgba(242, 79, 134, 0.14);
  color: var(--c-primary);
  font-weight: 600;
}

.reader-set__preview {
  margin-top: 18px;
  padding: 16px;
  border-radius: 8px;
  background: #fafafa;
  border: 1px dashed var(--c-border-strong);
}

.reader-set__preview-label {
  margin: 0 0 8px;
  font-size: 12px;
  color: var(--c-text-muted);
}

.reader-set__preview-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.9;
  color: var(--c-text-secondary);
}

@media (max-width: 900px) {
  .uc__body {
    flex-direction: column;
  }

  .side {
    width: 100%;
  }

  .side__nav {
    display: flex;
    flex-wrap: wrap;
  }

  .side__item {
    width: auto;
  }
}
</style>
