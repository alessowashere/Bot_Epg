<template>
  <div class="p-6 space-y-5 animate-fade-in">
    <!-- Header -->
    <div class="flex items-center gap-3">
      <button @click="$router.back()" class="btn-ghost btn-sm">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" /></svg>
        Volver
      </button>
      <div class="flex-1">
        <div class="flex items-center gap-2 flex-wrap">
          <h2 class="text-xl font-bold text-white">Expediente #{{ exp?.id_expediente }}</h2>
          <span v-if="exp" :class="badgeEstado(exp.estado_expediente)">{{ exp.estado_expediente }}</span>
          <span v-if="exp" :class="exp.grado_postula === 'Doctor' ? 'badge bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'badge bg-blue-500/20 text-blue-300 border border-blue-500/30'">
            {{ exp.grado_postula }}
          </span>
        </div>
        <p class="text-slate-400 text-sm mt-0.5">{{ exp?.nombre_alumno }} — {{ exp?.codigo_alumno }}</p>
      </div>
    </div>

    <div v-if="cargando" class="space-y-4">
      <div class="h-32 bg-slate-800/60 rounded-xl animate-pulse"></div>
      <div class="h-48 bg-slate-800/60 rounded-xl animate-pulse"></div>
    </div>

    <div v-else-if="exp">
      <!-- Timeline de pasos -->
      <div class="card">
        <h3 class="text-sm font-semibold text-white mb-4">Progreso del Flujo</h3>
        <StepTimeline :paso-actual="exp.id_paso_actual" />
        <div class="mt-4 flex items-center gap-3 p-3 rounded-lg bg-indigo-600/10 border border-indigo-500/20">
          <div class="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-sm font-bold text-white flex-shrink-0">
            {{ exp.id_paso_actual }}
          </div>
          <div>
            <p class="text-sm font-semibold text-white">{{ exp.nombre_paso_actual }}</p>
            <p class="text-xs text-slate-400">Paso actual — Inicio: {{ exp.fecha_inicio }}</p>
          </div>
        </div>
      </div>

      <!-- Acciones de revisión humana -->
      <div v-if="exp.estado_expediente !== 'Archivado_Graduado'" class="card">
        <h3 class="text-sm font-semibold text-white mb-4">
          <span class="text-amber-400">⚡</span> Acción de Revisión Humana
        </h3>

        <!-- Aprobar / Avanzar -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/20">
            <div class="flex items-center gap-2 mb-2">
              <svg class="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              <p class="text-sm font-semibold text-emerald-300">
                {{ exp.id_paso_actual < 7 ? `Aprobar → Paso ${exp.id_paso_actual + 1}` : 'Completar (Graduado)' }}
              </p>
            </div>
            <p class="text-xs text-slate-400 mb-3">El expediente avanzará al siguiente paso del flujo.</p>
            <textarea v-model="notaAprobacion" class="input-field resize-none text-xs" rows="2" placeholder="Nota opcional de aprobación..."></textarea>
            <button @click="aprobar" :disabled="procesando" class="btn-success w-full justify-center mt-3">
              <svg v-if="procesando === 'aprobar'" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              ✓ Aprobar y Avanzar
            </button>
          </div>

          <div class="p-4 rounded-xl bg-red-950/30 border border-red-500/20">
            <div class="flex items-center gap-2 mb-2">
              <svg class="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" /></svg>
              <p class="text-sm font-semibold text-red-300">Observar Expediente</p>
            </div>
            <p class="text-xs text-slate-400 mb-3">El expediente regresa con observación. El alumno debe subsanar.</p>
            <textarea v-model="notaObservacion" class="input-field resize-none text-xs" rows="2" placeholder="Describe la observación... *requerido"></textarea>
            <button
              @click="observar"
              :disabled="procesando || !notaObservacion.trim()"
              class="btn-danger w-full justify-center mt-3"
            >
              <svg v-if="procesando === 'observar'" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
              ✗ Marcar como Observado
            </button>
          </div>
        </div>
      </div>

      <!-- Graduado -->
      <div v-else class="card border-emerald-500/30 bg-emerald-950/20 text-center py-6">
        <div class="w-14 h-14 rounded-full bg-emerald-600 flex items-center justify-center mx-auto mb-3 shadow-lg shadow-emerald-500/30">
          <svg class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" /></svg>
        </div>
        <h3 class="text-lg font-bold text-emerald-300">¡Alumno Graduado!</h3>
        <p class="text-slate-400 text-sm mt-1">Todos los pasos del flujo han sido completados exitosamente.</p>
      </div>

      <!-- Grid inferior: historial + tickets + asignaciones -->
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <!-- Historial de movimientos -->
        <div class="card">
          <h3 class="text-sm font-semibold text-white mb-4">
            <svg class="w-4 h-4 inline mr-1 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            Historial de Movimientos
          </h3>
          <div class="space-y-0 relative">
            <div class="absolute left-3 top-0 bottom-0 w-px bg-slate-700 -z-0"></div>
            <div v-for="(mov, idx) in exp.historial" :key="mov.id_movimiento" class="relative pl-8 pb-4">
              <!-- Dot -->
              <div :class="[
                'absolute left-1.5 top-1 w-3 h-3 rounded-full border-2 border-slate-900',
                accionColor(mov.accion)
              ]"></div>
              <!-- Contenido -->
              <div class="bg-slate-800/40 rounded-lg p-3">
                <div class="flex items-center justify-between mb-1">
                  <span :class="['text-xs font-semibold', accionTextColor(mov.accion)]">{{ mov.accion }}</span>
                  <span class="text-[10px] text-slate-500">{{ mov.fecha }}</span>
                </div>
                <p v-if="mov.nombre_paso" class="text-xs text-slate-300 mb-1">{{ mov.nombre_paso }}</p>
                <p v-if="mov.nota" class="text-xs text-slate-400 italic">{{ mov.nota }}</p>
                <p class="text-[10px] text-slate-600 mt-1">Por: {{ mov.usuario_nombre || 'Sistema' }}</p>
              </div>
            </div>
            <div v-if="exp.historial.length === 0" class="pl-8 text-xs text-slate-500">Sin movimientos registrados</div>
          </div>
        </div>

        <!-- Tickets vinculados + Asignaciones docentes -->
        <div class="space-y-5">
          <!-- Tickets vinculados -->
          <div class="card">
            <h3 class="text-sm font-semibold text-white mb-3">Tickets Vinculados ({{ exp.tickets.length }})</h3>
            <div class="space-y-2">
              <div v-for="t in exp.tickets" :key="t.ticket_id"
                class="flex items-center gap-3 p-2.5 rounded-lg bg-slate-800/40 hover:bg-slate-700/40 cursor-pointer transition-colors"
                @click="$router.push(`/bandeja/${t.ticket_id}`)">
                <span class="font-mono text-xs text-indigo-400 font-bold flex-shrink-0">#{{ t.numero_visual }}</span>
                <span class="text-xs text-slate-300 truncate flex-1">{{ t.asunto }}</span>
                <span class="text-[10px] text-slate-500 flex-shrink-0">{{ t.adjuntos_count }} adj.</span>
              </div>
              <p v-if="exp.tickets.length === 0" class="text-xs text-slate-500 text-center py-2">Sin tickets vinculados</p>
            </div>
          </div>

          <!-- Docentes asignados -->
          <div class="card">
            <h3 class="text-sm font-semibold text-white mb-3">Docentes Asignados</h3>
            <div class="space-y-2">
              <div v-for="asig in exp.asignaciones" :key="asig.id_asignacion"
                class="flex items-center gap-3 p-2.5 rounded-lg bg-slate-800/40">
                <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold text-slate-300 flex-shrink-0">
                  {{ asig.nombre_docente.split(' ')[0][0] }}
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-semibold text-white truncate">{{ asig.nombre_docente }}</p>
                  <p class="text-[10px] text-slate-500">{{ asig.especialidad }}</p>
                </div>
                <span class="text-[10px] font-medium text-violet-400 flex-shrink-0">{{ asig.rol_asignado }}</span>
              </div>
              <p v-if="exp.asignaciones.length === 0" class="text-xs text-slate-500 text-center py-2">Sin docentes asignados</p>
            </div>
          </div>

          <!-- Datos del expediente -->
          <div class="card" v-if="exp.titulo_tesis">
            <h3 class="text-sm font-semibold text-white mb-2">Título de Tesis</h3>
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
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import api from '../api.js'
import StepTimeline from '../components/StepTimeline.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const exp = ref(null)
const cargando = ref(true)
const procesando = ref(null)
const notaAprobacion = ref('')
const notaObservacion = ref('')

function badgeEstado(estado) {
  const map = {
    'En Proceso': 'badge-proceso',
    'Observado': 'badge-observado',
    'Archivado_Graduado': 'badge-graduado',
    'Caduco': 'badge-caduco',
  }
  return map[estado] || 'badge'
}

function accionColor(accion) {
  const map = {
    'Creado': 'bg-blue-500',
    'Clasificado': 'bg-indigo-500',
    'Avanzado': 'bg-emerald-500',
    'Observado': 'bg-amber-500',
    'Archivado': 'bg-emerald-600',
    'Desarchivado': 'bg-slate-500',
  }
  return map[accion] || 'bg-slate-600'
}

function accionTextColor(accion) {
  const map = {
    'Creado': 'text-blue-400',
    'Clasificado': 'text-indigo-400',
    'Avanzado': 'text-emerald-400',
    'Observado': 'text-amber-400',
    'Archivado': 'text-emerald-300',
    'Desarchivado': 'text-slate-400',
  }
  return map[accion] || 'text-slate-400'
}

async function cargar() {
  cargando.value = true
  try {
    const res = await api.get(`/expedientes/${route.params.id}`)
    exp.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    cargando.value = false
  }
}

async function aprobar() {
  procesando.value = 'aprobar'
  try {
    await api.post(`/expedientes/${route.params.id}/avanzar`, null, {
      params: { nota: notaAprobacion.value || undefined, usuario_nombre: auth.nombre }
    })
    notaAprobacion.value = ''
    await cargar()
  } catch (e) {
    console.error(e)
  } finally {
    procesando.value = null
  }
}

async function observar() {
  if (!notaObservacion.value.trim()) return
  procesando.value = 'observar'
  try {
    await api.post(`/expedientes/${route.params.id}/observar`, null, {
      params: { nota: notaObservacion.value, usuario_nombre: auth.nombre }
    })
    notaObservacion.value = ''
    await cargar()
  } catch (e) {
    console.error(e)
  } finally {
    procesando.value = null
  }
}

onMounted(cargar)
</script>
