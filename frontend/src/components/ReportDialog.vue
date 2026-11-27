<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createReport, getReportReasons } from '@/api'
import { useUserStore } from '@/stores/user'
import { toast } from '@/utils/toast'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  targetType: { type: String, default: '' },
  targetId: { type: Number, default: 0 },
  preview: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue', 'submitted'])

const router = useRouter()
const user = useUserStore()

const reasons = ref(['广告引流', '辱骂攻击', '违法违规', '色情低俗', '侵权抄袭', '其他'])
const selected = ref('')
const detail = ref('')
const submitting = ref(false)

const typeLabel = computed(() =>
  props.targetType === 'book_comment' ? '书评' : '间贴'
)

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

watch(
  () => props.modelValue,
  async (open) => {
    if (!open) return
    selected.value = ''
    detail.value = ''
    try {
      const data = await getReportReasons()
      if (Array.isArray(data) && data.length) reasons.value = data
    } catch {
      /* 用内置默认值 */
    }
  }
)

function close() {
  visible.value = false
}

async function submit() {
  if (!user.isLogin) {
    router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
    return
  }
  if (!selected.value) {
    toast('请选择举报理由')
    return
  }
  submitting.value = true
  try {
    const res = await createReport({
      target_type: props.targetType,
      target_id: props.targetId,
      reason: selected.value,
      detail: detail.value.trim()
    })
    toast(
      res.pending_reports > 1
        ? `已举报，该内容当前有 ${res.pending_reports} 条待处理举报`
        : '已举报，管理员会尽快处理'
    )
    emit('submitted')
    close()
  } catch {
    /* 拦截器已提示 */
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="rp-mask" @click.self="close">
      <div class="rp">
        <header class="rp__head">
          <div>
            <p class="rp__title">举报{{ typeLabel }}</p>
            <p class="rp__desc">请选择理由，恶意举报会被记录</p>
          </div>
          <button class="rp__close" type="button" @click="close">✕</button>
        </header>

        <p v-if="preview" class="rp__quote">{{ preview }}</p>

        <div class="rp__body">
          <div class="rp__reasons">
            <label
              v-for="reason in reasons"
              :key="reason"
              class="rp__reason"
              :class="{ 'rp__reason--on': selected === reason }"
            >
              <input v-model="selected" type="radio" :value="reason" />
              {{ reason }}
            </label>
          </div>

          <textarea
            v-model="detail"
            class="rp__detail"
            rows="3"
            maxlength="300"
            placeholder="补充说明（选填）"
          ></textarea>
          <p class="rp__count">{{ detail.length }}/300</p>
        </div>

        <footer class="rp__foot">
          <button class="btn" type="button" @click="close">取消</button>
          <button
            class="btn btn--primary"
            type="button"
            :disabled="submitting || !selected"
            @click="submit"
          >
            {{ submitting ? '提交中…' : '提交举报' }}
          </button>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.rp-mask {
  position: fixed;
  inset: 0;
  z-index: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(0, 0, 0, 0.45);
}

.rp {
  width: 460px;
  max-width: 100%;
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.24);
  overflow: hidden;
}

.rp__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 20px 12px;
  border-bottom: 1px solid #f2f2f2;
}

.rp__title {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
}

.rp__desc {
  margin: 0;
  font-size: 12px;
  color: var(--c-text-muted);
}

.rp__close {
  border: none;
  background: transparent;
  font-size: 15px;
  color: #999;
}

.rp__quote {
  margin: 0;
  padding: 10px 20px;
  background: #fafafa;
  border-bottom: 1px solid #f2f2f2;
  font-size: 12px;
  color: var(--c-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rp__body {
  padding: 16px 20px 6px;
}

.rp__reasons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.rp__reason {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  border: 1px solid var(--c-border);
  border-radius: 15px;
  font-size: 13px;
  color: var(--c-text-secondary);
  cursor: pointer;
}

.rp__reason input {
  display: none;
}

.rp__reason--on {
  border-color: var(--c-primary);
  background: var(--c-primary-soft);
  color: var(--c-primary);
}

.rp__detail {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: 13px;
  line-height: 1.7;
  resize: none;
}

.rp__count {
  margin: 4px 0 0;
  text-align: right;
  font-size: 12px;
  color: var(--c-text-muted);
}

.rp__foot {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px 18px;
}
</style>
