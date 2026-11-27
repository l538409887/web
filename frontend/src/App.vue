<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const route = useRoute()
const fullscreen = computed(() => Boolean(route.meta.fullscreen))
</script>

<template>
  <AppHeader v-if="!fullscreen" />
  <main :class="['app-main', { 'app-main--fullscreen': fullscreen }]">
    <router-view v-slot="{ Component }">
      <component :is="Component" />
    </router-view>
  </main>
  <AppFooter v-if="!fullscreen" />

  <ConfirmDialog />
</template>