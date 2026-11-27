<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getMyFollows, unfollowAuthor } from '@/api'
import { toast } from '@/utils/toast'
import EmptyState from '@/components/EmptyState.vue'
import UserAvatar from '@/components/UserAvatar.vue'

const router = useRouter()
const loading = ref(true)
const list = ref([])
const total = ref(0)
const query = reactive({ page: 1, size: 12 })

async function load() {
  loading.value = true
  try {
    const data = await getMyFollows({ page: query.page, size: query.size })
    list.value = data.list
    total.value = data.total
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

async function onUnfollow(item) {
  try {
    await unfollowAuthor(item.id)
    list.value = list.value.filter((x) => x.id !== item.id)
    total.value = Math.max(0, total.value - 1)
    toast('已取消关注')
  } catch {
    /* 拦截器已提示 */
  }
}

function open(item) {
  router.push(`/author/${item.id}`)
}

onMounted(load)
</script>

<template>
  <div class="mf">
    <div v-if="loading" class="skeleton" style="height: 180px"></div>

    <EmptyState
      v-else-if="!list.length"
      text="还没有关注任何作者"
      action-text="去书库看看"
      to="/search"
    />

    <template v-else>
      <ul class="mf__list">
        <li v-for="item in list" :key="item.id" class="author">
          <UserAvatar :user="item" :size="52" />
          <div class="author__info" @click="open(item)">
            <p class="author__name">{{ item.nickname || item.username }}</p>
            <p class="author__bio">{{ item.bio || '暂无简介' }}</p>
            <p class="author__meta">{{ item.book_count }} 部作品</p>
          </div>
          <div class="author__ops">
            <button class="btn" type="button" @click="open(item)">主页</button>
            <button class="btn" type="button" @click="onUnfollow(item)">取消关注</button>
          </div>
        </li>
      </ul>
    </template>
  </div>
</template>

<style scoped>
.mf {
  padding-top: 16px;
}

.mf__list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.author {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: #fff;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
}

.author__info {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.author__name {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 600;
}

.author__name:hover {
  color: var(--c-primary);
}

.author__bio {
  margin: 0 0 4px;
  font-size: 12px;
  color: var(--c-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.author__meta {
  margin: 0;
  font-size: 12px;
  color: var(--c-primary);
}

.author__ops {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.author__ops .btn {
  padding: 4px 12px;
  font-size: 12px;
}

@media (max-width: 768px) {
  .mf__list {
    grid-template-columns: 1fr;
  }
}
</style>