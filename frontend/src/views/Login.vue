<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { toast } from '@/utils/toast'

const route = useRoute()
const router = useRouter()
const user = useUserStore()

const mode = ref('login')
const loading = ref(false)
const form = ref({ username: '', password: '', password_confirm: '', nickname: '' })

const isRegister = computed(() => mode.value === 'register')
const isDev = import.meta.env.DEV

function switchMode(next) {
  mode.value = next
}

async function submit() {
  if (!form.value.username.trim() || !form.value.password) {
    toast('请填写用户名和密码')
    return
  }
  if (isRegister.value && form.value.password !== form.value.password_confirm) {
    toast('两次输入的密码不一致')
    return
  }

  loading.value = true
  try {
    if (isRegister.value) {
      await user.doRegister({
        username: form.value.username.trim(),
        password: form.value.password,
        password_confirm: form.value.password_confirm,
        nickname: form.value.nickname.trim() || undefined
      })
      toast('注册成功')
    } else {
      await user.doLogin({
        username: form.value.username.trim(),
        password: form.value.password
      })
      toast('登录成功')
    }
    router.push((route.query.redirect || '/').toString())
  } catch {
    /* 拦截器已提示 */
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth">
    <div class="auth__card">
      <router-link to="/" class="auth__logo">轻量<span>小说</span></router-link>

      <div class="auth__tabs">
        <button
          class="auth__tab"
          :class="{ 'auth__tab--active': !isRegister }"
          type="button"
          @click="switchMode('login')"
        >
          登录
        </button>
        <button
          class="auth__tab"
          :class="{ 'auth__tab--active': isRegister }"
          type="button"
          @click="switchMode('register')"
        >
          注册
        </button>
      </div>

      <form class="auth__form" @submit.prevent="submit">
        <label class="auth__field">
          <span>用户名</span>
          <input v-model="form.username" type="text" autocomplete="username" placeholder="3~20 位字母、数字或下划线" />
        </label>

        <label class="auth__field">
          <span>密码</span>
          <input v-model="form.password" type="password" autocomplete="current-password" placeholder="6~32 位" />
        </label>

        <template v-if="isRegister">
          <label class="auth__field">
            <span>确认密码</span>
            <input v-model="form.password_confirm" type="password" autocomplete="new-password" />
          </label>
          <label class="auth__field">
            <span>昵称（可选）</span>
            <input v-model="form.nickname" type="text" maxlength="20" />
          </label>
        </template>

        <button class="btn btn--primary auth__submit" type="submit" :disabled="loading">
          {{ loading ? '请稍候…' : isRegister ? '注册并登录' : '登录' }}
        </button>
      </form>

      <p v-if="isDev" class="auth__hint">
        演示账号：reader1 / reader123　　管理员：admin / admin123
      </p>
    </div>
  </div>
</template>

<style scoped>
.auth {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
  background: linear-gradient(135deg, #eef2f7, var(--c-bg));
}

.auth__card {
  width: 100%;
  max-width: 380px;
  padding: 32px;
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-hover);
}

.auth__logo {
  display: block;
  margin-bottom: 24px;
  font-size: 22px;
  font-weight: 700;
  text-align: center;
  color: var(--c-primary);
  letter-spacing: 1px;
}

.auth__logo span {
  color: var(--c-accent);
}

.auth__tabs {
  display: flex;
  margin-bottom: 24px;
  border-bottom: 1px solid var(--c-border);
}

.auth__tab {
  flex: 1;
  padding: 10px 0;
  border: none;
  background: transparent;
  font-size: 15px;
  color: var(--c-text-muted);
  border-bottom: 2px solid transparent;
}

.auth__tab--active {
  color: var(--c-primary);
  border-bottom-color: var(--c-accent);
  font-weight: 600;
}

.auth__form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.auth__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.auth__field span {
  font-size: 13px;
  color: var(--c-text-secondary);
}

.auth__field input {
  height: 38px;
  padding: 0 12px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  background: var(--c-bg);
  font-size: 14px;
}

.auth__field input:focus {
  background: #fff;
  border-color: var(--c-primary-light);
}

.auth__submit {
  height: 40px;
  margin-top: 8px;
}

.auth__hint {
  margin: 20px 0 0;
  padding-top: 16px;
  border-top: 1px dashed var(--c-border);
  font-size: 12px;
  color: var(--c-text-muted);
  text-align: center;
}
</style>