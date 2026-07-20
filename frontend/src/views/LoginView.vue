<template>
  <div class="min-h-screen bg-[#e9eef5] p-3 sm:p-5 lg:p-7">
    <div class="mx-auto grid min-h-[calc(100vh-1.5rem)] max-w-[1500px] overflow-hidden rounded-lg border border-slate-300/80 bg-white shadow-[0_24px_70px_rgba(15,35,66,0.16)] sm:min-h-[calc(100vh-2.5rem)] xl:grid-cols-[minmax(440px,1.08fr)_minmax(520px,0.92fr)]">
      <section class="login-visual relative hidden min-h-full flex-col justify-between overflow-hidden p-10 text-white xl:flex xl:p-12">
        <div class="login-visual-overlay absolute inset-0"></div>
        <div class="relative flex items-center gap-4">
          <div class="flex h-14 w-14 items-center justify-center rounded-lg border border-white/25 bg-white/10">
            <img src="/brand/uac-logo-white.png" alt="Universidad Andina del Cusco" class="h-10 w-10 object-contain" />
          </div>
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.12em] text-white/75">Universidad Andina del Cusco</p>
            <p class="mt-1 text-xl font-semibold">Escuela de Posgrado</p>
          </div>
        </div>
        <div class="relative max-w-xl pb-6">
          <div class="mb-6 h-1 w-16 bg-[#e3ad31]"></div>
          <p class="text-xs font-semibold uppercase tracking-[0.14em] text-[#f5cf70]">Alameda Pachacútec</p>
          <h1 class="mt-4 text-4xl font-semibold leading-[1.12] xl:text-5xl">Escuela de Posgrado</h1>
          <p class="mt-5 max-w-lg text-base leading-7 text-white/80">Sistema institucional para el seguimiento de expedientes de tesis.</p>
        </div>
        <div class="relative flex items-end justify-between border-t border-white/20 pt-5 text-xs text-white/65"><span>EPG-UAC</span><span>{{ new Date().getFullYear() }}</span></div>
      </section>

      <main class="flex min-h-full items-center justify-center bg-[#f8fafc] px-5 py-10 sm:px-10 lg:px-16 xl:bg-white xl:px-20">
        <div class="w-full max-w-[420px]">
          <div class="mb-10 flex items-center gap-3 xl:hidden">
            <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-[#0b315f] shadow-sm"><img src="/brand/uac-logo-white.png" alt="UAC" class="h-8 w-8 object-contain" /></div>
            <div><p class="text-xs font-semibold uppercase tracking-[0.1em] text-[#49617d]">Universidad Andina del Cusco</p><p class="mt-1 text-base font-semibold text-[#102a4c]">Escuela de Posgrado</p></div>
          </div>
          <header class="mb-9">
            <p class="mb-4 inline-flex items-center border-l-[3px] border-[#d4a62a] pl-3 text-xs font-semibold uppercase tracking-[0.12em] text-[#49617d]">Acceso institucional</p>
            <h2 class="text-[2rem] font-semibold leading-tight text-[#102a4c]">Bienvenido</h2>
            <p class="mt-3 text-sm leading-6 text-slate-600">Ingresa con las credenciales asignadas a tu cuenta.</p>
          </header>

          <form action="/bot-posgrado/api/auth/login" method="post" autocomplete="on" class="space-y-6" @submit.prevent="ingresar">
            <div>
              <label for="input-usuario" class="login-label">Usuario</label>
              <input id="input-usuario" v-model="form.usuario" name="username" type="text" class="login-input" placeholder="usuario" autocomplete="username" autocapitalize="none" spellcheck="false" required />
            </div>
            <div>
              <label for="input-password" class="login-label">Contraseña</label>
              <div class="relative">
                <input id="input-password" v-model="form.password" name="password" :type="mostrarPassword ? 'text' : 'password'" class="login-input pr-12" placeholder="Contraseña" autocomplete="current-password" />
                <button type="button" class="absolute right-2 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-[#102a4c] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#0b315f]" :aria-label="mostrarPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'" :title="mostrarPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'" @click="mostrarPassword = !mostrarPassword"><i :class="mostrarPassword ? 'pi-eye-slash' : 'pi-eye'" class="pi"></i></button>
              </div>
            </div>
            <div v-if="error" role="alert" class="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-3 text-sm leading-5 text-red-800"><i class="pi pi-exclamation-circle mt-0.5"></i><span>{{ error }}</span></div>
            <button id="btn-ingresar" type="submit" :disabled="!puedeIngresar || procesando" class="login-primary"><i :class="procesando ? 'pi-spin pi-spinner' : 'pi-sign-in'" class="pi"></i>{{ procesando ? 'Verificando...' : 'Ingresar al sistema' }}</button>
          </form>

          <div v-if="googleDisponible" class="my-7 flex items-center gap-3 text-xs font-medium text-slate-400" aria-hidden="true"><span class="h-px flex-1 bg-slate-200"></span><span>o continúa con</span><span class="h-px flex-1 bg-slate-200"></span></div>
          <button v-if="googleDisponible" type="button" class="login-google" :disabled="procesandoGoogle" @click="ingresarConGoogle"><i :class="procesandoGoogle ? 'pi-spin pi-spinner' : 'pi-google'" class="pi"></i>{{ procesandoGoogle ? 'Redirigiendo...' : 'Continuar con cuenta UAndina' }}</button>
          <p class="mt-10 border-t border-slate-200 pt-5 text-xs leading-5 text-slate-500">Sistema de uso interno · Escuela de Posgrado UAC</p>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import api from '../api.js'

const router = useRouter()
const auth = useAuthStore()

const form = ref({ usuario: '', password: '' })
const mostrarPassword = ref(false)
const procesando = ref(false)
const procesandoGoogle = ref(false)
const googleDisponible = ref(false)
const error = ref('')

const puedeIngresar = computed(() => form.value.usuario.trim().length > 0)

async function ingresar() {
  if (!puedeIngresar.value || procesando.value) return
  procesando.value = true
  error.value = ''

  try {
    const credenciales = new URLSearchParams()
    credenciales.set('username', form.value.usuario.trim())
    credenciales.set('password', form.value.password)
    const res = await api.post('/auth/login', credenciales, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    auth.login(res.data)
    await sugerirGuardarContrasena()
    router.push(res.data.debe_cambiar_password ? '/cambiar-password' : '/')
  } catch (e) {
    const status = e.response?.status
    const detail = e.response?.data?.detail
    if (status === 401) {
      error.value = detail || 'Usuario o contraseña incorrectos.'
    } else if (status === 422 || status === 400) {
      error.value = detail || 'Revisa las credenciales ingresadas.'
    } else {
      error.value = 'No se pudo conectar con el servidor. Verifica tu conexion.'
    }
  } finally {
    procesando.value = false
  }
}

async function cargarGoogleDisponible() {
  try {
    const respuesta = await api.get('/auth/google/config')
    googleDisponible.value = Boolean(respuesta.data?.enabled)
  } catch {
    googleDisponible.value = false
  }
}

function ingresarConGoogle() {
  if (procesandoGoogle.value) return
  procesandoGoogle.value = true
  const dispositivo = localStorage.getItem('epg_dispositivo_id')
  if (!dispositivo) {
    error.value = 'No se pudo preparar este navegador para el inicio de sesión.'
    procesandoGoogle.value = false
    return
  }
  window.location.assign(`/bot-posgrado/api/auth/google/login?dispositivo=${encodeURIComponent(dispositivo)}`)
}

async function completarLoginGoogle() {
  const hash = new URLSearchParams(window.location.hash.slice(1))
  const token = hash.get('oauth_token')
  const errorGoogle = hash.get('oauth_error')
  if (!token && !errorGoogle) return

  window.history.replaceState(null, '', window.location.pathname + window.location.search)
  if (errorGoogle) {
    error.value = errorGoogle
    return
  }

  procesandoGoogle.value = true
  try {
    localStorage.setItem('epg_token', token)
    const perfil = await api.get('/auth/me')
    auth.login({ access_token: token, ...perfil.data, debe_cambiar_password: false })
    router.replace('/')
  } catch {
    localStorage.removeItem('epg_token')
    error.value = 'La sesión institucional no pudo completarse. Inténtalo otra vez.'
  } finally {
    procesandoGoogle.value = false
  }
}

onMounted(() => {
  completarLoginGoogle()
  cargarGoogleDisponible()
})

async function sugerirGuardarContrasena() {
  // Complementa el formulario semantico en Chrome cuando el login se resuelve por XHR.
  if (!form.value.password || !window.PasswordCredential || !navigator.credentials?.store) return
  try {
    const credencial = new window.PasswordCredential({
      id: form.value.usuario.trim(),
      password: form.value.password,
      name: form.value.usuario.trim(),
    })
    await navigator.credentials.store(credencial)
  } catch {
    // Algunos navegadores bloquean el guardado programatico; el login no debe fallar por ello.
  }
}
</script>

<style scoped>
.login-visual {
  background-image: url('/brand/posgrado-pachacutec-uac.webp');
  background-position: center;
  background-size: cover;
}

.login-visual-overlay { background: rgba(8, 35, 71, 0.86); }

.login-label {
  display: block;
  margin-bottom: 0.55rem;
  color: #243b5a;
  font-size: 0.8125rem;
  font-weight: 650;
}

.login-input {
  min-height: 3rem;
  width: 100%;
  border: 1px solid #bac7d7;
  border-radius: 0.375rem;
  background: #fff;
  color: #102a4c;
  font-size: 0.9375rem;
  outline: none;
  padding: 0.7rem 0.875rem;
  transition: border-color 150ms ease, box-shadow 150ms ease;
}

.login-input::placeholder { color: #8291a5; }
.login-input:focus { border-color: #0b5d8c; box-shadow: 0 0 0 3px rgba(11, 93, 140, 0.14); }

.login-primary, .login-google {
  display: inline-flex;
  min-height: 3rem;
  width: 100%;
  align-items: center;
  justify-content: center;
  gap: 0.625rem;
  border-radius: 0.375rem;
  font-size: 0.9375rem;
  font-weight: 650;
  transition: background-color 150ms ease, border-color 150ms ease, box-shadow 150ms ease;
}

.login-primary { border: 1px solid #0b315f; background: #0b315f; color: #fff; box-shadow: 0 5px 12px rgba(11, 49, 95, 0.18); }
.login-primary:hover:not(:disabled) { background: #08284d; }
.login-google { border: 1px solid #aebdce; background: #fff; color: #173654; }
.login-google:hover:not(:disabled) { border-color: #0b5d8c; background: #f3f8fc; }
.login-primary:focus-visible, .login-google:focus-visible { outline: 3px solid rgba(11, 93, 140, 0.28); outline-offset: 2px; }
.login-primary:disabled, .login-google:disabled { cursor: not-allowed; opacity: 0.56; }
</style>
