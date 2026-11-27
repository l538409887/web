<script setup>
defineProps({
  text: { type: String, default: '这里什么都没有' },
  actionText: { type: String, default: '' },
  to: { type: String, default: '/' }
})
</script>

<template>
  <div class="empty">
    <div class="empty__icon">📖</div>
    <p class="empty__text">{{ text }}</p>
    <router-link v-if="actionText" class="btn btn--primary" :to="to">{{ actionText }}</router-link>
  </div>
</template>

<style scoped>
.empty {
  padding: 72px 0;
  text-align: center;
}

.empty__icon {
  font-size: 40px;
  opacity: 0.6;
}

.empty__text {
  margin: 12px 0 20px;
  color: var(--c-text-muted);
}
</style>