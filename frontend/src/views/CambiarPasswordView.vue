<template>
  <main class="flex min-h-screen items-center justify-center bg-slate-50 px-5 py-10">
    <section class="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
      <div class="flex items-start gap-3">
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-amber-100 text-amber-800"><i class="pi pi-key"></i></span>
        <div>
          <p class="text-xs font-semibold uppercase text-sky-700">Acceso protegido</p>
          <h1 class="mt-1 text-xl font-bold text-slate-950">Actualiza tu contraseña</h1>
          <p class="mt-2 text-sm leading-6 text-slate-600">Antes de continuar, establece una contraseña personal para tu cuenta.</p>
        </div>
      </div>

      <form class="mt-7 space-y-4" autocomplete="on" @submit.prevent="guardar">
        <div>
          <label for="password-actual" class="input-label">Contraseña actual</label>
          <input id="password-actual" v-model="form.password_actual" class="input-field" type="password" autocomplete="current-password" required />
        </div>
        <div>
          <label for="password-nueva" class="input-label">Nueva contraseña</label>
          <input id="password-nueva" v-model="form.nueva_password" class="input-field" type="password" autocomplete="new-password" minlength="12" required />
          <p class="mt-1.5 text-xs text-slate-500">Mínimo 12 caracteres, con mayúscula, minúscula y número.</p>
        </div>
        <div>
          <label for="password-confirmacion" class="input-label">Confirmar nueva contraseña</label>
          <input id="password-confirmacion" v-model="confirmacion" class="input-field" type="password" autocomplete="new-password" minlength="12" required />
        </div>
        <p v-if="error" role="alert" class="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{{ error }}</p>
        <p v-if="mensaje" role="status" class="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{{ mensaje }}</p>
        <button type="submit" :disabled="guardando" class="btn-primary min-h-11 w-full justify-center">
          <i :class="guardando ? 'pi pi-spin pi-spinner' : 'pi pi-check'"></i>
          {{ guardando ? 'Actualizando...' : 'Guardar y continuar' }}
        </button>
      </form>
      <button type="button" class="mt-5 w-full text-center text-sm font-medium text-slate-600 hover:text-slate-950" @click="salir">Cerrar sesión</button>
    </section>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api.js'
import { useAuthStore } from '../stores/auth.js'

const router = useRouter()
const auth = useAuthStore()
const form = ref({ password_actual: '', nueva_password: '' })
const confirmacion = ref('')
const guardando = ref(false)
const error = ref('')
const mensaje = ref('')

async function guardar() {
  error.value = ''
  mensaje.value = ''
  if (form.value.nueva_password !== confirmacion.value) {
    error.value = 'La confirmación no coincide con la nueva contraseña.'
    return
  }
  guardando.value = true
  try {
    const respuesta = await api.put('/auth/cambiar-password', form.value)
    mensaje.value = respuesta.data?.mensaje || 'Contraseña actualizada. Inicia sesión nuevamente.'
    window.setTimeout(() => {
      auth.logout()
      router.replace('/a0')
    }, 900)
  } catch (e) {
    error.value = e.response?.data?.detail || 'No se pudo actualizar la contraseña.'
  } finally {
    guardando.value = false
  }
}

function salir() {
  auth.logout()
  router.replace('/login')
}
</script>
