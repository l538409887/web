<script setup>
defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  art: { type: String, default: '' }
})
</script>

<template>
  <div class="strip">
    <div class="strip__bg" :style="art ? { backgroundImage: `url(${art})` } : {}"></div>
    <div class="strip__veil"></div>
    <div class="strip__text">
      <p class="strip__title">{{ title }}</p>
      <p class="strip__sub">{{ subtitle }}</p>
    </div>
  </div>
</template>

<style scoped>
.strip {
  position: relative;
  height: 150px;
  margin-top: 26px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: linear-gradient(120deg, var(--c-primary), #d93e73);
}

/* 原图分辨率有限，用模糊做成景深，避免硬拉伸的糊 */
.strip__bg {
  position: absolute;
  inset: -26px;
  background-size: cover;
  background-position: center;
  filter: blur(11px) saturate(1.25) brightness(0.95);
  transform: scale(1.08);
}

.strip__veil {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    rgba(242, 79, 134, 0.9) 0%,
    rgba(217, 62, 115, 0.62) 42%,
    rgba(217, 62, 115, 0.12) 78%,
    rgba(255, 255, 255, 0) 100%
  );
}

.strip__text {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
  padding: 0 46px;
  color: #fff;
}

.strip__title {
  margin: 0 0 6px;
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 6px;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.28);
}

.strip__sub {
  margin: 0;
  font-size: 13px;
  letter-spacing: 2px;
  opacity: 0.9;
}

@media (max-width: 768px) {
  .strip {
    height: 104px;
  }
  .strip__text {
    padding: 0 22px;
  }
  .strip__title {
    font-size: 20px;
    letter-spacing: 3px;
  }
}
</style>
