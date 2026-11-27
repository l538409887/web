import { reactive } from 'vue'

const state = reactive({
  visible: false,
  title: '',
  message: '',
  confirmText: '确定',
  cancelText: '取消',
  danger: true,
  resolve: null
})

/**
 * 打开确认弹窗，返回 Promise<boolean>。
 * 用法：const ok = await confirmDialog({ title: '删除？' }); if (!ok) return
 */
export function confirmDialog(options = {}) {
  return new Promise((resolve) => {
    state.visible = true
    state.title = options.title || '确认操作'
    state.message = options.message || ''
    state.confirmText = options.confirmText || '确定'
    state.cancelText = options.cancelText || '取消'
    state.danger = options.danger !== false
    state.resolve = resolve
  })
}

export function useConfirmState() {
  return state
}

export function settleConfirm(result) {
  if (!state.visible) return
  state.visible = false
  const resolve = state.resolve
  state.resolve = null
  if (resolve) resolve(result)
}