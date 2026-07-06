<template>
  <!-- Hilo de conversación estilo osTicket -->
  <div class="space-y-3">
    <div v-if="cargando" class="space-y-3">
      <div v-for="i in 3" :key="i" class="h-20 bg-slate-800/40 rounded-lg animate-pulse"></div>
    </div>

    <div v-else-if="!mensajes.length" class="text-center py-8 text-slate-500 text-sm">
      Sin mensajes en el hilo de conversación.
    </div>

    <div
      v-for="msg in mensajes"
      :key="msg.id || msg.fecha"
      :class="[
        'rounded-lg border p-4 transition-all',
        msg.tipo === 'respuesta_agente' || msg.tipo === 'nota_interna'
          ? 'bg-indigo-950/30 border-indigo-500/20'
          : 'bg-slate-800/40 border-slate-700/40'
      ]"
    >
      <!-- Cabecera del mensaje -->
      <div class="flex items-center justify-between gap-3 mb-2">
        <div class="flex items-center gap-2">
          <div :class="['w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0', avatarClass(msg.tipo)]">
            {{ iniciales(msg.autor || msg.tipo) }}
          </div>
          <div>
            <span class="text-xs font-semibold text-white">{{ msg.autor || etiquetaTipo(msg.tipo) }}</span>
            <span v-if="msg.tipo === 'nota_interna'" class="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-yellow-500/20 text-yellow-300 border border-yellow-500/20">Nota Interna</span>
          </div>
        </div>
        <span class="text-[10px] text-slate-500 flex-shrink-0">{{ msg.fecha }}</span>
      </div>

      <!-- Cuerpo del mensaje -->
      <div class="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap pl-9">{{ msg.cuerpo }}</div>
    </div>

    <!-- Formulario de respuesta -->
    <div v-if="mostrarFormulario" class="mt-4 pt-4 border-t border-slate-700/50">
      <h4 class="text-xs font-semibold text-slate-300 mb-3">Responder en osTicket</h4>
      <div class="space-y-3">
        <div class="flex gap-2">
          <button
            @click="tipoRespuesta = 'nota_interna'"
            :class="['btn-sm text-xs flex-1', tipoRespuesta === 'nota_interna' ? 'btn-primary' : 'btn-ghost']"
          >
            Nota Interna
          </button>
          <button
            @click="tipoRespuesta = 'respuesta_cliente'"
            :class="['btn-sm text-xs flex-1', tipoRespuesta === 'respuesta_cliente' ? 'btn-warning' : 'btn-ghost']"
          >
            Respuesta al Alumno
          </button>
        </div>
        <textarea
          v-model="mensajeRespuesta"
          class="input-field resize-none text-sm"
          rows="4"
          :placeholder="tipoRespuesta === 'nota_interna' ? 'Escribe una nota interna (solo visible para el equipo)...' : 'Escribe la respuesta para el alumno...'"
        ></textarea>
        <div class="flex gap-2 justify-end">
          <button @click="cancelarRespuesta" class="btn-ghost btn-sm">Cancelar</button>
          <button
            @click="enviarRespuesta"
            :disabled="!mensajeRespuesta.trim() || enviando"
            :class="tipoRespuesta === 'nota_interna' ? 'btn-primary btn-sm' : 'btn-warning btn-sm'"
          >
            <svg v-if="enviando" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
            {{ enviando ? 'Enviando...' : (tipoRespuesta === 'nota_interna' ? 'Agregar Nota' : 'Enviar Respuesta') }}
          </button>
        </div>
        <p v-if="errorEnvio" class="text-xs text-red-400">{{ errorEnvio }}</p>
        <p v-if="exitoEnvio" class="text-xs text-emerald-400">{{ exitoEnvio }}</p>
      </div>
    </div>

    <!-- Botón para abrir formulario -->
    <div v-else class="pt-2">
      <button @click="mostrarFormulario = true" class="btn-outline btn-sm w-full justify-center">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Agregar respuesta / nota
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '../api.js'
import { useAuthStore } from '../stores/auth.js'

const props = defineProps({
  ticketRef: { type: String, required: true },
  cuerpoTicket: { type: String, default: '' },
})

const emit = defineEmits(['respuesta-enviada'])
const auth = useAuthStore()

const mensajes = ref([])
const cargando = ref(false)
const mostrarFormulario = ref(false)
const tipoRespuesta = ref('nota_interna')
const mensajeRespuesta = ref('')
const enviando = ref(false)
const errorEnvio = ref('')
const exitoEnvio = ref('')

// Construir hilo desde el cuerpo del ticket como primer mensaje
function construirHilo(cuerpo) {
  const hilo = []
  if (cuerpo) {
    hilo.push({
      tipo: 'alumno',
      autor: 'Alumno (osTicket)',
      cuerpo: cuerpo,
      fecha: '',
    })
  }
  return hilo
}

function iniciales(texto) {
  if (!texto) return '?'
  return texto.trim().split(' ').slice(0, 2).map(w => w[0]?.toUpperCase() || '').join('')
}

function etiquetaTipo(tipo) {
  const map = {
    alumno: 'Alumno',
    respuesta_agente: 'Agente EPG',
    nota_interna: 'Nota Interna',
  }
  return map[tipo] || tipo
}

function avatarClass(tipo) {
  const map = {
    alumno: 'bg-emerald-600',
    respuesta_agente: 'bg-indigo-600',
    nota_interna: 'bg-yellow-600',
  }
  return map[tipo] || 'bg-slate-600'
}

function cancelarRespuesta() {
  mostrarFormulario.value = false
  mensajeRespuesta.value = ''
  errorEnvio.value = ''
  exitoEnvio.value = ''
}

async function enviarRespuesta() {
  if (!mensajeRespuesta.value.trim()) return
  enviando.value = true
  errorEnvio.value = ''
  exitoEnvio.value = ''

  try {
    await api.post(`/tickets/${props.ticketRef}/responder-osticket`, null, {
      params: {
        mensaje: mensajeRespuesta.value,
        tipo: tipoRespuesta.value,
        usuario_nombre: auth.nombre,
      }
    })

    // Agregar el mensaje al hilo localmente
    mensajes.value.push({
      tipo: tipoRespuesta.value,
      autor: auth.nombre,
      cuerpo: mensajeRespuesta.value,
      fecha: new Date().toLocaleString('es-PE'),
    })

    exitoEnvio.value = tipoRespuesta.value === 'nota_interna'
      ? '✓ Nota interna agregada y enviada a osTicket.'
      : '✓ Respuesta enviada al alumno en osTicket.'

    mensajeRespuesta.value = ''
    mostrarFormulario.value = false
    emit('respuesta-enviada')
  } catch (e) {
    errorEnvio.value = e.response?.data?.detail || 'Error al enviar. Verifica la conexión con el servidor.'
  } finally {
    enviando.value = false
  }
}

onMounted(() => {
  mensajes.value = construirHilo(props.cuerpoTicket)
})

watch(() => props.cuerpoTicket, (nuevoValor) => {
  if (nuevoValor && mensajes.value.length === 0) {
    mensajes.value = construirHilo(nuevoValor)
  }
})
</script>
