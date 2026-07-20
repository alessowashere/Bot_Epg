<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { useToast } from 'primevue/usetoast'

const route = useRoute()
const toast = useToast()

const asignacion = ref(null)
const cargando = ref(true)
const enviando = ref(false)
const nota = ref('')
const error = ref(null)

const uuid = route.params.uuid_asignacion

onMounted(async () => {
  try {
    const res = await axios.get(`/api/dictaminante/${uuid}`)
    asignacion.value = res.data
  } catch (err) {
    console.error(err)
    error.value = 'No se encontró la asignación o el enlace es inválido.'
  } finally {
    cargando.value = false
  }
})

const responder = async (respuesta) => {
  if (respuesta === 'Rechazado' && !nota.value) {
    toast.add({ severity: 'warn', summary: 'Atención', detail: 'Debe ingresar un motivo si declina el cargo.', life: 3000 })
    return
  }

  enviando.value = true
  try {
    await axios.post(`/api/dictaminante/${uuid}/responder?respuesta=${respuesta}&nota=${encodeURIComponent(nota.value)}`)
    asignacion.value.estado_actual = respuesta
    toast.add({ severity: 'success', summary: 'Éxito', detail: `Respuesta enviada: ${respuesta}`, life: 3000 })
  } catch (err) {
    console.error(err)
    toast.add({ severity: 'error', summary: 'Error', detail: 'Hubo un error al enviar su respuesta.', life: 3000 })
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-[#f4f7fb] px-4 py-8 sm:px-6">
    <div class="mx-auto w-full max-w-2xl">
      <header class="mb-5 flex items-center gap-3 rounded-md bg-[#102f63] px-5 py-4 text-white shadow-sm">
        <div class="flex h-10 w-10 items-center justify-center rounded-md bg-white/10">
          <img src="https://uandina.edu.pe/assets/logo-uandina-icono.svg" alt="Universidad Andina del Cusco" class="h-7 w-7 object-contain" />
        </div>
        <div>
          <p class="text-[10px] font-bold uppercase tracking-wide text-cyan-200">Universidad Andina del Cusco</p>
          <h1 class="text-base font-bold">Escuela de Posgrado</h1>
        </div>
      </header>

      <main class="card shadow-sm">
        <div class="mb-7 border-b border-slate-200 pb-5 dark:border-slate-800">
          <p class="eyebrow">Respuesta externa segura</p>
          <h2 class="text-2xl font-bold tracking-tight text-slate-950 dark:text-white">Asignacion de dictaminante</h2>
          <p class="mt-1 text-sm text-slate-500">Revisa los datos y registra tu respuesta institucional.</p>
        </div>

      <div v-if="cargando" class="flex justify-center py-12">
        <i class="pi pi-spin pi-spinner text-3xl text-sky-700"></i>
      </div>

      <div v-else-if="error" class="text-center py-12">
        <i class="pi pi-exclamation-triangle mb-4 text-4xl text-red-500"></i>
        <h2 class="text-lg font-semibold text-slate-900 dark:text-white">{{ error }}</h2>
      </div>

      <div v-else-if="asignacion">
        <div class="surface-muted mb-7 grid gap-4 p-5 sm:grid-cols-2">
          <div>
            <p class="field-caption">Docente asignado</p>
            <p class="mt-1 font-semibold text-slate-900 dark:text-white">{{ asignacion.docente }}</p>
          </div>
          <div>
            <p class="field-caption">Rol designado</p>
            <p class="mt-1 font-semibold text-sky-700 dark:text-cyan-300">{{ asignacion.rol }}</p>
          </div>
          <div>
            <p class="field-caption">Tesista / estudiante</p>
            <p class="mt-1 text-sm font-medium text-slate-900 dark:text-white">{{ asignacion.alumno }}</p>
          </div>
          <div class="sm:col-span-2">
            <p class="field-caption">Titulo de tesis / proyecto</p>
            <p class="mt-1 text-sm leading-5 text-slate-700 dark:text-slate-200">{{ asignacion.titulo_tesis || 'No especificado' }}</p>
          </div>
        </div>

        <div v-if="asignacion.estado_actual !== 'Pendiente'" class="surface-muted p-6 text-center">
          <i class="pi pi-check-circle mb-4 text-4xl" :class="asignacion.estado_actual === 'Aceptado' ? 'text-emerald-600' : 'text-red-500'"></i>
          <h3 class="text-xl font-bold text-slate-900 dark:text-white">
            Cargo {{ asignacion.estado_actual }}
          </h3>
          <p class="mt-1 text-sm text-slate-500">Ya has respondido a esta asignacion anteriormente.</p>
        </div>

        <div v-else>
          <div class="mb-6">
            <label for="nota-dictaminante" class="input-label">Observaciones / motivo</label>
            <textarea 
              id="nota-dictaminante"
              v-model="nota" 
              class="input-field resize-none"
              rows="3"
              placeholder="Obligatorio si declinas el cargo."
            ></textarea>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button 
              @click="responder('Rechazado')" 
              :disabled="enviando"
              class="btn-danger w-full justify-center"
            >
              <i class="pi pi-times mr-2"></i> Declino el cargo
            </button>
            <button 
              @click="responder('Aceptado')" 
              :disabled="enviando"
              class="btn-primary w-full justify-center"
            >
              <i class="pi pi-check mr-2"></i> Acepto el cargo
            </button>
          </div>
        </div>
      </div>
      </main>
    </div>
  </div>
</template>
