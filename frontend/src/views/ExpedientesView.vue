<template>
  <div class="page-shell animate-fade-in">
    <div class="flex items-center justify-between">
      <div>
        <p class="eyebrow">Operacion academica</p>
        <h2 class="page-title">Expedientes oficiales</h2>
        <p class="page-subtitle">Seguimiento del flujo de tesis</p>
      </div>
    </div>

    <div class="card p-4 flex flex-wrap gap-3">
      <div class="relative flex-1 min-w-48">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803a7.5 7.5 0 0010.607 10.607z" />
        </svg>
        <input v-model="filtros.busqueda" @keyup.enter="buscar" class="input-field pl-9" placeholder="Buscar alumno, c&oacute;digo, t&iacute;tulo..." />
      </div>
      <select v-model="filtros.id_paso" @change="buscar" class="input-field w-56">
        <option value="">Todos los pasos</option>
        <option v-for="p in pasos" :key="p.id_paso" :value="p.id_paso">Paso {{ p.id_paso }}: {{ p.nombre_paso }}</option>
      </select>
      <select v-model="filtros.estado" @change="buscar" class="input-field w-44">
        <option value="">Todos los estados</option>
        <option value="En Proceso">En Proceso</option>
        <option value="Observado">Observado</option>
        <option value="Archivado_Graduado">Graduados</option>
        <option value="Caduco">Caducos</option>
      </select>
      <select v-model="filtros.anio" @change="buscar" class="input-field w-32">
        <option value="">Todos los años</option>
        <option v-for="anio in anios" :key="anio" :value="anio">{{ anio }}</option>
      </select>
      <select v-model="filtros.requisitos" @change="buscar" class="input-field w-48">
        <option value="">Todos los requisitos</option>
        <option value="pendientes">Con pendientes</option>
        <option value="observados">Con observaciones</option>
        <option value="listos">Listos para revisar</option>
      </select>
      <select v-model.number="porPagina" @change="pagina = 1; cargar()" class="input-field w-28">
        <option :value="10">10</option>
        <option :value="25">25</option>
        <option :value="50">50</option>
      </select>
      <button @click="limpiar" class="btn-ghost btn-sm">Limpiar</button>
    </div>

    <div class="flex gap-2 overflow-x-auto pb-1">
      <button @click="filtros.id_paso = ''; buscar()" :class="['btn-sm flex-shrink-0', !filtros.id_paso ? 'btn-primary' : 'btn-ghost']">Todos</button>
      <button
        v-for="p in pasos"
        :key="p.id_paso"
        @click="filtros.id_paso = p.id_paso; buscar()"
        :class="['btn-sm flex-shrink-0', Number(filtros.id_paso) === p.id_paso ? 'btn-primary' : 'btn-ghost']"
      >
        P{{ p.id_paso }}: {{ p.nombre_paso.split(' ').slice(0, 2).join(' ') }}
      </button>
    </div>

    <div class="card p-0 overflow-hidden">
      <div v-if="cargando" class="p-4 space-y-3">
        <div v-for="i in 8" :key="i" class="h-16 bg-slate-700/30 rounded-lg animate-pulse"></div>
      </div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Estudiante y Expediente</th>
            <th class="hidden md:table-cell">Grado</th>
            <th>Paso Actual</th>
            <th>Estado Principal</th>
            <th class="hidden lg:table-cell">Sub Estado</th>
            <th class="hidden lg:table-cell">Últ. Movimiento</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="expedientes.length === 0">
            <td colspan="7" class="text-center py-12 text-slate-500 font-medium">No se encontraron expedientes con los filtros aplicados.</td>
          </tr>
          <tr v-for="exp in expedientes" :key="exp.uuid || exp.id_expediente" class="cursor-pointer hover:bg-slate-700/20 transition-colors" @click="abrirExpediente(exp)">
            <td>
              <div class="flex items-center gap-4">
                <div class="w-10 h-10 rounded-md border border-sky-200 bg-sky-50 flex items-center justify-center text-sky-800 font-bold text-lg shadow-sm flex-shrink-0 dark:border-cyan-500/30 dark:bg-cyan-500/15 dark:text-cyan-100">
                  {{ exp.nombre_alumno.charAt(0).toUpperCase() }}
                </div>
                <div>
                  <p class="font-bold text-slate-900 dark:text-white text-[15px] tracking-tight">{{ exp.nombre_alumno }}</p>
                  <p class="text-xs font-mono text-sky-700 dark:text-cyan-300 mt-0.5 font-semibold">EXP-2026-{{ String(exp.id_expediente).padStart(4, '0') }} <span class="text-slate-500 dark:text-slate-400">| {{ exp.codigo_alumno }}</span></p>
                  <p v-if="exp.titulo_tesis" class="text-xs text-slate-600 dark:text-slate-400 mt-1 max-w-sm hidden xl:block leading-relaxed" :title="exp.titulo_tesis">
                    {{ exp.titulo_tesis.length > 80 ? exp.titulo_tesis.substring(0, 80) + '...' : exp.titulo_tesis }}
                  </p>
                </div>
              </div>
            </td>
            <td class="hidden md:table-cell">
              <span :class="exp.grado_postula === 'Doctor' ? 'badge badge-proceso' : 'badge badge-nuevo'">
                {{ exp.grado_postula }}
              </span>
            </td>
            <td>
              <div class="flex items-center gap-3">
                <div class="w-7 h-7 rounded-md bg-slate-100 border border-slate-300 shadow-inner flex items-center justify-center text-xs font-black text-sky-700 flex-shrink-0 dark:bg-slate-800 dark:border-slate-600 dark:text-cyan-300">
                  {{ exp.id_paso_actual }}
                </div>
                <span class="text-xs font-semibold text-slate-700 dark:text-slate-200 hidden xl:block">{{ exp.nombre_paso_actual }}</span>
              </div>
            </td>
            <td><span :class="badgeEstado(exp.estado_expediente) + ' shadow-sm'">{{ exp.estado_expediente }}</span></td>
            <td class="hidden lg:table-cell">
              <span v-if="exp.sub_estado" class="badge-observado text-[11px] uppercase tracking-wider">{{ exp.sub_estado }}</span>
              <span v-else class="text-xs text-slate-600 font-medium">-</span>
            </td>
            <td class="hidden lg:table-cell text-xs text-slate-400 font-mono">{{ exp.fecha_ultimo_movimiento }}</td>
            <td>
              <button class="icon-btn" title="Abrir expediente" aria-label="Abrir expediente" @click.stop="abrirExpediente(exp)">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex items-center justify-between gap-3 text-xs text-slate-500">
      <span>{{ total }} expediente(s) encontrados</span>
      <div class="flex items-center gap-2">
        <button @click="cambiarPagina(pagina - 1)" :disabled="pagina <= 1" class="btn-ghost btn-sm">Anterior</button>
        <span class="text-slate-300">P&aacute;gina {{ pagina }} / {{ totalPaginas }}</span>
        <button @click="cambiarPagina(pagina + 1)" :disabled="pagina >= totalPaginas" class="btn-ghost btn-sm">Siguiente</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api.js'

const route = useRoute()
const router = useRouter()
const expedientes = ref([])
const pasos = ref([])
const anios = ref([])
const cargando = ref(true)
const pagina = ref(1)
const porPagina = ref(25)
const total = ref(0)
const totalPaginas = ref(1)

const filtros = ref({
  busqueda: '',
  id_paso: route.query.id_paso ? Number(route.query.id_paso) : (route.query.paso ? Number(route.query.paso) : ''),
  estado: route.query.estado || '',
  requisitos: route.query.requisitos || '',
  anio: route.query.anio ? Number(route.query.anio) : '',
  antiguedad_anios: route.query.antiguedad_anios ? Number(route.query.antiguedad_anios) : '',
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

function abrirExpediente(exp) {
  router.push(`/expedientes/${exp.uuid || exp.id_expediente}`)
}

function buscar() {
  pagina.value = 1
  cargar()
}

function cambiarPagina(nuevaPagina) {
  if (nuevaPagina < 1 || nuevaPagina > totalPaginas.value) return
  pagina.value = nuevaPagina
  cargar()
}

async function cargar() {
  cargando.value = true
  try {
    const params = { page: pagina.value, per_page: porPagina.value }
    if (filtros.value.id_paso) params.id_paso = filtros.value.id_paso
    if (filtros.value.estado) params.estado = filtros.value.estado
    if (filtros.value.requisitos) params.requisitos = filtros.value.requisitos
    if (filtros.value.anio) params.anio = filtros.value.anio
    if (filtros.value.antiguedad_anios) params.antiguedad_anios = filtros.value.antiguedad_anios
    if (filtros.value.busqueda.trim()) params.busqueda = filtros.value.busqueda.trim()
    const res = await api.get('/expedientes', { params })
    expedientes.value = res.data.data
    total.value = res.data.total || 0
    totalPaginas.value = res.data.total_pages || 1
  } catch (e) {
    console.error(e)
  } finally {
    cargando.value = false
  }
}

function limpiar() {
  filtros.value = { busqueda: '', id_paso: '', estado: '', requisitos: '', anio: '', antiguedad_anios: '' }
  pagina.value = 1
  cargar()
}

onMounted(async () => {
  const [_, pasosRes, historicoRes] = await Promise.all([cargar(), api.get('/pasos'), api.get('/dashboard/seguimiento-historico')])
  pasos.value = pasosRes.data
  anios.value = historicoRes.data.anios_disponibles || []
})

watch(() => route.query, (query) => {
  filtros.value.id_paso = query.id_paso ? Number(query.id_paso) : (query.paso ? Number(query.paso) : '')
  filtros.value.estado = query.estado || ''
  filtros.value.requisitos = query.requisitos || ''
  filtros.value.anio = query.anio ? Number(query.anio) : ''
  filtros.value.antiguedad_anios = query.antiguedad_anios ? Number(query.antiguedad_anios) : ''
  pagina.value = 1
  cargar()
})
</script>
