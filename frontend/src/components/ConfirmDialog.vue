<script setup>
import { onBeforeUnmount, onMounted } from 'vue'
import { settleConfirm, useConfirmState } from '@/composables/useConfirm'

const state = useConfirmState()

function onKeydown(event) {
  if (!state.visible) return
  if (event.key === 'Escape') settleConfirm(false)
  else if (event.key === 'Enter') settleConfirm(true)
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <Transition name="confirm">
      <div v-if="state.visible" class="confirm" @click.self="settleConfirm(false)">
        <div class="confirm__box" role="dialog" aria-modal="true">
          <h3 class="confirm__title">{{ state.title }}</h3>
          <p v-if="state.message" class="confirm__message">{{ state.message }}</p>
          <div class="confirm__actions">
            <button class="btn" type="button" @click="settleConfirm(false)">
              {{ state.cancelText }}
            </button>
            <button
              class="btn"
              :class="state.danger ? 'btn--danger' : 'btn--primary'"
              type="button"
              autofocus
              @click="settleConfirm(true)"
            >
              {{ state.confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.confirm {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(32, 30, 26, 0.42);
  backdrop-filter: blur(2px);
}

.confirm__box {
  width: 100%;
  max-width: 360px;
  padding: 24px;
  background: var(--c-surface);
  border-radius: var(--radius-lg);
  box-shadow: 0 18px 48px rgba(30, 28, 24, 0.22);
}

.confirm__title {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: 600;
  color: var(--c-text);
}

.confirm__message {
  margin: 0 0 22px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--c-text-secondary);
  word-break: break-word;
}

.confirm__actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.confirm-enter-active,
.confirm-leave-active {
  transition: opacity 0.16s ease;
}

.confirm-enter-active .confirm__box,
.confirm-leave-active .confirm__box {
  transition: transform 0.16s ease;
}

.confirm-enter-from,
.confirm-leave-to {
  opacity: 0;
}

.confirm-enter-from .confirm__box,
.confirm-leave-to .confirm__box {
  transform: translateY(8px) scale(0.98);
}
</style>