<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const user = useUserStore()

const menus = [
  { path: '/admin/dashboard', label: '数据看板' },
  { path: '/admin/books', label: '书籍管理' },
  { path: '/admin/categories', label: '分类管理' },
  { path: '/admin/users', label: '用户管理' },
  { path: '/admin/comments', label: '评论管理' },
  { path: '/admin/paragraph-comments', label: '间贴审核' },
  { path: '/admin/notices', label: '公告管理' },
  { path: '/admin/orders', label: '充值订单' }
]

const active = computed(() => route.path)

async function onLogout() {
  await user.doLogout()
  router.push('/')
}
</script>

<template>
  <el-config-provider :locale="zhCn">
    <el-container class="admin">
      <el-aside width="200px" class="admin__aside">
        <div class="admin__logo">轻量化小说<span>后台</span></div>
        <el-menu :default-active="active" router class="admin__menu">
          <el-menu-item v-for="menu in menus" :key="menu.path" :index="menu.path">
            {{ menu.label }}
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header class="admin__header">
          <span class="admin__title">{{ route.meta.title || '管理后台' }}</span>
          <div class="admin__actions">
            <router-link class="admin__link" to="/">返回前台</router-link>
            <el-button link type="danger" @click="onLogout">退出登录</el-button>
          </div>
        </el-header>

        <el-main class="admin__main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </el-config-provider>
</template>

<style scoped>
.admin {
  min-height: 100vh;
}

.admin__aside {
  background: #fff;
  color: var(--c-text);
  border-right: 1px solid var(--c-border);
}

.admin__logo {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 1px;
  color: var(--c-text);
}

.admin__logo span {
  margin-left: 4px;
  color: var(--c-primary);
  font-size: 13px;
  font-weight: 400;
}

.admin__menu {
  border-right: none;
  background: transparent;
}

.admin__menu :deep(.el-menu-item) {
  color: var(--c-text-secondary);
  border-radius: 6px;
  margin: 2px 10px;
  height: 42px;
}

.admin__menu :deep(.el-menu-item:hover) {
  background: var(--c-primary-soft);
  color: var(--c-primary);
}

.admin__menu :deep(.el-menu-item.is-active) {
  background: var(--c-primary-soft);
  color: var(--c-primary);
  font-weight: 600;
}

.admin__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e8e3da;
}

.admin__title {
  font-size: 15px;
  font-weight: 600;
  color: #2b2b2b;
}

.admin__actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.admin__link {
  font-size: 13px;
  color: #7a7a7a;
}

.admin__link:hover {
  color: var(--c-primary);
}

.admin__main {
  background: var(--c-bg);
  padding: 20px;
}
</style>