<template>
  <div class="p-6 space-y-5 animate-fade-in">
    <!-- Header con volver -->
    <div class="flex items-center gap-3">
      <button @click="$router.back()" class="btn-ghost btn-sm">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
        </svg>
        Volver
      </button>
      <div class="flex-1">
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
      <!-- Columna principal: cuerpo + adjuntos -->
      <div class="xl:col-span-2 space-y-5">

        <!-- Datos extraídos automáticamente -->
        <div class="card border-indigo-500/30 bg-indigo-950/30">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
              </svg>
              <h3 class="text-sm font-semibold text-white">Datos Extraídos por IA</h3>
            </div>
            <button @click="extraerDatos" :disabled="extrayendo" class="btn-primary btn-sm">
              <svg v-if="extrayendo" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" /></svg>
              {{ extrayendo ? 'Extrayendo PDFs...' : 'Extraer / Actualizar' }}
            </button>
          </div>

          <div v-if="Object.keys(datosExt).length === 0" class="text-slate-500 text-sm text-center py-3">
            Haz clic en "Extraer / Actualizar" para analizar el cuerpo del correo y los PDFs adjuntos.
          </div>
          <div v-else class="grid grid-cols-2 gap-3">
            <div v-if="datosExt.dni" class="flex items-center gap-2 p-2.5 rounded-lg bg-slate-800/50">
              <span class="text-xs text-slate-500 w-20 flex-shrink-0">DNI</span>
              <span class="text-sm font-mono font-bold text-white">{{ datosExt.dni }}</span>
            </div>
            <div v-if="datosExt.nombre_firma" class="flex items-center gap-2 p-2.5 rounded-lg bg-slate-800/50 col-span-2">
              <span class="text-xs text-slate-500 w-20 flex-shrink-0">Nombre</span>
              <span class="text-sm font-semibold text-white">{{ datosExt.nombre_firma }}</span>
            </div>
            <div v-if="datosExt.email_uac_alumno" class="flex items-center gap-2 p-2.5 rounded-lg bg-slate-800/50 col-span-2">
              <span class="text-xs text-slate-500 w-20 flex-shrink-0">Email UAC</span>
              <span class="text-sm text-indigo-300 font-mono">{{ datosExt.email_uac_alumno }}</span>
            </div>
            <div v-if="datosExt.codigo_alumno" class="flex items-center gap-2 p-2.5 rounded-lg bg-slate-800/50">
              <span class="text-xs text-slate-500 w-20 flex-shrink-0">Código</span>
              <span class="text-sm font-mono text-violet-300">{{ datosExt.codigo_alumno }}</span>
            </div>
            <div v-if="datosExt.nro_expediente_osticket" class="flex items-center gap-2 p-2.5 rounded-lg bg-slate-800/50">
              <span class="text-xs text-slate-500 w-20 flex-shrink-0">Nro. Exp.</span>
              <span class="text-sm font-mono text-amber-300">{{ datosExt.nro_expediente_osticket }}</span>
            </div>
            <div v-if="datosExt.resoluciones?.length" class="col-span-2 flex flex-wrap gap-1.5 p-2.5 rounded-lg bg-slate-800/50">
              <span class="text-xs text-slate-500 w-full">Resoluciones detectadas</span>
              <span v-for="r in datosExt.resoluciones" :key="r" class="badge-nuevo text-[10px]">{{ r }}</span>
            </div>
          </div>

          <!-- Detalle de archivos procesados -->
          <div v-if="detalleArchivos.length > 0" class="mt-3 pt-3 border-t border-slate-700/50">
            <p class="text-xs text-slate-500 mb-2">{{ detalleArchivos.length }} archivo(s) analizados:</p>
            <div class="space-y-1.5">
              <div v-for="arch in detalleArchivos" :key="arch.nombre" class="flex items-center gap-2 text-xs">
                <svg class="w-3.5 h-3.5 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                <span class="text-slate-400 truncate flex-1">{{ arch.nombre }}</span>
                <span class="text-slate-600 flex-shrink-0">{{ arch.paginas }}p.</span>
                <span v-if="arch.error" class="text-red-400 flex-shrink-0">⚠ No encontrado</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Cuerpo del correo -->
        <div class="card">
          <div class="flex items-center gap-2 mb-3">
            <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
            </svg>
            <h3 class="text-sm font-semibold text-white">Cuerpo del Correo</h3>
            <span class="text-xs text-slate-500">{{ ticket.fecha }}</span>
          </div>
          <div class="bg-slate-900/60 rounded-lg p-4 max-h-72 overflow-y-auto">
            <pre class="text-xs text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">{{ ticket.cuerpo || 'Sin cuerpo disponible' }}</pre>
          </div>
        </div>

        <!-- Adjuntos con visor PDF -->
        <div class="card">
          <div class="flex items-center gap-2 mb-4">
            <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
            </svg>
            <h3 class="text-sm font-semibold text-white">Archivos Adjuntos ({{ ticket.adjuntos.length }})</h3>
          </div>

          <div v-if="ticket.adjuntos.length === 0" class="text-slate-500 text-sm text-center py-6">
            Sin archivos adjuntos
          </div>

          <div class="space-y-3">
            <div v-for="adj in ticket.adjuntos" :key="adj.id_archivo" class="border border-slate-700/50 rounded-xl overflow-hidden">
              <!-- Header del adjunto -->
              <div class="flex items-center gap-3 px-4 py-3 bg-slate-800/40">
                <svg class="w-5 h-5 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                <span class="text-sm text-slate-200 font-medium truncate flex-1">{{ adj.nombre }}</span>
                <div class="flex items-center gap-2 flex-shrink-0">
                  <button @click="toggleVisor(adj.id_archivo)" class="btn-ghost btn-sm">
                    {{ visorAbierto === adj.id_archivo ? 'Cerrar' : 'Ver PDF' }}
                  </button>
                  <a :href="adj.url_visor" target="_blank" class="btn-outline btn-sm">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                    </svg>
                    Abrir
                  </a>
                </div>
              </div>
              <!-- Visor iframe embebido -->
              <div v-if="visorAbierto === adj.id_archivo && esPdf(adj.nombre)"
                class="bg-slate-900">
                <iframe
                  :src="adj.url_visor"
                  class="w-full border-0"
                  style="height: 500px;"
                  :title="adj.nombre"
                ></iframe>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Columna derecha: clasificación -->
      <div class="space-y-5">
        <!-- Estado actual -->
        <div class="card">
          <h3 class="text-sm font-semibold text-white mb-3">Información del Ticket</h3>
          <div class="space-y-2 text-xs">
            <div class="flex justify-between py-1.5 border-b border-slate-700/50">
              <span class="text-slate-500">Nº Ticket</span>
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

        <!-- Ya clasificado -->
        <div v-if="ticket.id_expediente" class="card border-emerald-500/30 bg-emerald-950/20">
          <div class="flex items-center gap-2 mb-2">
            <svg class="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-sm font-semibold text-emerald-300">Ticket Clasificado</p>
          </div>
          <p class="text-xs text-slate-400">Este ticket ya está vinculado al expediente #{{ ticket.id_expediente }}.</p>
          <button @click="$router.push(`/expedientes/${ticket.id_expediente}`)" class="btn-success btn-sm mt-3 w-full justify-center">
            Ver Expediente
          </button>
        </div>

        <!-- Formulario de clasificación -->
        <div v-else class="card">
          <h3 class="text-sm font-semibold text-white mb-4">
            <span class="text-indigo-400">⚡</span> Clasificar Ticket
          </h3>
          <div class="space-y-4">
            <div>
              <label class="input-label">Nombre del Alumno *</label>
              <input v-model="form.nombre_alumno" class="input-field" placeholder="Nombre completo" />
              <button v-if="datosExt.nombre_firma" @click="form.nombre_alumno = datosExt.nombre_firma"
                class="text-xs text-indigo-400 hover:text-indigo-300 mt-1">
                Usar detectado: "{{ datosExt.nombre_firma }}"
              </button>
            </div>
            <div>
              <label class="input-label">Código del Alumno *</label>
              <input v-model="form.codigo_alumno" class="input-field font-mono" placeholder="Ej: 012200001" />
              <button v-if="datosExt.codigo_alumno" @click="form.codigo_alumno = datosExt.codigo_alumno"
                class="text-xs text-indigo-400 hover:text-indigo-300 mt-1">
                Usar detectado: "{{ datosExt.codigo_alumno }}"
              </button>
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
                <option v-for="p in pasos" :key="p.id_paso" :value="p.id_paso">
                  Paso {{ p.id_paso }}: {{ p.nombre_paso }}
                </option>
              </select>
            </div>
            <div>
              <label class="input-label">Título de Tesis (opcional)</label>
              <textarea v-model="form.titulo_tesis" class="input-field resize-none" rows="2" placeholder="Si ya se conoce..."></textarea>
            </div>

            <button
              @click="clasificar"
              :disabled="!puedeClasificar || clasificando"
              class="btn-primary w-full justify-center"
            >
              <svg v-if="clasificando" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              {{ clasificando ? 'Creando expediente...' : 'Crear Expediente y Clasificar' }}
            </button>

            <p v-if="errorClasificar" class="text-xs text-red-400 text-center">{{ errorClasificar }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 404 -->
    <div v-else class="card text-center py-12">
      <p class="text-slate-400">Ticket no encontrado.</p>
      <button @click="$router.back()" class="btn-ghost mt-4">Volver a la bandeja</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import api from '../api.js'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const ticket = ref(null)
const pasos = ref([])
const cargando = ref(true)
const extrayendo = ref(false)
const clasificando = ref(false)
const visorAbierto = ref(null)
const errorClasificar = ref('')

const datosExt = ref({})
const detalleArchivos = ref([])

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

function badgeEstado(estado) {
  const map = {
    'Nuevo': 'badge-nuevo',
    'Adjuntos_Descargados': 'badge-proceso',
    'Procesado': 'badge-graduado',
    'Error': 'badge-error',
  }
  return map[estado] || 'badge'
}

function esPdf(nombre) {
  return nombre?.toLowerCase().endsWith('.pdf')
}

function toggleVisor(id) {
  visorAbierto.value = visorAbierto.value === id ? null : id
}

async function extraerDatos() {
  extrayendo.value = true
  try {
    const res = await api.get(`/tickets/${route.params.id}/extraer-datos`)
    datosExt.value = res.data.datos_estructurados || {}
    detalleArchivos.value = res.data.detalle_archivos || []
    // Prellenar el form con los datos extraídos
    if (datosExt.value.nombre_firma) form.value.nombre_alumno = datosExt.value.nombre_firma
    if (datosExt.value.codigo_alumno) form.value.codigo_alumno = datosExt.value.codigo_alumno
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
    const res = await api.post(`/tickets/${route.params.id}/clasificar`, null, {
      params: {
        id_paso: form.value.id_paso,
        nombre_alumno: form.value.nombre_alumno,
        codigo_alumno: form.value.codigo_alumno,
        grado_postula: form.value.grado_postula,
        titulo_tesis: form.value.titulo_tesis || undefined,
        usuario_nombre: auth.nombre
      }
    })
    router.push(`/expedientes/${res.data.id_expediente}`)
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
      api.get(`/tickets/${route.params.id}`),
      api.get('/pasos')
    ])
    ticket.value = tkRes.data
    pasos.value = pasosRes.data

    // Cargar datos ya extraídos si existen
    const de = ticket.value.datos_extraidos
    if (de?.datos_estructurados) {
      datosExt.value = de.datos_estructurados
      detalleArchivos.value = de.detalle_archivos || []
    }
  } catch (e) {
    console.error(e)
  } finally {
    cargando.value = false
  }
})
</script>
