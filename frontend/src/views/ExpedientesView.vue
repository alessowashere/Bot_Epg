<template>
  <div class="p-6 space-y-5 animate-fade-in">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-white">Expedientes</h2>
        <p class="text-slate-400 text-sm mt-0.5">Gestión del flujo de tesis — 7 pasos</p>
      </div>
    </div>

    <!-- Filtros -->
    <div class="card p-4 flex flex-wrap gap-3">
      <div class="relative flex-1 min-w-48">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803a7.5 7.5 0 0010.607 10.607z" />
        </svg>
        <input v-model="filtros.busqueda" @input="cargar" class="input-field pl-9" placeholder="Buscar alumno, código, título..." />
      </div>
      <select v-model="filtros.id_paso" @change="cargar" class="input-field w-56">
        <option value="">Todos los pasos</option>
        <option v-for="p in pasos" :key="p.id_paso" :value="p.id_paso">
          Paso {{ p.id_paso }}: {{ p.nombre_paso }}
        </option>
      </select>
      <select v-model="filtros.estado" @change="cargar" class="input-field w-44">
        <option value="">Todos los estados</option>
        <option value="En Proceso">En Proceso</option>
        <option value="Observado">Observado</option>
        <option value="Archivado_Graduado">Graduados</option>
        <option value="Caduco">Caducos</option>
      </select>
      <button @click="limpiar" class="btn-ghost btn-sm">Limpiar</button>
    </div>

    <!-- Tabs de pasos rápidos -->
    <div class="flex gap-2 overflow-x-auto pb-1">
      <button
        @click="filtros.id_paso = ''; cargar()"
        :class="['btn-sm flex-shrink-0', !filtros.id_paso ? 'btn-primary' : 'btn-ghost']"
      >Todos</button>
      <button
        v-for="p in pasos"
        :key="p.id_paso"
        @click="filtros.id_paso = p.id_paso; cargar()"
        :class="['btn-sm flex-shrink-0', filtros.id_paso === p.id_paso ? 'btn-primary' : 'btn-ghost']"
      >
        P{{ p.id_paso }}: {{ p.nombre_paso.split(' ').slice(0, 2).join(' ') }}
      </button>
    </div>

    <!-- Tabla de expedientes -->
    <div class="card p-0 overflow-hidden">
      <div v-if="cargando" class="p-4 space-y-3">
        <div v-for="i in 8" :key="i" class="h-16 bg-slate-700/30 rounded-lg animate-pulse"></div>
      </div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Alumno</th>
            <th class="hidden md:table-cell">Grado</th>
            <th>Paso actual</th>
            <th>Estado</th>
            <th class="hidden lg:table-cell">Último movimiento</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="expedientes.length === 0">
            <td colspan="6" class="text-center py-12 text-slate-500">
              <svg class="w-10 h-10 mx-auto mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932H19.05a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776" /></svg>
              No hay expedientes con estos filtros
            </td>
          </tr>
          <tr v-for="exp in expedientes" :key="exp.id_expediente" class="cursor-pointer" @click="$router.push(`/expedientes/${exp.id_expediente}`)">
            <td>
              <div>
                <p class="font-semibold text-white">{{ exp.nombre_alumno }}</p>
                <p class="text-xs font-mono text-slate-500">{{ exp.codigo_alumno }}</p>
                <p v-if="exp.titulo_tesis" class="text-xs text-slate-400 truncate-2 mt-0.5 max-w-xs hidden xl:block">{{ exp.titulo_tesis }}</p>
              </div>
            </td>
            <td class="hidden md:table-cell">
              <span :class="exp.grado_postula === 'Doctor' ? 'badge bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'badge bg-blue-500/20 text-blue-300 border border-blue-500/30'">
                {{ exp.grado_postula }}
              </span>
            </td>
            <td>
              <div class="flex items-center gap-2">
                <div class="w-6 h-6 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                  {{ exp.id_paso_actual }}
                </div>
                <span class="text-xs text-slate-300 hidden xl:block">{{ exp.nombre_paso_actual }}</span>
              </div>
            </td>
            <td>
              <span :class="badgeEstado(exp.estado_expediente)">{{ exp.estado_expediente }}</span>
            </td>
            <td class="hidden lg:table-cell text-xs text-slate-500">
              {{ exp.fecha_ultimo_movimiento }}
            </td>
            <td>
              <button class="btn-ghost btn-sm" @click.stop="$router.push(`/expedientes/${exp.id_expediente}`)">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="text-xs text-slate-500 text-right">{{ expedientes.length }} expediente(s) encontrados</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api.js'

const route = useRoute()
const expedientes = ref([])
const pasos = ref([])
const cargando = ref(true)

const filtros = ref({
  busqueda: '',
  id_paso: route.query.paso ? Number(route.query.paso) : '',
  estado: route.query.estado || ''
})

function badgeEstado(estado) {
  const map = {
    'En Proceso': 'badge-proceso',
    'Observado': 'badge-observado',
    'Archivado_Graduado': 'badge-graduado',
    'Caduco': 'badge-caduco',
  }
  return map[estado] || 'badge'
}

async function cargar() {
  cargando.value = true
  try {
    const params = {}
    if (filtros.value.id_paso) params.id_paso = filtros.value.id_paso
    if (filtros.value.estado) params.estado = filtros.value.estado
    if (filtros.value.busqueda.trim()) params.busqueda = filtros.value.busqueda.trim()
    const res = await api.get('/expedientes', { params })
    expedientes.value = res.data.data
  } catch (e) {
    console.error(e)
  } finally {
    cargando.value = false
  }
}

function limpiar() {
  filtros.value = { busqueda: '', id_paso: '', estado: '' }
  cargar()
}

onMounted(async () => {
  const [_, pasosRes] = await Promise.all([cargar(), api.get('/pasos')])
  pasos.value = pasosRes.data
})
</script>
