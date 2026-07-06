<template>
  <div class="p-6 space-y-5 animate-fade-in">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-white">Directora</h2>
        <p class="text-slate-400 text-sm mt-0.5">Expedientes derivados y resoluciones pendientes</p>
      </div>
      <button @click="cargar" class="btn-ghost btn-sm">Actualizar</button>
    </div>

    <div v-if="cargando" class="space-y-3">
      <div v-for="i in 4" :key="i" class="h-32 bg-slate-800/60 rounded-xl animate-pulse"></div>
    </div>

    <div v-else class="space-y-4">
      <div v-if="expedientes.length === 0" class="card text-center py-10 text-slate-500">No hay expedientes derivados</div>

      <div v-for="exp in expedientes" :key="exp.uuid" class="card">
        <div class="flex flex-col lg:flex-row lg:items-start gap-4">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <h3 class="text-base font-bold text-white truncate">{{ exp.nombre_alumno }}</h3>
              <span class="badge-proceso">Paso {{ exp.id_paso_actual }}</span>
              <span v-if="exp.sub_estado" class="badge-observado">{{ exp.sub_estado }}</span>
            </div>
            <p class="text-xs font-mono text-slate-500 mt-1">{{ exp.codigo_alumno }}</p>
            <p v-if="exp.titulo_tesis" class="text-sm text-slate-300 mt-2 truncate-2">{{ exp.titulo_tesis }}</p>
            <button @click="$router.push(`/expedientes/${exp.uuid}`)" class="btn-ghost btn-sm mt-3">Abrir Expediente</button>
          </div>

          <div class="w-full lg:w-96 space-y-3">
            <div class="grid grid-cols-1 gap-2">
              <select v-for="(_, idx) in seleccion[exp.uuid]" :key="idx" v-model="seleccion[exp.uuid][idx]" class="input-field text-xs">
                <option value="">Dictaminante {{ idx + 1 }}</option>
                <option v-for="d in docentesDisponibles" :key="d.id_docente" :value="d.id_docente">
                  {{ d.nombre_completo }} ({{ d.carga_actual }}/{{ d.max_tesis_permitidas }})
                </option>
              </select>
            </div>
            <button @click="asignar(exp)" :disabled="procesando === exp.uuid || !puedeAsignar(exp.uuid)" class="btn-primary w-full justify-center">
              Asignar Dictaminantes
            </button>

            <div v-if="exp.resoluciones?.length" class="pt-3 border-t border-slate-700/60 space-y-2">
              <div v-for="res in exp.resoluciones" :key="res.id_resolucion" class="flex items-center gap-2">
                <span class="text-xs text-slate-300 truncate flex-1">{{ res.tipo_documento }}</span>
                <span :class="res.estado_firma === 'Firmado' ? 'badge-graduado' : 'badge-observado'">{{ res.estado_firma }}</span>
                <button v-if="res.estado_firma !== 'Firmado'" @click="aprobarResolucion(res.id_resolucion)" class="btn-success btn-sm">Aprobar</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import api from '../api.js'

const auth = useAuthStore()
const expedientes = ref([])
const docentes = ref([])
const cargando = ref(true)
const procesando = ref(null)
const seleccion = reactive({})

const docentesDisponibles = computed(() => docentes.value.filter(d => d.disponible))

function asegurarSeleccion() {
  for (const exp of expedientes.value) {
    if (!seleccion[exp.uuid]) seleccion[exp.uuid] = ['', '', '']
  }
}

function puedeAsignar(uuid) {
  const ids = (seleccion[uuid] || []).filter(Boolean)
  return ids.length === 3 && new Set(ids).size === 3
}

async function cargar() {
  cargando.value = true
  try {
    const [expRes, docRes] = await Promise.all([
      api.get('/directora/pendientes'),
      api.get('/docentes')
    ])
    expedientes.value = expRes.data.data
    docentes.value = docRes.data.data
    asegurarSeleccion()
  } catch (e) {
    console.error(e)
  } finally {
    cargando.value = false
  }
}

async function asignar(exp) {
  procesando.value = exp.uuid
  try {
    await api.post(`/expedientes/${exp.uuid}/asignar-dictaminantes`, null, {
      params: {
        docente_ids: seleccion[exp.uuid].join(','),
        usuario_nombre: auth.nombre
      }
    })
    seleccion[exp.uuid] = ['', '', '']
    await cargar()
  } catch (e) {
    console.error(e)
  } finally {
    procesando.value = null
  }
}

async function aprobarResolucion(id) {
  try {
    await api.post(`/resoluciones/${id}/aprobar`)
    await cargar()
  } catch (e) {
    console.error(e)
  }
}

onMounted(cargar)
</script>
