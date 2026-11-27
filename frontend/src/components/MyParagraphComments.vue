<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getMyParagraphComments } from '@/api'
import EmptyState from '@/components/EmptyState.vue'

const router = useRouter()
const loading = ref(true)
const list = ref([])
const total = ref(0)
const query = reactive({ page: 1, size: 10 })

function formatTime(value) {
  return (value || '').replace('T', ' ').slice(0, 16)
}

async function load() {
  loading.value = true
  try {
    const data = await getMyParagraphComments({ page: query.page, size: query.size })
    list.value = data.list
    total.value = data.total
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

function jump(item) {
  router.push({
    path: `/read/${item.chapter_id}`,
    query: { para: item.paragraph_index, cid: item.id }
  })
}

onMounted(load)
</script>

<template>
  <div class="mine">
    <div v-if="loading" class="skeleton" style="height: 200px"></div>

    <EmptyState
      v-else-if="!list.length"
      text="还没有发表过间贴，去阅读页试试"
      action-text="去书库"
      to="/search"
    />

    <template v-else>
      <ul class="mine__list">
        <li v-for="item in list" :key="item.id" class="mitem" @click="jump(item)">
          <div class="mitem__head">
            <span class="mitem__book">{{ item.book_title }}</span>
            <span class="mitem__chapter">{{ item.chapter_title }}</span>
            <span class="mitem__para">第 {{ item.paragraph_index + 1 }} 段</span>
            <span v-if="item.parent_id" class="mitem__reply">回复</span>
            <span v-if="item.status === 0" class="mitem__hidden">已被隐藏</span>
          </div>

          <p v-if="item.parent_content" class="mitem__quote">
            回复「{{ item.parent_content }}」
          </p>
          <p class="mitem__content">{{ item.content }}</p>

          <div class="mitem__foot">
            <span class="mitem__stat">
              <em>👍 {{ item.like_count }}</em>
              <em>👎 {{ item.dislike_count }}</em>
              <em>💬 {{ item.reply_count }}</em>
            </span>
            <span class="mitem__time">{{ formatTime(item.created_at) }}</span>
            <span class="mitem__go">查看位置 ›</span>
          </div>
        </li>
      </ul>

      <div v-if="total > query.size" class="mine__pager">
        <button
          class="pager__btn"
          type="button"
          :disabled="query.page <= 1"
          @click="query.page -= 1; load()"
        >
          上一页
        </button>
        <span class="pager__info">{{ query.page }} / {{ Math.ceil(total / query.size) }}</span>
        <button
          class="pager__btn"
          type="button"
          :disabled="query.page >= Math.ceil(total / query.size)"
          @click="query.page += 1; load()"
        >
          下一页
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.mine {
  padding-top: 16px;
}

.mine__list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.mitem {
  padding: 14px 16px;
  margin-bottom: 10px;
  background: #fff;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.mitem:hover {
  border-color: var(--c-primary-light);
  box-shadow: var(--shadow-card);
}

.mitem__head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 12px;
}

.mitem__book {
  font-size: 13px;
  font-weight: 600;
  color: var(--c-text);
}

.mitem__chapter,
.mitem__para {
  color: var(--c-text-muted);
}

.mitem__reply {
  padding: 1px 6px;
  border-radius: 3px;
  background: var(--c-primary-soft);
  color: var(--c-primary);
}

.mitem__hidden {
  padding: 1px 6px;
  border-radius: 3px;
  background: #f5f5f5;
  color: #999;
}

.mitem__quote {
  margin: 0 0 6px;
  padding: 6px 10px;
  border-left: 2px solid var(--c-border-strong);
  font-size: 12px;
  color: var(--c-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mitem__content {
  margin: 0 0 10px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--c-text);
  word-break: break-word;
}

.mitem__foot {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 12px;
  color: var(--c-text-muted);
}

.mitem__stat em {
  margin-right: 10px;
  font-style: normal;
}

.mitem__go {
  margin-left: auto;
  color: var(--c-primary);
}

.mine__pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  margin-top: 16px;
}

.pager__btn {
  padding: 5px 14px;
  border: 1px solid var(--c-border-strong);
  border-radius: var(--radius-sm);
  background: #fff;
  font-size: 13px;
  color: var(--c-text-secondary);
}

.pager__btn[disabled] {
  opacity: 0.45;
  cursor: not-allowed;
}

.pager__info {
  font-size: 13px;
  color: var(--c-text-muted);
}
</style>
