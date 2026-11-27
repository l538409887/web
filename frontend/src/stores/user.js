import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import * as api from '@/api'

const TOKEN_KEY = 'novel_platform_token'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const profile = ref(null)
  const initialized = ref(false)

  const isLogin = computed(() => Boolean(token.value))
  const role = computed(() => profile.value?.role || 'guest')

  function setToken(value) {
    token.value = value || ''
    if (value) localStorage.setItem(TOKEN_KEY, value)
    else localStorage.removeItem(TOKEN_KEY)
  }

  async function fetchMe() {
    if (!token.value) {
      initialized.value = true
      return null
    }
    try {
      profile.value = await api.getMe()
    } catch {
      setToken('')
      profile.value = null
    } finally {
      initialized.value = true
    }
    return profile.value
  }

  async function doLogin(payload) {
    const data = await api.login(payload)
    setToken(data.access_token)
    profile.value = data.user
    initialized.value = true
    return data.user
  }

  async function doRegister(payload) {
    const data = await api.register(payload)
    setToken(data.access_token)
    profile.value = data.user
    initialized.value = true
    return data.user
  }

  async function doLogout() {
    try {
      if (token.value) await api.logout()
    } catch {
      /* 忽略退出接口异常 */
    }
    setToken('')
    profile.value = null
  }

  return { token, profile, initialized, isLogin, role, setToken, fetchMe, doLogin, doRegister, doLogout }
})