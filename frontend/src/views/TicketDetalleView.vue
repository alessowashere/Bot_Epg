<template>
  <div class="p-6 space-y-5 animate-fade-in">
    <div class="flex items-center gap-3">
      <button @click="$router.back()" class="btn-ghost btn-sm">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
        </svg>
        Volver
      </button>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2">
          <h2 class="text-xl font-bold text-white">Ticket <span class="text-indigo-400 font-mono">#{{ ticket?.numero_visual }}</span></h2>
          <span v-if="ticket" :class="badgeEstado(ticket.estado)">{{ ticket.estado }}</span>
        </div>
        <p class="text-slate-400 text-sm mt-0.5 truncate">{{ ticket?.asunto }}</p>
      </div>
    </div>

    <div v-if="cargando" class="space-y-4">
      <div class="h-32 bg-slate-800/60 rounded-xl animate-pulse"></div>
      <div class="h-64 bg-slate-800/60 rounded-xl animate-pulse"></div>
    </div>

    <div v-else-if="ticket" class="grid grid-cols-1 xl:grid-cols-3 gap-5">
      <div class="xl:col-span-2 space-y-5">
        <div class="card border-indigo-500/30 bg-indigo-950/30">
          <div class="flex items-center justify-between mb-4 gap-3">
            <div>
              <h3 class="text-sm font-semibold text-white">Datos del Ticket</h3>
              <p v-if="resumen?.resumen_texto" class="text-xs text-slate-400 mt-1">{{ resumen.resumen_texto }}</p>
            </div>
            <button @click="extraerDatos" :disabled="extrayendo" class="btn-primary btn-sm">
              <svg v-if="extrayendo" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>
              <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7" /></svg>
              {{ extrayendo ? 'Extrayendo...' : 'Extraer / Actualizar' }}
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Dato label="Nombre osTicket" :valor="ticket.nombre_estudiante_osticket" />
            <Dato label="Email osTicket" :valor="ticket.email_estudiante" mono />
            <Dato label="C&oacute;digo osTicket" :valor="ticket.codigo_alumno_osticket" mono />
            <Dato label="Paso sugerido" :valor="pasoSugeridoTexto" />
            <Dato label="DNI" :valor="datosExt.dni" mono />
            <Dato label="Grado detectado" :valor="datosExt.grado_detectado || resumen?.grado_detectado" />
            <Dato label="Nombre detectado" :valor="datosExt.nombre_firma || datosExt.nombre_osticket" />
            <Dato label="C&oacute;digo detectado" :valor="datosExt.codigo_alumno" mono />
          </div>

          <div v-if="datosExt.resoluciones?.length" class="mt-3 flex flex-wrap gap-1.5">
            <span v-for="r in datosExt.resoluciones" :key="r" class="badge-nuevo text-[10px]">{{ r }}</span>
          </div>

          <div v-if="detalleArchivos.length > 0" class="mt-3 pt-3 border-t border-slate-700/50">
            <p class="text-xs text-slate-500 mb-2">{{ detalleArchivos.length }} archivo(s) analizados</p>
            <div class="space-y-1.5">
              <div v-for="arch in detalleArchivos" :key="arch.nombre" class="flex items-center gap-2 text-xs">
                <span class="text-slate-400 truncate flex-1">{{ arch.nombre }}</span>
                <span class="text-slate-600 flex-shrink-0">{{ arch.paginas }}p.</span>
                <span v-if="arch.error" class="text-red-400 flex-shrink-0">No encontrado</span>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center gap-2 mb-3">
            <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75" />
            </svg>
            <h3 class="text-sm font-semibold text-white">Cuerpo del Correo</h3>
            <span class="text-xs text-slate-500">{{ ticket.fecha }}</span>
          </div>
          <div class="bg-slate-900/60 rounded-lg p-4 max-h-72 overflow-y-auto">
            <pre class="text-xs text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">{{ ticket.cuerpo || 'Sin cuerpo disponible' }}</pre>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center gap-2 mb-4">
            <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372" />
            </svg>
            <h3 class="text-sm font-semibold text-white">Archivos Adjuntos ({{ ticket.adjuntos.length }})</h3>
          </div>

          <div v-if="ticket.adjuntos.length === 0" class="text-slate-500 text-sm text-center py-6">Sin archivos adjuntos</div>

          <div class="space-y-3">
            <div v-for="adj in ticket.adjuntos" :key="adj.id_archivo" class="border border-slate-700/50 rounded-lg overflow-hidden">
              <div class="flex items-center gap-3 px-4 py-3 bg-slate-800/40">
                <svg class="w-5 h-5 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625A3.375 3.375 0 0016.125 8.25h-1.5A1.125 1.125 0 0113.5 7.125v-1.5A3.375 3.375 0 0010.125 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                <span class="text-sm text-slate-200 font-medium truncate flex-1">{{ adj.nombre }}</span>
                <div class="flex items-center gap-2 flex-shrink-0">
                  <button v-if="esPdf(adj.nombre)" @click="abrirVisor(adj)" class="btn-ghost btn-sm">Ver</button>
                  <a :href="adj.url_visor" target="_blank" download class="btn-outline btn-sm">Descargar</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="space-y-5">
        <div class="card">
          <h3 class="text-sm font-semibold text-white mb-3">Informaci&oacute;n del Ticket</h3>
          <div class="space-y-2 text-xs">
            <div class="flex justify-between py-1.5 border-b border-slate-700/50">
              <span class="text-slate-500">Nro. Ticket</span>
              <span class="font-mono font-bold text-indigo-400">{{ ticket.numero_visual }}</span>
            </div>
            <div class="flex justify-between py-1.5 border-b border-slate-700/50">
              <span class="text-slate-500">Fecha</span>
              <span class="text-slate-300">{{ ticket.fecha }}</span>
            </div>
            <div class="flex justify-between py-1.5 border-b border-slate-700/50">
              <span class="text-slate-500">Estado bot</span>
              <span :class="badgeEstado(ticket.estado)">{{ ticket.estado }}</span>
            </div>
            <div class="flex justify-between py-1.5">
              <span class="text-slate-500">Adjuntos</span>
              <span class="text-slate-300">{{ ticket.adjuntos.length }} archivo(s)</span>
            </div>
          </div>
        </div>

        <div v-if="ticket.id_expediente" class="card border-emerald-500/30 bg-emerald-950/20">
          <p class="text-sm font-semibold text-emerald-300">Ticket Clasificado</p>
          <p class="text-xs text-slate-400 mt-1">Vinculado al expediente #{{ ticket.id_expediente }}.</p>
          <button @click="$router.push(`/expedientes/${ticket.expediente_uuid || ticket.id_expediente}`)" class="btn-success btn-sm mt-3 w-full justify-center">
            Ver Expediente
          </button>
        </div>

        <div v-else class="card">
          <h3 class="text-sm font-semibold text-white mb-4">Clasificar Ticket</h3>
          <div class="space-y-4">
            <div>
              <label class="input-label">Nombre del Alumno *</label>
              <input v-model="form.nombre_alumno" class="input-field" placeholder="Nombre completo" />
            </div>
            <div>
              <label class="input-label">C&oacute;digo del Alumno *</label>
              <input v-model="form.codigo_alumno" class="input-field font-mono" placeholder="Ej: 012200001" />
            </div>
            <div>
              <label class="input-label">Grado que Postula *</label>
              <select v-model="form.grado_postula" class="input-field">
                <option value="">Seleccionar...</option>
                <option value="Maestro">Maestro</option>
                <option value="Doctor">Doctor</option>
              </select>
            </div>
            <div>
              <label class="input-label">Paso Actual del Flujo *</label>
              <select v-model="form.id_paso" class="input-field">
                <option value="">Seleccionar paso...</option>
                <option v-for="p in pasos" :key="p.id_paso" :value="p.id_paso">Paso {{ p.id_paso }}: {{ p.nombre_paso }}</option>
              </select>
            </div>
            <div>
              <label class="input-label">T&iacute;tulo de Tesis</label>
              <textarea v-model="form.titulo_tesis" class="input-field resize-none" rows="2" placeholder="Si ya se conoce..."></textarea>
            </div>

            <button @click="clasificar" :disabled="!puedeClasificar || clasificando" class="btn-primary w-full justify-center">
              {{ clasificando ? 'Creando expediente...' : 'Crear Expediente y Clasificar' }}
            </button>
            <p v-if="errorClasificar" class="text-xs text-red-400 text-center">{{ errorClasificar }}</p>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="card text-center py-12">
      <p class="text-slate-400">Ticket no encontrado.</p>
      <button @click="$router.back()" class="btn-ghost mt-4">Volver a la bandeja</button>
    </div>

    <div v-if="visorModal" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex flex-col p-4" @click.self="cerrarVisor">
      <div class="flex items-center gap-3 mb-3">
        <p class="text-sm font-semibold text-white truncate flex-1">{{ visorModal.nombre }}</p>
        <a :href="visorModal.url_visor" target="_blank" download class="btn-outline btn-sm">Descargar</a>
        <button @click="cerrarVisor" class="btn-ghost btn-sm">Cerrar</button>
      </div>
      <iframe :src="visorModal.url_visor" class="w-full flex-1 bg-white rounded-lg border-0" :title="visorModal.nombre"></iframe>
    </div>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import api from '../api.js'

const Dato = defineComponent({
  props: { label: String, valor: [String, Number], mono: Boolean },
  setup(props) {
    return () => props.valor
      ? h('div', { class: 'flex items-center gap-2 p-2.5 rounded-lg bg-slate-800/50 min-w-0' }, [
          h('span', { class: 'text-xs text-slate-500 w-28 flex-shrink-0', innerHTML: props.label }),
          h('span', { class: ['text-sm text-white truncate', props.mono ? 'font-mono' : 'font-semibold'] }, String(props.valor)),
        ])
      : null
  },
})

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const ticket = ref(null)
const pasos = ref([])
const cargando = ref(true)
const extrayendo = ref(false)
const clasificando = ref(false)
const errorClasificar = ref('')
const visorModal = ref(null)
const datosExt = ref({})
const detalleArchivos = ref([])
const resumen = ref(null)

const form = ref({
  nombre_alumno: '',
  codigo_alumno: '',
  grado_postula: '',
  id_paso: '',
  titulo_tesis: ''
})

const puedeClasificar = computed(() =>
  form.value.nombre_alumno.trim() &&
  form.value.codigo_alumno.trim() &&
  form.value.grado_postula &&
  form.value.id_paso
)

const pasoSugeridoTexto = computed(() => {
  const paso = resumen.value?.paso_sugerido || datosExt.value.paso_sugerido
  if (!paso?.id_paso) return ''
  const confianza = paso.confianza ? ` (${Math.round(paso.confianza * 100)}%)` : ''
  return `Paso ${paso.id_paso}: ${paso.nombre_paso}${confianza}`
})

function badgeEstado(estado) {
  const map = {
    Pendiente_Descarga: 'badge-nuevo',
    Archivos_Descargados: 'badge-proceso',
    Datos_Extraidos: 'badge-observado',
    Clasificado: 'badge-graduado',
    Notificado: 'badge-graduado',
    Error: 'badge-error',
    Nuevo: 'badge-nuevo',
    Adjuntos_Descargados: 'badge-proceso',
    Procesado: 'badge-graduado',
  }
  return map[estado] || 'badge'
}

function esPdf(nombre) {
  return nombre?.toLowerCase().endsWith('.pdf')
}

function abrirVisor(adj) {
  visorModal.value = adj
}

function cerrarVisor() {
  visorModal.value = null
}

function prellenarDesdeDatos() {
  if (!ticket.value) return
  if (!form.value.nombre_alumno) form.value.nombre_alumno = ticket.value.nombre_estudiante_osticket || datosExt.value.nombre_firma || datosExt.value.nombre_osticket || ''
  if (!form.value.codigo_alumno) form.value.codigo_alumno = ticket.value.codigo_alumno_osticket || datosExt.value.codigo_alumno || ''
  if (!form.value.grado_postula) form.value.grado_postula = datosExt.value.grado_detectado || resumen.value?.grado_detectado || ''
  const paso = resumen.value?.paso_sugerido || datosExt.value.paso_sugerido
  if (!form.value.id_paso && paso?.id_paso) form.value.id_paso = paso.id_paso
}

async function extraerDatos() {
  extrayendo.value = true
  try {
    const res = await api.get(`/tickets/${route.params.uuid}/extraer-datos`)
    datosExt.value = res.data.datos_estructurados || {}
    detalleArchivos.value = res.data.detalle_archivos || []
    resumen.value = res.data.resumen || null
    prellenarDesdeDatos()
  } catch (e) {
    console.error('Error extrayendo datos:', e)
  } finally {
    extrayendo.value = false
  }
}

async function clasificar() {
  clasificando.value = true
  errorClasificar.value = ''
  try {
    const res = await api.post(`/tickets/${route.params.uuid}/clasificar`, null, {
      params: {
        id_paso: form.value.id_paso,
        nombre_alumno: form.value.nombre_alumno,
        codigo_alumno: form.value.codigo_alumno,
        grado_postula: form.value.grado_postula,
        titulo_tesis: form.value.titulo_tesis || undefined,
        usuario_nombre: auth.nombre
      }
    })
    router.push(`/expedientes/${res.data.uuid || res.data.id_expediente}`)
  } catch (e) {
    errorClasificar.value = 'Error al clasificar el ticket. Verifica los datos.'
    console.error(e)
  } finally {
    clasificando.value = false
  }
}

onMounted(async () => {
  try {
    const [tkRes, pasosRes] = await Promise.all([
      api.get(`/tickets/${route.params.uuid}`),
      api.get('/pasos')
    ])
    ticket.value = tkRes.data
    pasos.value = pasosRes.data
    const de = ticket.value.datos_extraidos
    if (de?.datos_estructurados) datosExt.value = de.datos_estructurados
    if (de?.detalle_archivos) detalleArchivos.value = de.detalle_archivos
    if (de?.resumen) resumen.value = de.resumen
    prellenarDesdeDatos()
  } catch (e) {
    console.error(e)
  } finally {
    cargando.value = false
  }
})
</script>
