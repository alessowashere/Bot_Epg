<template>
  <div class="space-y-4">
    <!-- Cargando -->
    <div v-if="cargando" class="space-y-3">
      <div v-for="i in 2" :key="i" class="h-24 bg-slate-800/40 rounded-lg animate-pulse"></div>
    </div>

    <!-- Sin revisiones -->
    <div v-else-if="!revisiones.length" class="text-center py-6">
      <div class="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center mx-auto mb-3">
        <svg class="w-6 h-6 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <p class="text-slate-500 text-sm">Sin revisiones registradas</p>
      <p class="text-slate-600 text-xs mt-1">Las observaciones aparecerán aquí</p>
    </div>

    <!-- Timeline de revisiones -->
    <div v-else class="relative">
      <!-- Línea vertical del timeline -->
      <div class="absolute left-4 top-0 bottom-0 w-px bg-slate-700/50"></div>

      <div class="space-y-4">
        <div
          v-for="(rev, idx) in revisiones"
          :key="rev.id_revision"
          class="flex gap-4 relative"
        >
          <!-- Punto del timeline -->
          <div :class="['w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 z-10 border-2', puntoBg(rev)]">
            V{{ rev.version_documento }}
          </div>

          <!-- Tarjeta de revisión -->
          <div :class="['flex-1 rounded-lg border p-4 mb-2', cardClass(rev)]">
            <div class="flex items-start justify-between gap-3 mb-2">
              <div>
                <div class="flex items-center gap-2 flex-wrap">
                  <span :class="['text-xs font-semibold', textoTipo(rev.tipo_revision)]">
                    {{ rev.tipo_revision }}
                  </span>
                  <span class="text-xs text-slate-500">Version {{ rev.version_documento }}</span>
                  <span :class="['text-[10px] px-1.5 py-0.5 rounded-full border', badgeEstado(rev.estado)]">
                    {{ rev.estado }}
                  </span>
                </div>
                <p v-if="rev.docente" class="text-xs text-slate-400 mt-0.5">Por: {{ rev.docente }}</p>
              </div>
              <span class="text-[10px] text-slate-500 flex-shrink-0">{{ rev.fecha_revision }}</span>
            </div>

            <p v-if="rev.descripcion_observacion" class="text-sm text-slate-300 leading-relaxed">
              {{ rev.descripcion_observacion }}
            </p>

            <!-- Archivos adjuntos de la revisión -->
            <div class="flex gap-2 mt-3 flex-wrap">
              <a
                v-if="rev.archivo_observado_url"
                :href="rev.archivo_observado_url"
                target="_blank"
                class="btn-ghost btn-sm text-xs gap-1"
              >
                <svg class="w-3.5 h-3.5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625A3.375 3.375 0 0016.125 8.25h-1.5A1.125 1.125 0 0113.5 7.125v-1.5A3.375 3.375 0 0010.125 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                Doc. Observado
              </a>
              <a
                v-if="rev.archivo_corregido_url"
                :href="rev.archivo_corregido_url"
                target="_blank"
                class="btn-ghost btn-sm text-xs gap-1"
              >
                <svg class="w-3.5 h-3.5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
                Doc. Corregido
              </a>
            </div>

            <!-- Acciones -->
            <div v-if="rev.estado === 'Pendiente'" class="flex gap-2 mt-3 pt-3 border-t border-slate-700/40">
              <button @click="marcarCorregido(rev)" :disabled="procesando === rev.id_revision" class="btn-success btn-sm text-xs">
                Marcar Corregido
              </button>
            </div>
            <div v-else-if="rev.estado === 'Corregido'" class="flex gap-2 mt-3 pt-3 border-t border-slate-700/40">
              <button @click="marcarAceptado(rev)" :disabled="procesando === rev.id_revision" class="btn-primary btn-sm text-xs">
                Aceptar Corrección
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Botón agregar nueva revisión -->
    <div v-if="mostrarAgregar" class="mt-4 pt-4 border-t border-slate-700/50">
      <h4 class="text-xs font-semibold text-slate-300 mb-3">Registrar Observación</h4>
      <div class="space-y-3">
        <select v-model="nuevaRevision.tipo_revision" class="input-field text-sm">
          <option value="Observacion">Observación</option>
          <option value="Corrección">Corrección</option>
          <option value="Aprobacion">Aprobación</option>
        </select>
        <textarea
          v-model="nuevaRevision.descripcion"
          class="input-field resize-none text-sm"
          rows="3"
          placeholder="Describe la observación o corrección..."
        ></textarea>
        <input
          v-model="nuevaRevision.archivo_url"
          class="input-field text-sm"
          placeholder="URL del documento observado (opcional)"
        />
        <div class="flex gap-2 justify-end">
          <button @click="mostrarAgregar = false" class="btn-ghost btn-sm text-xs">Cancelar</button>
          <button
            @click="agregarRevision"
            :disabled="!nuevaRevision.descripcion.trim() || creando"
            class="btn-danger btn-sm text-xs"
          >
            {{ creando ? 'Registrando...' : 'Registrar Observación' }}
          </button>
        </div>
        <p v-if="errorCrear" class="text-xs text-red-400">{{ errorCrear }}</p>
      </div>
    </div>
    <button v-else @click="mostrarAgregar = true" class="btn-outline btn-sm w-full justify-center text-xs">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      Agregar Observación
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api.js'
import { useAuthStore } from '../stores/auth.js'

const props = defineProps({
  expedienteRef: { type: String, required: true },
})

const emit = defineEmits(['actualizado'])
const auth = useAuthStore()

const revisiones = ref([])
const cargando = ref(false)
const procesando = ref(null)
const mostrarAgregar = ref(false)
const creando = ref(false)
const errorCrear = ref('')
const nuevaRevision = ref({ tipo_revision: 'Observacion', descripcion: '', archivo_url: '' })

function puntoBg(rev) {
  const mapa = {
    Pendiente: 'bg-amber-500/20 border-amber-500 text-amber-300',
    Corregido: 'bg-blue-500/20 border-blue-500 text-blue-300',
    Aceptado: 'bg-emerald-500/20 border-emerald-500 text-emerald-300',
  }
  return mapa[rev.estado] || 'bg-slate-700 border-slate-600 text-slate-300'
}

function cardClass(rev) {
  const mapa = {
    Pendiente: 'bg-amber-950/20 border-amber-500/20',
    Corregido: 'bg-blue-950/20 border-blue-500/20',
    Aceptado: 'bg-emerald-950/20 border-emerald-500/20',
  }
  return mapa[rev.estado] || 'bg-slate-800/40 border-slate-700/50'
}

function textoTipo(tipo) {
  const mapa = {
    Observacion: 'text-amber-300',
    'Corrección': 'text-blue-300',
    Aprobacion: 'text-emerald-300',
  }
  return mapa[tipo] || 'text-slate-300'
}

function badgeEstado(estado) {
  const mapa = {
    Pendiente: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
    Corregido: 'bg-blue-500/10 border-blue-500/30 text-blue-300',
    Aceptado: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
  }
  return mapa[estado] || 'bg-slate-700/50 border-slate-600 text-slate-400'
}

async function cargar() {
  cargando.value = true
  try {
    const res = await api.get(`/expedientes/${props.expedienteRef}/revisiones`)
    revisiones.value = res.data.data
  } catch (e) {
    console.error('Error cargando revisiones:', e)
  } finally {
    cargando.value = false
  }
}

async function agregarRevision() {
  if (!nuevaRevision.value.descripcion.trim()) return
  creando.value = true
  errorCrear.value = ''
  try {
    await api.post(`/expedientes/${props.expedienteRef}/revisiones`, null, {
      params: {
        tipo_revision: nuevaRevision.value.tipo_revision,
        descripcion_observacion: nuevaRevision.value.descripcion,
        archivo_observado_url: nuevaRevision.value.archivo_url || undefined,
        usuario_nombre: auth.nombre,
      }
    })
    nuevaRevision.value = { tipo_revision: 'Observacion', descripcion: '', archivo_url: '' }
    mostrarAgregar.value = false
    await cargar()
    emit('actualizado')
  } catch (e) {
    errorCrear.value = e.response?.data?.detail || 'Error al registrar la revisión.'
  } finally {
    creando.value = false
  }
}

async function marcarCorregido(rev) {
  procesando.value = rev.id_revision
  try {
    await api.put(`/revisiones/${rev.id_revision}/corregido`, null, {
      params: { usuario_nombre: auth.nombre }
    })
    await cargar()
    emit('actualizado')
  } finally {
    procesando.value = null
  }
}

async function marcarAceptado(rev) {
  procesando.value = rev.id_revision
  try {
    await api.put(`/revisiones/${rev.id_revision}/aceptado`, null, {
      params: { usuario_nombre: auth.nombre }
    })
    await cargar()
    emit('actualizado')
  } finally {
    procesando.value = null
  }
}

onMounted(cargar)
</script>
