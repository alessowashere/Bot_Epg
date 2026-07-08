<template>
  <div class="p-6 space-y-6 animate-fade-in">
    <!-- Header -->
    <div>
      <h2 class="text-2xl font-bold text-white">Dashboard</h2>
      <p class="text-slate-400 text-sm mt-1">Resumen del sistema — {{ fechaHoy }}</p>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div v-for="kpi in kpis" :key="kpi.label" class="card hover:border-indigo-500/40 transition-all duration-200 group">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs text-slate-400 font-medium">{{ kpi.label }}</p>
            <p class="text-3xl font-bold mt-1" :class="kpi.color">
              <span v-if="cargando" class="inline-block w-16 h-8 bg-slate-700 rounded animate-pulse"></span>
              <span v-else>{{ kpi.valor }}</span>
            </p>
          </div>
          <div :class="['w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0', kpi.bgIcon]" v-html="kpi.icon"></div>
        </div>
        <p class="text-xs text-slate-500 mt-2">{{ kpi.sub }}</p>
      </div>
    </div>

    <!-- Distribución por pasos + Tickets sin clasificar -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
      <!-- Distribución por pasos -->
      <div class="xl:col-span-2 card">
        <div class="flex items-center justify-between mb-5">
          <h3 class="text-base font-semibold text-white">Expedientes por Paso del Flujo</h3>
          <router-link to="/expedientes" class="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
            Ver todos →
          </router-link>
        </div>
        <div v-if="cargando" class="space-y-3">
          <div v-for="i in 7" :key="i" class="h-10 bg-slate-700/50 rounded-lg animate-pulse"></div>
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="paso in distribucion"
            :key="paso.id_paso"
            class="flex items-center gap-3 group cursor-pointer"
            @click="$router.push(`/expedientes?id_paso=${paso.id_paso}`)"
          >
            <!-- Número del paso -->
            <div class="w-7 h-7 rounded-full bg-slate-700 group-hover:bg-indigo-600 text-slate-400 group-hover:text-white flex items-center justify-center text-xs font-bold transition-all duration-200 flex-shrink-0">
              {{ paso.id_paso }}
            </div>
            <!-- Nombre y barra -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-1">
                <p class="text-xs text-slate-300 truncate group-hover:text-white transition-colors">{{ paso.nombre_paso }}</p>
                <span class="text-xs font-bold text-slate-300 ml-2 flex-shrink-0">{{ paso.total }}</span>
              </div>
              <div class="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div
                  class="h-full bg-gradient-to-r from-indigo-600 to-violet-600 rounded-full transition-all duration-700"
                  :style="{ width: maxDistribucion > 0 ? `${(paso.total / maxDistribucion) * 100}%` : '0%' }"
                ></div>
              </div>
            </div>
          </div>
          <p v-if="distribucion.length === 0" class="text-slate-500 text-sm text-center py-4">Sin datos disponibles</p>
        </div>
      </div>

      <!-- Panel de alertas y acciones rápidas -->
      <div class="space-y-4">
        <!-- Alertas críticas -->
        <div class="card">
          <h3 class="text-base font-semibold text-white mb-4">Acciones Urgentes</h3>
          <div class="space-y-3">
            <!-- Tickets sin clasificar -->
            <div
              @click="$router.push('/bandeja')"
              class="flex items-center gap-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/20 cursor-pointer transition-all duration-200"
            >
              <div class="w-2 h-2 bg-amber-400 rounded-full animate-pulse-dot flex-shrink-0"></div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-semibold text-amber-300">Tickets por clasificar</p>
                <p class="text-xl font-bold text-amber-400">{{ cargando ? '—' : datos?.tickets_sin_clasificar }}</p>
              </div>
              <svg class="w-4 h-4 text-amber-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            </div>

            <!-- Expedientes observados -->
            <div
              @click="$router.push('/expedientes?estado=Observado')"
              class="flex items-center gap-3 p-3 rounded-lg bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 cursor-pointer transition-all duration-200"
            >
              <div class="w-2 h-2 bg-red-400 rounded-full flex-shrink-0"></div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-semibold text-red-300">Expedientes observados</p>
                <p class="text-xl font-bold text-red-400">{{ cargando ? '—' : datos?.observados }}</p>
              </div>
              <svg class="w-4 h-4 text-red-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
              </svg>
            </div>

            <!-- Graduados -->
            <div class="flex items-center gap-3 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <div class="w-2 h-2 bg-emerald-400 rounded-full flex-shrink-0"></div>
              <div class="flex-1 min-w-0">
                <p class="text-xs font-semibold text-emerald-300">Alumnos graduados</p>
                <p class="text-xl font-bold text-emerald-400">{{ cargando ? '—' : datos?.graduados }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Acceso rápido -->
        <div class="card">
          <h3 class="text-sm font-semibold text-white mb-3">Acceso Rápido</h3>
          <div class="space-y-2">
            <router-link to="/bandeja" class="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-700/50 transition-colors text-sm text-slate-300 hover:text-white">
              <svg class="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 012.012 1.244l.256.512a2.25 2.25 0 002.013 1.244h3.218a2.25 2.25 0 002.013-1.244l.256-.512a2.25 2.25 0 012.013-1.244h3.859m-19.5.338V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 00-2.15-1.588H6.911a2.25 2.25 0 00-2.15 1.588L2.35 13.177a2.25 2.25 0 00-.1.661z" /></svg>
              Ver bandeja de tickets
            </router-link>
            <router-link to="/expedientes" class="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-700/50 transition-colors text-sm text-slate-300 hover:text-white">
              <svg class="w-4 h-4 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932H19.05a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776" /></svg>
              Gestionar expedientes
            </router-link>
            <router-link to="/docentes" class="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-700/50 transition-colors text-sm text-slate-300 hover:text-white">
              <svg class="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" /></svg>
              Docentes y carga laboral
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api.js'

const cargando = ref(true)
const datos = ref(null)
const distribucion = ref([])

const fechaHoy = new Date().toLocaleDateString('es-PE', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })

const maxDistribucion = computed(() => Math.max(...distribucion.value.map(d => d.total), 1))

const kpis = computed(() => [
  {
    label: 'Tickets Sincronizados',
    valor: datos.value?.tickets_sincronizados ?? 0,
    color: 'text-indigo-400',
    bgIcon: 'bg-indigo-500/20',
    sub: 'Total recibidos del bot',
    icon: `<svg class="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 012.012 1.244l.256.512a2.25 2.25 0 002.013 1.244h3.218a2.25 2.25 0 002.013-1.244l.256-.512a2.25 2.25 0 012.013-1.244h3.859m-19.5.338V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 00-2.15-1.588H6.911a2.25 2.25 0 00-2.15 1.588L2.35 13.177a2.25 2.25 0 00-.1.661z" /></svg>`
  },
  {
    label: 'Total Expedientes',
    valor: datos.value?.total_expedientes ?? 0,
    color: 'text-violet-400',
    bgIcon: 'bg-violet-500/20',
    sub: 'En todos los estados',
    icon: `<svg class="w-5 h-5 text-violet-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932H19.05a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776" /></svg>`
  },
  {
    label: 'En Proceso',
    valor: datos.value?.en_proceso ?? 0,
    color: 'text-blue-400',
    bgIcon: 'bg-blue-500/20',
    sub: 'Avanzando en el flujo',
    icon: `<svg class="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" /></svg>`
  },
  {
    label: 'Graduados',
    valor: datos.value?.graduados ?? 0,
    color: 'text-emerald-400',
    bgIcon: 'bg-emerald-500/20',
    sub: 'Proceso completado',
    icon: `<svg class="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" /></svg>`
  },
])

onMounted(async () => {
  try {
    const res = await api.get('/dashboard/kpis')
    datos.value = res.data
    distribucion.value = res.data.distribucion_pasos || []
  } catch (e) {
    console.error('Error cargando KPIs:', e)
  } finally {
    cargando.value = false
  }
})
</script>
