import { watch } from 'vue'
import { defineStore } from 'pinia'
import { ref } from 'vue'

const KEY = 'novel_platform_reader_settings'

const DEFAULTS = {
  fontSize: 18,
  lineHeight: 2.0,
  theme: 'white'
}

const THEMES = {
  white: { bg: '#FFFFFF', text: '#2B2B2B', border: '#E8E3DA' },
  sepia: { bg: '#F5EFE3', text: '#3A3226', border: '#E0D6C2' },
  green: { bg: '#D8E6D5', text: '#23301F', border: '#C3D5BF' },
  dark: { bg: '#1A1A1A', text: '#C9C6C0', border: '#333333' }
}

function load() {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) || '{}') }
  } catch {
    return { ...DEFAULTS }
  }
}

export const useReaderStore = defineStore('reader', () => {
  const settings = ref(load())

  watch(
    settings,
    (value) => localStorage.setItem(KEY, JSON.stringify(value)),
    { deep: true }
  )

  function applyTheme() {
    const theme = THEMES[settings.value.theme] || THEMES.white
    const el = document.documentElement
    el.style.setProperty('--reader-bg', theme.bg)
    el.style.setProperty('--reader-text', theme.text)
    el.style.setProperty('--reader-border', theme.border)
    el.style.setProperty('--reader-font-size', `${settings.value.fontSize}px`)
    el.style.setProperty('--reader-line-height', String(settings.value.lineHeight))
  }

  function setFontSize(size) {
    settings.value.fontSize = Math.min(24, Math.max(14, size))
    applyTheme()
  }

  function setLineHeight(value) {
    settings.value.lineHeight = Number(value)
    applyTheme()
  }

  function setTheme(value) {
    settings.value.theme = value
    applyTheme()
  }

  return { settings, themes: THEMES, applyTheme, setFontSize, setLineHeight, setTheme }
})