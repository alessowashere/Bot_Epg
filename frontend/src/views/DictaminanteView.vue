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
  <div class="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
    <div class="max-w-2xl w-full bg-gray-800 rounded-xl shadow-2xl p-8 border border-gray-700">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-white mb-2">Sistema de Posgrado UAC</h1>
        <p class="text-gray-400">Asignación de Jurado / Dictaminante</p>
      </div>

      <div v-if="cargando" class="flex justify-center py-12">
        <i class="pi pi-spin pi-spinner text-4xl text-primary-500"></i>
      </div>

      <div v-else-if="error" class="text-center py-12">
        <i class="pi pi-exclamation-triangle text-6xl text-red-500 mb-4"></i>
        <h2 class="text-xl text-white">{{ error }}</h2>
      </div>

      <div v-else-if="asignacion">
        <div class="bg-gray-900 rounded-lg p-6 mb-8 border border-gray-700">
          <p class="text-gray-400 text-sm mb-1">Docente Asignado:</p>
          <p class="text-white font-semibold text-lg mb-4">{{ asignacion.docente }}</p>

          <p class="text-gray-400 text-sm mb-1">Rol Designado:</p>
          <p class="text-primary-400 font-semibold mb-4">{{ asignacion.rol }}</p>

          <p class="text-gray-400 text-sm mb-1">Tesista / Estudiante:</p>
          <p class="text-white mb-4">{{ asignacion.alumno }}</p>

          <p class="text-gray-400 text-sm mb-1">Título de la Tesis / Proyecto:</p>
          <p class="text-white">{{ asignacion.titulo_tesis || 'No especificado' }}</p>
        </div>

        <div v-if="asignacion.estado_actual !== 'Pendiente'" class="text-center bg-gray-900 p-6 rounded-lg border border-gray-700">
          <i class="pi pi-check-circle text-5xl mb-4" :class="asignacion.estado_actual === 'Aceptado' ? 'text-green-500' : 'text-red-500'"></i>
          <h3 class="text-2xl font-bold text-white mb-2">
            Cargo {{ asignacion.estado_actual }}
          </h3>
          <p class="text-gray-400">Ya has respondido a esta asignación anteriormente.</p>
        </div>

        <div v-else>
          <div class="mb-6">
            <label class="block text-gray-400 text-sm mb-2">Observaciones / Motivo (Obligatorio si declina):</label>
            <textarea 
              v-model="nota" 
              class="w-full bg-gray-900 border border-gray-700 rounded-lg text-white p-3 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none transition-colors"
              rows="3"
              placeholder="Ingrese alguna nota u observación (opcional si acepta)..."
            ></textarea>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button 
              @click="responder('Rechazado')" 
              :disabled="enviando"
              class="w-full py-3 px-4 bg-transparent border border-red-500 text-red-500 hover:bg-red-500 hover:text-white rounded-lg font-semibold transition-colors disabled:opacity-50"
            >
              <i class="pi pi-times mr-2"></i> Declino el cargo
            </button>
            <button 
              @click="responder('Aceptado')" 
              :disabled="enviando"
              class="w-full py-3 px-4 bg-primary-600 hover:bg-primary-500 text-white rounded-lg font-semibold transition-colors shadow-lg disabled:opacity-50"
            >
              <i class="pi pi-check mr-2"></i> Acepto el cargo
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
