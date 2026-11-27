import { ref } from 'vue'
import { defineStore } from 'pinia'
import { getCategories } from '@/api'

export const useCatalogStore = defineStore('catalog', () => {
  const categories = ref([])
  let loaded = false

  async function ensureCategories() {
    if (loaded && categories.value.length) return categories.value
    try {
      categories.value = await getCategories()
      loaded = true
    } catch {
      /* 忽略，导航栏降级为空 */
    }
    return categories.value
  }

  return { categories, ensureCategories }
})