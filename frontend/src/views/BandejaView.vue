<template>
  <div class="p-6 space-y-5 animate-fade-in">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-white">Bandeja de Tickets</h2>
        <p class="text-slate-400 text-sm mt-0.5">Tickets recibidos del bot — pendientes de clasificar</p>
      </div>
      <div class="flex items-center gap-3">
        <!-- Toggle: solo sin clasificar -->
        <label class="flex items-center gap-2 cursor-pointer select-none">
          <div
            @click="soloPendientes = !soloPendientes; cargar()"
            :class="['relative w-10 h-5 rounded-full transition-colors duration-200', soloPendientes ? 'bg-indigo-600' : 'bg-slate-700']"
          >
            <span :class="['absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200', soloPendientes ? 'translate-x-5' : 'translate-x-0.5']"></span>
          </div>
          <span class="text-sm text-slate-300">Solo pendientes</span>
        </label>
        <button @click="cargar" class="btn-ghost btn-sm">
          <svg class="w-4 h-4" :class="cargando ? 'animate-spin' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
          Actualizar
        </button>
      </div>
    </div>

    <!-- Buscador -->
    <div class="relative">
      <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803a7.5 7.5 0 0010.607 10.607z" />
      </svg>
      <input v-model="busqueda" class="input-field pl-9" placeholder="Buscar por número de ticket, asunto..." />
    </div>

    <!-- Tabla de tickets -->
    <div class="card p-0 overflow-hidden">
      <!-- Skeleton carga -->
      <div v-if="cargando" class="p-4 space-y-3">
        <div v-for="i in 8" :key="i" class="h-14 bg-slate-700/30 rounded-lg animate-pulse"></div>
      </div>

      <!-- Tabla -->
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Nº Ticket</th>
            <th>Fecha</th>
            <th class="hidden md:table-cell">Asunto</th>
            <th>Estado Bot</th>
            <th class="hidden lg:table-cell">Adjuntos</th>
            <th>Expediente</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="ticketsFiltrados.length === 0">
            <td colspan="7" class="text-center py-12 text-slate-500">
              <svg class="w-10 h-10 mx-auto mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 012.012 1.244l.256.512a2.25 2.25 0 002.013 1.244h3.218a2.25 2.25 0 002.013-1.244l.256-.512a2.25 2.25 0 012.013-1.244h3.859m-19.5.338V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 00-2.15-1.588H6.911a2.25 2.25 0 00-2.15 1.588L2.35 13.177a2.25 2.25 0 00-.1.661z" />
              </svg>
              No hay tickets que mostrar
            </td>
          </tr>

          <tr v-for="t in ticketsFiltrados" :key="t.ticket_id" class="cursor-pointer" @click="$router.push(`/bandeja/${t.ticket_id}`)">
            <td>
              <span class="font-mono font-bold text-indigo-400">{{ t.numero_visual }}</span>
            </td>
            <td class="text-slate-400 text-xs whitespace-nowrap">{{ formatFecha(t.fecha) }}</td>
            <td class="hidden md:table-cell max-w-xs">
              <p class="truncate-2 text-slate-200 text-sm">{{ t.asunto }}</p>
            </td>
            <td>
              <span :class="badgeEstado(t.estado)">
                <span v-if="t.estado === 'Nuevo'" class="w-1.5 h-1.5 bg-current rounded-full animate-pulse-dot"></span>
                {{ t.estado }}
              </span>
            </td>
            <td class="hidden lg:table-cell">
              <span class="text-slate-400 text-xs">
                <svg class="w-4 h-4 inline mr-1 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
                </svg>
                {{ t.adjuntos.length }} archivo{{ t.adjuntos.length !== 1 ? 's' : '' }}
              </span>
            </td>
            <td>
              <span v-if="t.id_expediente" class="badge-proceso">
                Exp. #{{ t.id_expediente }}
              </span>
              <span v-else class="badge-nuevo">
                Sin vincular
              </span>
            </td>
            <td>
              <button class="btn-ghost btn-sm" @click.stop="$router.push(`/bandeja/${t.ticket_id}`)">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Total -->
    <p class="text-xs text-slate-500 text-right">
      Mostrando {{ ticketsFiltrados.length }} de {{ tickets.length }} tickets
    </p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api.js'

const tickets = ref([])
const cargando = ref(true)
const busqueda = ref('')
const soloPendientes = ref(false)

const ticketsFiltrados = computed(() => {
  let lista = tickets.value
  if (busqueda.value.trim()) {
    const q = busqueda.value.toLowerCase()
    lista = lista.filter(t =>
      t.numero_visual.toLowerCase().includes(q) ||
      (t.asunto || '').toLowerCase().includes(q)
    )
  }
  return lista
})

function badgeEstado(estado) {
  const map = {
    'Nuevo': 'badge-nuevo',
    'Adjuntos_Descargados': 'badge-proceso',
    'Procesado': 'badge-graduado',
    'Error': 'badge-error',
  }
  return map[estado] || 'badge'
}

function formatFecha(fecha) {
  return new Date(fecha).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: '2-digit' })
}

async function cargar() {
  cargando.value = true
  try {
    const params = soloPendientes.value ? { solo_sin_clasificar: true } : {}
    const res = await api.get('/tickets', { params })
    tickets.value = res.data.data
  } catch (e) {
    console.error(e)
  } finally {
    cargando.value = false
  }
}

onMounted(cargar)
</script>
