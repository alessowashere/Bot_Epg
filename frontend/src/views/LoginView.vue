<template>
  <div class="min-h-screen bg-slate-950 flex items-center justify-center relative overflow-hidden">
    <!-- Fondo decorativo animado -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl animate-pulse-slow"></div>
      <div class="absolute -bottom-40 -left-40 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl animate-pulse-slow" style="animation-delay: 1.5s"></div>
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-900/5 rounded-full blur-3xl"></div>
    </div>

    <!-- Card de login -->
    <div class="relative z-10 w-full max-w-md mx-4 animate-fade-in">
      <!-- Header con logo UAC -->
      <div class="text-center mb-8">
        <div class="inline-flex flex-col items-center justify-center mb-4 gap-2">
          <!-- Logo UAC / ícono institucional -->
          <div class="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-2xl shadow-indigo-500/40 flex items-center justify-center">
            <svg class="w-11 h-11 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0118 18a8.966 8.966 0 00-6 2.292m0-14.25v14.25" />
            </svg>
          </div>
          <div>
            <h1 class="text-2xl font-bold text-white leading-tight">Escuela de Posgrado</h1>
            <p class="text-slate-400 text-sm mt-0.5">Universidad Andina del Cusco</p>
          </div>
        </div>
        <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20">
          <div class="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse"></div>
          <span class="text-xs text-indigo-300 font-medium">Sistema de Gestión de Tesis — TesisTrack</span>
        </div>
      </div>

      <!-- Formulario -->
      <div class="card-glass p-8">
        <h2 class="text-lg font-semibold text-white mb-1">Iniciar sesión</h2>
        <p class="text-slate-400 text-sm mb-6">Ingresa tus credenciales institucionales</p>

        <!-- Campo Correo -->
        <div class="mb-4">
          <label class="input-label">Correo electrónico</label>
          <input
            id="input-correo"
            v-model="form.correo"
            type="email"
            class="input-field"
            placeholder="tu.correo@uandina.edu.pe"
            autocomplete="email"
            @keyup.enter="ingresar"
          />
        </div>

        <!-- Campo Contraseña -->
        <div class="mb-6">
          <label class="input-label">Contraseña</label>
          <div class="relative">
            <input
              id="input-password"
              v-model="form.password"
              :type="mostrarPassword ? 'text' : 'password'"
              class="input-field pr-10"
              placeholder="••••••••"
              autocomplete="current-password"
              @keyup.enter="ingresar"
            />
            <button
              type="button"
              @click="mostrarPassword = !mostrarPassword"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <svg v-if="mostrarPassword" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          </div>
          <p class="text-xs text-slate-500 mt-1.5">Si no tienes contraseña asignada aún, deja el campo vacío.</p>
        </div>

        <!-- Error -->
        <div v-if="error" class="mb-4 flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          {{ error }}
        </div>

        <!-- Botón ingresar -->
        <button
          id="btn-ingresar"
          @click="ingresar"
          :disabled="!puedeIngresar || procesando"
          class="btn-primary w-full justify-center py-3"
        >
          <svg v-if="procesando" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
          </svg>
          {{ procesando ? 'Verificando...' : 'Ingresar al sistema' }}
        </button>
      </div>

      <p class="text-center text-slate-600 text-xs mt-6">
        EPG-UAC © {{ new Date().getFullYear() }} — Sistema interno de gestión de tesis
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import api from '../api.js'

const router = useRouter()
const auth = useAuthStore()

const form = ref({ correo: '', password: '' })
const mostrarPassword = ref(false)
const procesando = ref(false)
const error = ref('')

const puedeIngresar = computed(() => form.value.correo.trim().length > 0)

async function ingresar() {
  if (!puedeIngresar.value || procesando.value) return
  procesando.value = true
  error.value = ''

  try {
    const res = await api.post('/auth/login', null, {
      params: {
        correo: form.value.correo.trim(),
        password: form.value.password,
      }
    })
    auth.login(res.data)
    router.push('/')
  } catch (e) {
    const status = e.response?.status
    const detail = e.response?.data?.detail
    if (status === 401) {
      error.value = detail || 'Correo o contraseña incorrectos.'
    } else if (status === 422) {
      error.value = 'Por favor ingresa un correo válido.'
    } else {
      error.value = 'No se pudo conectar con el servidor. Verifica tu conexión.'
    }
  } finally {
    procesando.value = false
  }
}
</script>
