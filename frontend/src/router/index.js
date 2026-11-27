import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  { path: '/', name: 'Home', component: () => import('@/views/Home.vue'), meta: { title: '首页' } },
  {
    path: '/book/:id(\\d+)',
    name: 'BookDetail',
    component: () => import('@/views/BookDetail.vue'),
    meta: { title: '书籍详情' }
  },
  {
    path: '/read/:chapterId(\\d+)',
    name: 'Reader',
    component: () => import('@/views/Reader.vue'),
    meta: { title: '阅读', fullscreen: true }
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('@/views/Search.vue'),
    meta: { title: '搜索' }
  },
  {
    path: '/rank',
    name: 'Rank',
    component: () => import('@/views/Rank.vue'),
    meta: { title: '排行榜' }
  },
  {
    path: '/rank/:key',
    name: 'RankDetail',
    component: () => import('@/views/RankDetail.vue'),
    meta: { title: '榜单详情' }
  },
  {
    path: '/author/:id(\\d+)',
    name: 'AuthorHome',
    component: () => import('@/views/AuthorHome.vue'),
    meta: { title: '作者主页' }
  },
  {
    path: '/shelf',
    name: 'Shelf',
    component: () => import('@/views/Shelf.vue'),
    meta: { requiresAuth: true, title: '我的书架' }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { guestOnly: true, title: '登录' }
  },
  {
    path: '/user',
    name: 'UserCenter',
    component: () => import('@/views/UserCenter.vue'),
    meta: { requiresAuth: true, title: '个人中心' }
  },
  {
    path: '/author',
    component: () => import('@/layouts/AuthorLayout.vue'),
    meta: { requiresAuth: true, title: '作者中心' },
    children: [
      { path: '', redirect: '/author/books' },
      {
        path: 'books',
        name: 'AuthorBooks',
        component: () => import('@/views/author/Books.vue'),
        meta: { title: '我的作品' }
      },
      {
        path: 'books/:id(\\d+)/chapters',
        name: 'AuthorChapters',
        component: () => import('@/views/author/Chapters.vue'),
        meta: { title: '章节管理' }
      }
    ]
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, roles: ['admin'], title: '管理后台' },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '数据看板' }
      },
      {
        path: 'books',
        name: 'AdminBooks',
        component: () => import('@/views/admin/Books.vue'),
        meta: { title: '书籍管理' }
      },
      {
        path: 'categories',
        name: 'AdminCategories',
        component: () => import('@/views/admin/Categories.vue'),
        meta: { title: '分类管理' }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/Users.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'comments',
        name: 'AdminComments',
        component: () => import('@/views/admin/Comments.vue'),
        meta: { title: '评论管理' }
      },
      {
        path: 'reports',
        name: 'AdminReports',
        component: () => import('@/views/admin/Reports.vue'),
        meta: { title: '举报处理' }
      },
      {
        path: 'notices',
        name: 'AdminNotices',
        component: () => import('@/views/admin/Notices.vue'),
        meta: { title: '公告管理' }
      },
      {
        path: 'paragraph-comments',
        name: 'AdminParagraphComments',
        component: () => import('@/views/admin/ParagraphComments.vue'),
        meta: { title: '间贴审核' }
      },
      {
        path: 'orders',
        name: 'AdminOrders',
        component: () => import('@/views/admin/Orders.vue'),
        meta: { title: '充值订单' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.beforeEach(async (to) => {
  document.title = to.meta.title ? `${to.meta.title} · 轻量化小说平台` : '轻量化小说平台'

  const user = useUserStore()
  if (!user.initialized) await user.fetchMe()

  if (to.meta.requiresAuth && !user.isLogin) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.roles && !to.meta.roles.includes(user.role)) {
    return { path: '/' }
  }
  if (to.meta.guestOnly && user.isLogin) {
    return { path: '/' }
  }
  return true
})

export default router