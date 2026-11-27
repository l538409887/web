<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const user = useUserStore()

const menus = computed(() => [
  { path: '/author/books', label: '我的作品' }
])

const active = computed(() => (route.path.startsWith('/author/books') ? '/author/books' : route.path))

async function onLogout() {
  await user.doLogout()
  router.push('/')
}
</script>

<template>
  <el-config-provider :locale="zhCn">
    <el-container class="author">
      <el-aside width="200px" class="author__aside">
        <div class="author__logo">轻量化小说<span>作者中心</span></div>
        <el-menu :default-active="active" router class="author__menu">
          <el-menu-item v-for="menu in menus" :key="menu.path" :index="menu.path">
            {{ menu.label }}
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header class="author__header">
          <span class="author__title">{{ route.meta.title || '作者中心' }}</span>
          <div class="author__actions">
            <router-link class="author__link" to="/">返回前台</router-link>
            <el-button link type="danger" @click="onLogout">退出登录</el-button>
          </div>
        </el-header>

        <el-main class="author__main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </el-config-provider>
</template>

<style scoped>
.author {
  min-height: 100vh;
}

.author__aside {
  background: #fff;
  color: var(--c-text);
  border-right: 1px solid var(--c-border);
}

.author__logo {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 1px;
  color: var(--c-text);
}

.author__logo span {
  margin-left: 4px;
  color: var(--c-primary);
  font-size: 13px;
  font-weight: 400;
}

.author__menu {
  border-right: none;
  background: transparent;
}

.author__menu :deep(.el-menu-item) {
  color: var(--c-text-secondary);
  border-radius: 6px;
  margin: 2px 10px;
  height: 42px;
}

.author__menu :deep(.el-menu-item:hover) {
  background: var(--c-primary-soft);
  color: var(--c-primary);
}

.author__menu :deep(.el-menu-item.is-active) {
  background: var(--c-primary-soft);
  color: var(--c-primary);
  font-weight: 600;
}

.author__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e8e3da;
}

.author__title {
  font-size: 15px;
  font-weight: 600;
  color: #2b2b2b;
}

.author__actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.author__link {
  font-size: 13px;
  color: #7a7a7a;
}

.author__link:hover {
  color: var(--c-primary);
}

.author__main {
  background: var(--c-bg);
  padding: 20px;
}
</style>