<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import UserAvatar from '@/components/UserAvatar.vue'
import logo from '@/assets/logo.png'

const router = useRouter()
const route = useRoute()
const user = useUserStore()

const keyword = ref(route.query.keyword || '')
const isAdmin = computed(() => user.role === 'admin')

watch(
  () => route.query.keyword,
  (value) => {
    keyword.value = value || ''
  }
)

function onSearch() {
  const kw = keyword.value.trim()
  if (!kw) return
  router.push({ path: '/search', query: { keyword: kw } })
}

async function onLogout() {
  await user.doLogout()
  router.push('/')
}
</script>

<template>
  <header class="hd">
    <div class="hd__top">
      <div class="container hd__top-inner">
        <router-link to="/" class="hd__logo">
          <img :src="logo" alt="轻量小说" />
          <span class="hd__brand">轻量小说</span>
          <span class="hd__slogan">· 轻量化阅读</span>
        </router-link>

        <div class="hd__search">
          <input
            v-model="keyword"
            type="text"
            placeholder="搜索更多作品或作者"
            @keyup.enter="onSearch"
          />
          <button type="button" @click="onSearch">搜索</button>
        </div>

        <div class="hd__user">
          <template v-if="user.isLogin">
            <router-link class="hd__entry" to="/user">
              <UserAvatar :user="user.profile" :size="30" />
              <span class="hd__name">{{ user.profile?.nickname || user.profile?.username }}</span>
            </router-link>
          </template>
          <template v-else>
            <router-link class="hd__auth" to="/login">登录</router-link>
            <span class="hd__divider">|</span>
            <router-link class="hd__auth" to="/login">注册</router-link>
          </template>
        </div>
      </div>
    </div>

    <div class="hd__nav">
      <div class="container hd__nav-inner">
        <nav class="hd__links">
          <router-link to="/" class="hd__link" :class="{ 'hd__link--on': route.path === '/' }">
            首页
          </router-link>
          <router-link
            to="/search"
            class="hd__link"
            :class="{ 'hd__link--on': route.path === '/search' }"
          >
            书库
          </router-link>
          <router-link
            to="/rank"
            class="hd__link"
            :class="{ 'hd__link--on': route.path === '/rank' }"
          >
            排行
          </router-link>
          <router-link
            to="/shelf"
            class="hd__link"
            :class="{ 'hd__link--on': route.path === '/shelf' }"
          >
            书架
          </router-link>
        </nav>

        <div class="hd__utils">
          <router-link class="hd__util" to="/author">作者后台</router-link>
          <router-link v-if="isAdmin" class="hd__util" to="/admin">管理后台</router-link>
          <router-link class="hd__util" to="/user">个人中心</router-link>
          <button v-if="user.isLogin" class="hd__util" type="button" @click="onLogout">
            退出
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.hd {
  position: sticky;
  top: 0;
  z-index: 200;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.hd__top {
  border-bottom: 1px solid #f2f2f2;
}

.hd__top-inner {
  display: flex;
  align-items: center;
  gap: 32px;
  height: 68px;
}

.hd__logo {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.hd__logo img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--c-primary-soft);
}

.hd__brand {
  font-size: 20px;
  font-weight: 700;
  color: var(--c-text);
  letter-spacing: 1px;
}

.hd__slogan {
  font-size: 12px;
  color: var(--c-text-muted);
  margin-left: -4px;
}

.hd__search {
  display: flex;
  flex: 1;
  max-width: 620px;
  height: 40px;
  border: 2px solid var(--c-primary);
  border-radius: 20px;
  overflow: hidden;
  background: #fff;
}

.hd__search input {
  flex: 1;
  border: none;
  background: transparent;
  padding: 0 18px;
  font-size: 14px;
}

.hd__search button {
  border: none;
  background: var(--c-primary);
  color: #fff;
  padding: 0 26px;
  font-size: 14px;
  letter-spacing: 2px;
}

.hd__search button:hover {
  background: var(--c-primary-light);
}

.hd__user {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.hd__entry {
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 160px;
}

.hd__name {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hd__entry:hover .hd__name {
  color: var(--c-primary);
}

.hd__auth {
  font-size: 14px;
  color: var(--c-text-secondary);
}

.hd__auth:hover {
  color: var(--c-primary);
}

.hd__divider {
  color: #ddd;
}

.hd__nav {
  border-bottom: 1px solid #f2f2f2;
}

.hd__nav-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 46px;
}

.hd__links {
  display: flex;
  gap: 30px;
}

.hd__link {
  font-size: 15px;
  color: var(--c-text);
  padding: 4px 0;
  position: relative;
}

.hd__link:hover {
  color: var(--c-primary);
}

.hd__link--on {
  color: var(--c-primary);
  font-weight: 600;
}

.hd__link--on::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: -13px;
  transform: translateX(-50%);
  width: 18px;
  height: 3px;
  border-radius: 2px;
  background: var(--c-primary);
}

.hd__utils {
  display: flex;
  align-items: center;
  gap: 20px;
}

.hd__util {
  font-size: 13px;
  color: var(--c-text-secondary);
  border: none;
  background: transparent;
  padding: 0;
}

.hd__util:hover {
  color: var(--c-primary);
}

@media (max-width: 992px) {
  .hd__slogan {
    display: none;
  }
  .hd__top-inner {
    gap: 16px;
  }
  .hd__search {
    max-width: none;
  }
  .hd__utils {
    display: none;
  }
}

@media (max-width: 640px) {
  .hd__brand {
    display: none;
  }
  .hd__links {
    gap: 18px;
  }
  .hd__link {
    font-size: 14px;
  }
  .hd__name {
    display: none;
  }
  .hd__search button {
    padding: 0 14px;
  }
}
</style>