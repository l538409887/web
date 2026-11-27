<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { followAuthor, getAuthor, getAuthorBooks, unfollowAuthor } from '@/api'
import { useUserStore } from '@/stores/user'
import { toast } from '@/utils/toast'
import BookCard from '@/components/BookCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import UserAvatar from '@/components/UserAvatar.vue'

const route = useRoute()
const router = useRouter()
const user = useUserStore()

const loading = ref(true)
const author = ref(null)
const books = ref([])
const total = ref(0)
const busy = ref(false)

async function load() {
  loading.value = true
  try {
    const id = route.params.id
    const [profile, bookPage] = await Promise.all([
      getAuthor(id),
      getAuthorBooks(id, { page: 1, size: 24 })
    ])
    author.value = profile
    books.value = bookPage.list
    total.value = bookPage.total
  } catch {
    author.value = null
  } finally {
    loading.value = false
  }
}

async function toggleFollow() {
  if (!user.isLogin) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  busy.value = true
  try {
    if (author.value.is_followed) {
      const res = await unfollowAuthor(author.value.id)
      author.value.is_followed = false
      author.value.follower_count = res.follower_count
      toast('已取消关注')
    } else {
      const res = await followAuthor(author.value.id)
      author.value.is_followed = true
      author.value.follower_count = res.follower_count
      toast('关注成功')
    }
  } catch {
    /* 拦截器已提示 */
  } finally {
    busy.value = false
  }
}

watch(() => route.params.id, load)
onMounted(load)
</script>

<template>
  <div class="container ah">
    <div v-if="loading" class="skeleton" style="height: 160px; margin-top: 20px"></div>

    <EmptyState v-else-if="!author" text="作者不存在" action-text="回首页" to="/" />

    <template v-else>
      <section class="hero">
        <UserAvatar :user="author" :size="76" />
        <div class="hero__info">
          <h1 class="hero__name">{{ author.nickname || author.username }}</h1>
          <p class="hero__bio">{{ author.bio || '这位作者还没有填写简介' }}</p>
          <p class="hero__stat">
            <span><b>{{ author.book_count }}</b> 部作品</span>
            <span><b>{{ author.follower_count }}</b> 位粉丝</span>
          </p>
        </div>
        <div class="hero__actions">
          <button
            class="btn"
            :class="author.is_followed ? '' : 'btn--primary'"
            type="button"
            :disabled="busy"
            @click="toggleFollow"
          >
            {{ author.is_followed ? '已关注' : '+ 关注' }}
          </button>
        </div>
      </section>

      <section class="block">
        <div class="block__head">
          <h2 class="block__title">全部作品</h2>
          <span class="block__count">共 {{ total }} 部</span>
        </div>

        <div v-if="books.length" class="grid-books">
          <BookCard v-for="book in books" :key="book.id" :book="book" show-meta />
        </div>
        <EmptyState v-else text="这位作者还没有上架作品" action-text="回首页" to="/" />
      </section>
    </template>
  </div>
</template>

<style scoped>
.ah {
  padding-top: 20px;
}

.hero {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 28px;
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.hero__info {
  flex: 1;
  min-width: 0;
}

.hero__name {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 700;
}

.hero__bio {
  margin: 0 0 10px;
  font-size: 13px;
  line-height: 1.8;
  color: var(--c-text-secondary);
}

.hero__stat {
  margin: 0;
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: var(--c-text-muted);
}

.hero__stat b {
  margin-right: 4px;
  color: var(--c-text);
  font-size: 15px;
}

.hero__actions {
  flex-shrink: 0;
}

.block {
  margin-top: 26px;
}

.block__head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 14px;
}

.block__title {
  margin: 0;
  font-size: 19px;
  font-weight: 700;
}

.block__count {
  font-size: 12px;
  color: var(--c-text-muted);
}

@media (max-width: 640px) {
  .hero {
    flex-wrap: wrap;
    padding: 20px;
  }
}
</style>