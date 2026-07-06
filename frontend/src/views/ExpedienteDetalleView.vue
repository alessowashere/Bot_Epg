<template>
  <div class="p-6 space-y-5 animate-fade-in">
    <div class="flex items-center gap-3">
      <button @click="$router.back()" class="btn-ghost btn-sm">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" /></svg>
        Volver
      </button>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 flex-wrap">
          <h2 class="text-xl font-bold text-white">Expediente #{{ exp?.id_expediente }}</h2>
          <span v-if="exp" :class="badgeEstado(exp.estado_expediente)">{{ exp.estado_expediente }}</span>
          <span v-if="exp?.sub_estado" class="badge-observado">{{ exp.sub_estado }}</span>
          <span v-if="exp" :class="exp.grado_postula === 'Doctor' ? 'badge bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'badge bg-blue-500/20 text-blue-300 border border-blue-500/30'">{{ exp.grado_postula }}</span>
        </div>
        <p class="text-slate-400 text-sm mt-0.5">{{ exp?.nombre_alumno }} - {{ exp?.codigo_alumno }}</p>
      </div>
    </div>

    <div v-if="cargando" class="space-y-4">
      <div class="h-32 bg-slate-800/60 rounded-xl animate-pulse"></div>
      <div class="h-48 bg-slate-800/60 rounded-xl animate-pulse"></div>
    </div>

    <div v-else-if="exp" class="space-y-5">
      <div class="card">
        <h3 class="text-sm font-semibold text-white mb-4">Progreso del Flujo</h3>
        <StepTimeline :paso-actual="exp.id_paso_actual" />
        <div class="mt-4 flex items-center gap-3 p-3 rounded-lg bg-indigo-600/10 border border-indigo-500/20">
          <div class="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-sm font-bold text-white flex-shrink-0">{{ exp.id_paso_actual }}</div>
          <div>
            <p class="text-sm font-semibold text-white">{{ exp.nombre_paso_actual }}</p>
            <p class="text-xs text-slate-400">Inicio: {{ exp.fecha_inicio }}</p>
          </div>
        </div>
      </div>

      <div v-if="exp.estado_expediente !== 'Archivado_Graduado'" class="grid grid-cols-1 xl:grid-cols-3 gap-5">
        <div class="xl:col-span-2 card">
          <h3 class="text-sm font-semibold text-white mb-4">Acciones del Expediente</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="p-4 rounded-lg bg-emerald-950/30 border border-emerald-500/20">
              <p class="text-sm font-semibold text-emerald-300">{{ exp.id_paso_actual < 7 ? `Aprobar a Paso ${exp.id_paso_actual + 1}` : 'Completar' }}</p>
              <textarea v-model="notaAprobacion" class="input-field resize-none text-xs mt-3" rows="2" placeholder="Nota opcional"></textarea>
              <button @click="aprobar" :disabled="procesando" class="btn-success w-full justify-center mt-3">Aprobar y Avanzar</button>
            </div>

            <div class="p-4 rounded-lg bg-red-950/30 border border-red-500/20">
              <p class="text-sm font-semibold text-red-300">Observar</p>
              <textarea v-model="notaObservacion" class="input-field resize-none text-xs mt-3" rows="2" placeholder="Observaci&oacute;n requerida"></textarea>
              <button @click="observar" :disabled="procesando || !notaObservacion.trim()" class="btn-danger w-full justify-center mt-3">Marcar Observado</button>
            </div>

            <div class="p-4 rounded-lg bg-indigo-950/30 border border-indigo-500/20">
              <p class="text-sm font-semibold text-indigo-300">Derivar a Directora</p>
              <textarea v-model="notaDerivacion" class="input-field resize-none text-xs mt-3" rows="2" placeholder="Nota opcional"></textarea>
              <button @click="derivarDirectora" :disabled="procesando" class="btn-primary w-full justify-center mt-3">Derivar</button>
            </div>

            <div class="p-4 rounded-lg bg-slate-900/70 border border-slate-700/70">
              <p class="text-sm font-semibold text-white">Cargar Resoluci&oacute;n Directa</p>
              <input type="file" accept="application/pdf" @change="archivoResolucion = $event.target.files?.[0] || null" class="input-field mt-3 text-xs" />
              <input v-model="tipoResolucion" class="input-field mt-2 text-xs" placeholder="Tipo de resoluci&oacute;n" />
              <button @click="cargarResolucion" :disabled="procesando || !archivoResolucion" class="btn-outline w-full justify-center mt-3">Cargar</button>
            </div>

            <div class="p-4 rounded-lg bg-slate-900/70 border border-slate-700/70 md:col-span-2">
              <p class="text-sm font-semibold text-white">Notificar</p>
              <textarea v-model="mensajeNotificacion" class="input-field resize-none text-xs mt-3" rows="2" placeholder="Mensaje para el ticket o historial"></textarea>
              <select v-model="ticketNotificar" class="input-field mt-2 text-xs">
                <option value="">Solo registrar notificaci&oacute;n</option>
                <option v-for="t in exp.tickets" :key="t.ticket_id" :value="t.ticket_id">Ticket #{{ t.numero_visual }}</option>
              </select>
              <button @click="notificar" :disabled="procesando || !mensajeNotificacion.trim()" class="btn-warning w-full justify-center mt-3">Notificar</button>
            </div>
          </div>
        </div>

        <div class="space-y-5">
          <div class="card">
            <h3 class="text-sm font-semibold text-white mb-3">Cambio de T&iacute;tulo</h3>
            <textarea v-model="nuevoTitulo" class="input-field resize-none text-xs" rows="3" placeholder="Nuevo t&iacute;tulo de tesis"></textarea>
            <input v-model="notaTitulo" class="input-field mt-2 text-xs" placeholder="Nota de historial" />
            <button @click="cambiarTitulo" :disabled="procesando || !nuevoTitulo.trim()" class="btn-outline w-full justify-center mt-3">Actualizar T&iacute;tulo</button>
          </div>

          <div class="card">
            <h3 class="text-sm font-semibold text-white mb-3">Asignar Dictaminantes</h3>
            <div class="space-y-2">
              <select v-for="(_, idx) in dictaminantesSeleccionados" :key="idx" v-model="dictaminantesSeleccionados[idx]" class="input-field text-xs">
                <option value="">Docente {{ idx + 1 }}</option>
                <option v-for="d in docentesDisponibles" :key="d.id_docente" :value="d.id_docente">
                  {{ d.nombre_completo }} ({{ d.carga_actual }}/{{ d.max_tesis_permitidas }})
                </option>
              </select>
            </div>
            <button @click="asignarDictaminantes" :disabled="procesando || !puedeAsignarDictaminantes" class="btn-primary w-full justify-center mt-3">Asignar 3 Dictaminantes</button>
          </div>
        </div>
      </div>

      <div v-else class="card border-emerald-500/30 bg-emerald-950/20 text-center py-6">
        <h3 class="text-lg font-bold text-emerald-300">Alumno Graduado</h3>
        <p class="text-slate-400 text-sm mt-1">Todos los pasos del flujo han sido completados.</p>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div class="card">
          <h3 class="text-sm font-semibold text-white mb-4">Historial de Movimientos</h3>
          <div class="space-y-3">
            <div v-for="mov in exp.historial" :key="mov.id_movimiento" class="bg-slate-800/40 rounded-lg p-3">
              <div class="flex items-center justify-between mb-1 gap-3">
                <span :class="['text-xs font-semibold', accionTextColor(mov.accion)]">{{ mov.accion }}</span>
                <span class="text-[10px] text-slate-500">{{ mov.fecha }}</span>
              </div>
              <p v-if="mov.nombre_paso" class="text-xs text-slate-300 mb-1">{{ mov.nombre_paso }}</p>
              <p v-if="mov.nota" class="text-xs text-slate-400 italic">{{ mov.nota }}</p>
              <p class="text-[10px] text-slate-600 mt-1">Por: {{ mov.usuario_nombre || 'Sistema' }}</p>
            </div>
            <p v-if="exp.historial.length === 0" class="text-xs text-slate-500">Sin movimientos registrados</p>
          </div>
        </div>

        <div class="space-y-5">
          <!-- Timeline de Revisiones / Versiones de Observaciones -->
          <div class="card">
            <h3 class="text-sm font-semibold text-white mb-4">Revisiones / Versiones de Documento</h3>
            <TimelineRevisiones
              v-if="exp"
              :expediente-ref="route.params.uuid"
              @actualizado="cargar"
            />
          </div>

          <div class="card">
            <h3 class="text-sm font-semibold text-white mb-3">Dictaminantes y Asignaciones</h3>
            <div class="space-y-2">
              <div v-for="asig in exp.asignaciones" :key="asig.id_asignacion" class="flex items-center gap-3 p-2.5 rounded-lg bg-slate-800/40">
                <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-300 flex-shrink-0">{{ inicialDocente(asig.nombre_docente) }}</div>
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-semibold text-white truncate">{{ asig.nombre_docente }}</p>
                  <p class="text-[10px] text-slate-500">{{ asig.especialidad || asig.correo_docente }}</p>
                </div>
                <div class="text-right flex-shrink-0">
                  <span class="text-[10px] font-medium text-violet-400 block">{{ asig.rol_asignado }}</span>
                  <span v-if="asig.aceptacion" :class="badgeAceptacion(asig.aceptacion.estado_aceptacion)">{{ asig.aceptacion.estado_aceptacion }}</span>
                </div>
              </div>
              <p v-if="exp.asignaciones.length === 0" class="text-xs text-slate-500 text-center py-2">Sin docentes asignados</p>
            </div>
          </div>

          <div class="card">
            <h3 class="text-sm font-semibold text-white mb-3">Tickets Vinculados ({{ exp.tickets.length }})</h3>
            <div class="space-y-2">
              <div v-for="t in exp.tickets" :key="t.ticket_id" class="flex items-center gap-3 p-2.5 rounded-lg bg-slate-800/40 hover:bg-slate-700/40 cursor-pointer transition-colors" @click="$router.push(`/bandeja/${t.uuid || t.ticket_id}`)">
                <span class="font-mono text-xs text-indigo-400 font-bold flex-shrink-0">#{{ t.numero_visual }}</span>
                <span class="text-xs text-slate-300 truncate flex-1">{{ t.asunto }}</span>
                <span class="text-[10px] text-slate-500 flex-shrink-0">{{ t.adjuntos_count }} adj.</span>
              </div>
              <p v-if="exp.tickets.length === 0" class="text-xs text-slate-500 text-center py-2">Sin tickets vinculados</p>
            </div>
          </div>

          <div class="card">
            <h3 class="text-sm font-semibold text-white mb-3">Resoluciones</h3>
            <div class="space-y-2">
              <div v-for="res in exp.resoluciones" :key="res.id_resolucion" class="flex items-center gap-3 p-2.5 rounded-lg bg-slate-800/40">
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-semibold text-white truncate">{{ res.tipo_documento }}</p>
                  <a v-if="res.archivo_drive_url" :href="res.archivo_drive_url" target="_blank" class="text-[10px] text-indigo-400 truncate block">Abrir archivo</a>
                </div>
                <span :class="res.estado_firma === 'Firmado' ? 'badge-graduado' : 'badge-observado'">{{ res.estado_firma }}</span>
              </div>
              <p v-if="exp.resoluciones.length === 0" class="text-xs text-slate-500 text-center py-2">Sin resoluciones registradas</p>
            </div>
          </div>

          <div class="card" v-if="exp.titulo_tesis">
            <h3 class="text-sm font-semibold text-white mb-2">T&iacute;tulo de Tesis</h3>
            <p class="text-sm text-slate-300 leading-relaxed italic">"{{ exp.titulo_tesis }}"</p>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="card text-center py-12">
      <p class="text-slate-400">Expediente no encontrado.</p>
      <button @click="$router.back()" class="btn-ghost mt-4">Volver</button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import api from '../api.js'
import StepTimeline from '../components/StepTimeline.vue'
import TimelineRevisiones from '../components/TimelineRevisiones.vue'

const route = useRoute()
const auth = useAuthStore()

const exp = ref(null)
const docentes = ref([])
const cargando = ref(true)
const procesando = ref(null)
const notaAprobacion = ref('')
const notaObservacion = ref('')
const notaDerivacion = ref('')
const archivoResolucion = ref(null)
const tipoResolucion = ref('Resolucion directa')
const mensajeNotificacion = ref('')
const ticketNotificar = ref('')
const nuevoTitulo = ref('')
const notaTitulo = ref('')
const dictaminantesSeleccionados = ref(['', '', ''])

const docentesDisponibles = computed(() => docentes.value.filter(d => d.disponible))
const puedeAsignarDictaminantes = computed(() => {
  const ids = dictaminantesSeleccionados.value.filter(Boolean)
  return ids.length === 3 && new Set(ids).size === 3
})

function badgeEstado(estado) {
  const map = {
    'En Proceso': 'badge-proceso',
    Observado: 'badge-observado',
    Archivado_Graduado: 'badge-graduado',
    Caduco: 'badge-caduco',
  }
  return map[estado] || 'badge'
}

function badgeAceptacion(estado) {
  const map = {
    Pendiente: 'badge-observado text-[10px]',
    Aceptado: 'badge-graduado text-[10px]',
    Rechazado: 'badge-error text-[10px]',
  }
  return map[estado] || 'badge text-[10px]'
}

function accionTextColor(accion) {
  const map = {
    Creado: 'text-blue-400',
    Clasificado: 'text-indigo-400',
    Avanzado: 'text-emerald-400',
    Observado: 'text-amber-400',
    Archivado: 'text-emerald-300',
    Derivado: 'text-indigo-300',
    Notificado: 'text-sky-300',
    Titulo_Actualizado: 'text-violet-300',
    Resolucion_Cargada: 'text-emerald-300',
    Dictaminantes_Asignados: 'text-violet-300',
  }
  return map[accion] || 'text-slate-400'
}

function inicialDocente(nombre) {
  if (!nombre) return '?'
  return nombre.split(' ').slice(0, 2).map(n => n[0]).join('').toUpperCase()
}

async function cargar() {
  cargando.value = true
  try {
    const res = await api.get(`/expedientes/${route.params.uuid}`)
    exp.value = res.data
    nuevoTitulo.value = exp.value.titulo_tesis || ''
  } catch (e) {
    console.error(e)
  } finally {
    cargando.value = false
  }
}

async function cargarDocentes() {
  const res = await api.get('/docentes')
  docentes.value = res.data.data
}

async function ejecutar(nombre, fn) {
  procesando.value = nombre
  try {
    await fn()
    await cargar()
  } catch (e) {
    console.error(e)
  } finally {
    procesando.value = null
  }
}

function aprobar() {
  ejecutar('aprobar', () => api.post(`/expedientes/${route.params.uuid}/avanzar`, null, {
    params: { nota: notaAprobacion.value || undefined, usuario_nombre: auth.nombre }
  }).then(() => { notaAprobacion.value = '' }))
}

function observar() {
  if (!notaObservacion.value.trim()) return
  ejecutar('observar', () => api.post(`/expedientes/${route.params.uuid}/observar`, null, {
    params: { nota: notaObservacion.value, usuario_nombre: auth.nombre }
  }).then(() => { notaObservacion.value = '' }))
}

function derivarDirectora() {
  ejecutar('derivar', () => api.post(`/expedientes/${route.params.uuid}/derivar-directora`, null, {
    params: { nota: notaDerivacion.value || undefined, usuario_nombre: auth.nombre }
  }).then(() => { notaDerivacion.value = '' }))
}

function cargarResolucion() {
  if (!archivoResolucion.value) return
  const formData = new FormData()
  formData.append('archivo', archivoResolucion.value)
  ejecutar('resolucion', () => api.post(`/expedientes/${route.params.uuid}/cargar-resolucion-directa`, formData, {
    params: { tipo_documento: tipoResolucion.value, usuario_nombre: auth.nombre },
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(() => { archivoResolucion.value = null }))
}

function notificar() {
  ejecutar('notificar', () => api.post(`/expedientes/${route.params.uuid}/notificar`, null, {
    params: {
      mensaje: mensajeNotificacion.value,
      ticket_id: ticketNotificar.value || undefined,
      usuario_nombre: auth.nombre
    }
  }).then(() => {
    mensajeNotificacion.value = ''
    ticketNotificar.value = ''
  }))
}

function cambiarTitulo() {
  ejecutar('titulo', () => api.post(`/expedientes/${route.params.uuid}/cambiar-titulo`, null, {
    params: { nuevo_titulo: nuevoTitulo.value, nota: notaTitulo.value || undefined, usuario_nombre: auth.nombre }
  }).then(() => { notaTitulo.value = '' }))
}

function asignarDictaminantes() {
  const docente_ids = dictaminantesSeleccionados.value.join(',')
  ejecutar('dictaminantes', () => api.post(`/expedientes/${route.params.uuid}/asignar-dictaminantes`, null, {
    params: { docente_ids, usuario_nombre: auth.nombre }
  }).then(() => { dictaminantesSeleccionados.value = ['', '', ''] }))
}

onMounted(async () => {
  await Promise.all([cargar(), cargarDocentes()])
})
</script>
