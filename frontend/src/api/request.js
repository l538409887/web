import axios from 'axios'
import router from '@/router'
import { toast } from '@/utils/toast'

const service = axios.create({ baseURL: '/api/v1', timeout: 10000 })

service.interceptors.request.use((config) => {
  const token = localStorage.getItem('novel_platform_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

service.interceptors.response.use(
  (res) => {
    const { code, message, data } = res.data
    if (code === 0) return data
    toast(message)
    return Promise.reject(new Error(message))
  },
  (err) => {
    const payload = err.response?.data
    if (payload?.code === 1002) {
      localStorage.removeItem('novel_platform_token')
      const redirect = router.currentRoute.value.fullPath
      if (router.currentRoute.value.path !== '/login') {
        router.push({ path: '/login', query: { redirect } })
      }
    }
    toast(payload?.message || '网络异常，请稍后重试')
    return Promise.reject(err)
  }
)

export default service