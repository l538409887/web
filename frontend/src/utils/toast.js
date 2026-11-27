let timer = null

export function toast(message, duration = 2400) {
  if (!message) return
  let el = document.getElementById('bj-toast')
  if (!el) {
    el = document.createElement('div')
    el.id = 'bj-toast'
    el.className = 'bj-toast'
    document.body.appendChild(el)
  }
  el.textContent = message
  el.classList.add('bj-toast--show')
  clearTimeout(timer)
  timer = setTimeout(() => el.classList.remove('bj-toast--show'), duration)
}