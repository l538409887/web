<template>
  <div class="container nf">
    <p class="nf__code">404</p>
    <p class="nf__text">这个页面走丢了</p>
    <div class="nf__actions">
      <router-link class="btn btn--primary" to="/">回首页</router-link>
    </div>
  </div>
</template>

<style scoped>
.nf {
  padding: 120px 24px;
  text-align: center;
}

.nf__code {
  margin: 0;
  font-size: 64px;
  font-weight: 700;
  color: var(--c-primary-soft);
}

.nf__text {
  margin: 8px 0 24px;
  color: var(--c-text-muted);
}
</style>