<script setup>
import { computed } from 'vue'

const props = defineProps({
  user: { type: Object, default: () => ({}) },
  size: { type: Number, default: 32 }
})

const initial = computed(() =>
  (props.user?.nickname || props.user?.username || '读').trim().slice(0, 1)
)

const boxStyle = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`,
  fontSize: `${Math.round(props.size * 0.42)}px`
}))
</script>

<template>
  <img
    v-if="user?.avatar"
    class="uavatar"
    :style="boxStyle"
    :src="user.avatar"
    :alt="user.nickname || user.username"
  />
  <span v-else class="uavatar uavatar--text" :style="boxStyle">{{ initial }}</span>
</template>

<style scoped>
.uavatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  overflow: hidden;
}

.uavatar--text {
  background: linear-gradient(135deg, #ff8fb3, #e8457a);
  color: #fff;
  font-weight: 600;
  line-height: 1;
}
</style>