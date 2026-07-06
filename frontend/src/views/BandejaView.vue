<template>
  <div class="p-6 space-y-5 animate-fade-in">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-white">Bandeja de Tickets</h2>
        <p class="text-slate-400 text-sm mt-0.5">Tickets recibidos del bot</p>
      </div>
      <div class="flex items-center gap-3">
        <label class="flex items-center gap-2 cursor-pointer select-none">
          <div
            @click="soloPendientes = !soloPendientes; pagina = 1; cargar()"
            :class="['relative w-10 h-5 rounded-full transition-colors duration-200', soloPendientes ? 'bg-indigo-600' : 'bg-slate-700']"
          >
            <span :class="['absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200', soloPendientes ? 'translate-x-5' : 'translate-x-0.5']"></span>
          </div>
          <span class="text-sm text-slate-300">Solo pendientes</span>
        </label>
        <button @click="cargar" class="btn-ghost btn-sm">
          <svg class="w-4 h-4" :class="cargando ? 'animate-spin' : ''" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
          Actualizar
        </button>
      </div>
    </div>

    <div class="flex flex-col md:flex-row gap-3">
      <div class="relative flex-1">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803a7.5 7.5 0 0010.607 10.607z" />
        </svg>
        <input v-model="busqueda" @keyup.enter="buscar" class="input-field pl-9" placeholder="Buscar ticket, asunto, alumno, c&oacute;digo..." />
      </div>
      <button @click="buscar" class="btn-primary btn-sm justify-center">Buscar</button>
      <select v-model.number="porPagina" @change="pagina = 1; cargar()" class="input-field md:w-28">
        <option :value="10">10</option>
        <option :value="25">25</option>
        <option :value="50">50</option>
        <option :value="100">100</option>
      </select>
    </div>

    <div class="card p-0 overflow-hidden">
      <div v-if="cargando" class="p-4 space-y-3">
        <div v-for="i in 8" :key="i" class="h-14 bg-slate-700/30 rounded-lg animate-pulse"></div>
      </div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Nro. Ticket</th>
            <th>Fecha</th>
            <th class="hidden md:table-cell">Asunto</th>
            <th class="hidden xl:table-cell">Estudiante osTicket</th>
            <th>Estado Bot</th>
            <th class="hidden lg:table-cell">Adjuntos</th>
            <th>Expediente</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="tickets.length === 0">
            <td colspan="8" class="text-center py-12 text-slate-500">
              <svg class="w-10 h-10 mx-auto mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 012.012 1.244l.256.512a2.25 2.25 0 002.013 1.244h3.218a2.25 2.25 0 002.013-1.244l.256-.512a2.25 2.25 0 012.013-1.244h3.859" />
              </svg>
              No hay tickets que mostrar
            </td>
          </tr>

          <tr v-for="t in tickets" :key="t.uuid || t.ticket_id" class="cursor-pointer" @click="abrirTicket(t)">
            <td>
              <span class="font-mono font-bold text-indigo-400">{{ t.numero_visual }}</span>
            </td>
            <td class="text-slate-400 text-xs whitespace-nowrap">{{ formatFecha(t.fecha) }}</td>
            <td class="hidden md:table-cell max-w-xs">
              <p class="truncate-2 text-slate-200 text-sm">{{ t.asunto }}</p>
            </td>
            <td class="hidden xl:table-cell max-w-xs">
              <p class="text-xs text-white truncate">{{ t.nombre_estudiante_osticket || 'Sin nombre' }}</p>
              <p class="text-[10px] text-slate-500 truncate">{{ t.codigo_alumno_osticket || t.email_estudiante || 'Sin c&oacute;digo' }}</p>
            </td>
            <td>
              <span :class="badgeEstado(t.estado)">{{ t.estado }}</span>
            </td>
            <td class="hidden lg:table-cell">
              <span class="text-slate-400 text-xs">{{ t.adjuntos.length }} archivo{{ t.adjuntos.length !== 1 ? 's' : '' }}</span>
            </td>
            <td>
              <span v-if="t.id_expediente" class="badge-proceso">Exp. #{{ t.id_expediente }}</span>
              <span v-else class="badge-nuevo">Sin vincular</span>
            </td>
            <td>
              <button class="btn-ghost btn-sm" @click.stop="abrirTicket(t)">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex items-center justify-between gap-3 text-xs text-slate-500">
      <span>Mostrando {{ tickets.length }} de {{ total }} tickets</span>
      <div class="flex items-center gap-2">
        <button @click="cambiarPagina(pagina - 1)" :disabled="pagina <= 1" class="btn-ghost btn-sm">Anterior</button>
        <span class="text-slate-300">P&aacute;gina {{ pagina }} / {{ totalPaginas }}</span>
        <button @click="cambiarPagina(pagina + 1)" :disabled="pagina >= totalPaginas" class="btn-ghost btn-sm">Siguiente</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api.js'

const router = useRouter()
const tickets = ref([])
const cargando = ref(true)
const busqueda = ref('')
const soloPendientes = ref(false)
const pagina = ref(1)
const porPagina = ref(25)
const total = ref(0)
const totalPaginas = ref(1)

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

function formatFecha(fecha) {
  if (!fecha) return ''
  return new Date(fecha).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: '2-digit' })
}

function abrirTicket(ticket) {
  router.push(`/bandeja/${ticket.uuid || ticket.ticket_id}`)
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
    const params = {
      page: pagina.value,
      per_page: porPagina.value,
      solo_sin_clasificar: soloPendientes.value,
    }
    if (busqueda.value.trim()) params.busqueda = busqueda.value.trim()
    const res = await api.get('/tickets', { params })
    tickets.value = res.data.data
    total.value = res.data.total || res.data.total_tickets || 0
    totalPaginas.value = res.data.total_pages || 1
  } catch (e) {
    console.error(e)
  } finally {
    cargando.value = false
  }
}

onMounted(cargar)
</script>
