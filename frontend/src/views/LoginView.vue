<template>
  <div class="min-h-screen bg-slate-950 flex items-center justify-center relative overflow-hidden">
    <!-- Fondo decorativo -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl"></div>
      <div class="absolute -bottom-40 -left-40 w-96 h-96 bg-violet-600/10 rounded-full blur-3xl"></div>
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-900/5 rounded-full blur-3xl"></div>
    </div>

    <!-- Card de login -->
    <div class="relative z-10 w-full max-w-md mx-4 animate-fade-in">
      <!-- Header con logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-2xl shadow-indigo-500/40 mb-4">
          <svg class="w-9 h-9 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.966 8.966 0 00-6 2.292m0-14.25v14.25" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-white">Escuela de Posgrado</h1>
        <p class="text-slate-400 text-sm mt-1">Universidad Andina del Cusco — Sistema de Gestión</p>
      </div>

      <!-- Formulario -->
      <div class="card-glass p-8">
        <h2 class="text-lg font-semibold text-white mb-1">Iniciar sesión</h2>
        <p class="text-slate-400 text-sm mb-6">Selecciona tu usuario para continuar</p>

        <!-- Selector de usuario -->
        <div class="mb-5">
          <label class="input-label">Tu nombre</label>
          <div v-if="cargando" class="space-y-2">
            <div class="h-10 bg-slate-700/50 rounded-lg animate-pulse"></div>
          </div>
          <div v-else class="space-y-2 max-h-60 overflow-y-auto pr-1">
            <button
              v-for="u in usuarios"
              :key="u.id_usuario"
              @click="seleccionado = u"
              :class="[
                'w-full flex items-center gap-3 p-3 rounded-lg border transition-all duration-200 text-left',
                seleccionado?.id_usuario === u.id_usuario
                  ? 'border-indigo-500 bg-indigo-600/20 text-white'
                  : 'border-slate-700 bg-slate-800/40 text-slate-300 hover:border-slate-500 hover:bg-slate-700/40'
              ]"
            >
              <div :class="[
                'w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0',
                seleccionado?.id_usuario === u.id_usuario ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-400'
              ]">
                {{ iniciales(u.nombre_completo) }}
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium truncate">{{ u.nombre_completo }}</p>
                <p class="text-xs text-slate-500">{{ u.rol }}</p>
              </div>
              <svg v-if="seleccionado?.id_usuario === u.id_usuario" class="w-4 h-4 text-indigo-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </button>
          </div>
          <p v-if="!cargando && usuarios.length === 0" class="text-slate-500 text-sm text-center py-4">
            No hay usuarios configurados en el sistema.
          </p>
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
          @click="ingresar"
          :disabled="!seleccionado || procesando"
          class="btn-primary w-full justify-center py-3"
        >
          <svg v-if="procesando" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
          </svg>
          {{ procesando ? 'Ingresando...' : 'Ingresar al sistema' }}
        </button>
      </div>

      <p class="text-center text-slate-600 text-xs mt-6">
        EPG-UAC © {{ new Date().getFullYear() }} — Sistema interno de gestión de tesis
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import api from '../api.js'

const router = useRouter()
const auth = useAuthStore()

const usuarios = ref([])
const seleccionado = ref(null)
const cargando = ref(true)
const procesando = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    const res = await api.get('/usuarios')
    usuarios.value = res.data
  } catch (e) {
    error.value = 'No se pudo conectar con el servidor. Verifica la conexión.'
  } finally {
    cargando.value = false
  }
})

function iniciales(nombre) {
  return nombre.split(' ').slice(0, 2).map(n => n[0]).join('').toUpperCase()
}

async function ingresar() {
  if (!seleccionado.value) return
  procesando.value = true
  error.value = ''
  try {
    const res = await api.post(`/auth/login?id_usuario=${seleccionado.value.id_usuario}`)
    auth.login(res.data)
    router.push('/')
  } catch (e) {
    error.value = 'No se pudo verificar el usuario. Intenta nuevamente.'
  } finally {
    procesando.value = false
  }
}
</script>
