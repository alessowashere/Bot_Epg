<template>
  <div class="page-shell animate-fade-in">
    <header class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p class="text-xs font-semibold uppercase text-sky-700 dark:text-cyan-300">Consulta y trazabilidad</p>
        <h2 class="page-title">Archivo de tickets</h2>
        <p class="page-subtitle">Aqui se busca todo lo sincronizado, incluidos historicos y casos cerrados. Para decidir y tramitar un ingreso usa la Mesa de tickets.</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <router-link to="/tickets-pendientes" class="btn-outline">
          <i class="pi pi-list-check"></i>
          Ir a Mesa de tickets
        </router-link>
        <button type="button" class="btn-outline" :disabled="cargando" @click="cargar">
          <i :class="cargando ? 'pi-spin pi-spinner' : 'pi-refresh'" class="pi"></i>
          Actualizar
        </button>
      </div>
    </header>

    <section class="filter-bar space-y-3" aria-label="Filtros de tickets">
      <div class="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(280px,1fr)_210px_170px_170px_170px_auto]">
        <label class="relative block">
          <span class="sr-only">Busqueda general</span>
          <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400"></i>
          <input
            v-model="filtros.busqueda"
            class="input-field pl-9"
            placeholder="Ticket, persona, tesis, resolucion, docente, adjunto..."
            @keyup.enter="aplicarFiltros"
          />
        </label>
        <select v-model="filtros.situacion" class="input-field" @change="aplicarFiltros">
          <option value="">Todas las situaciones</option>
          <option value="requiere_accion">Requiere accion</option>
          <option value="por_clasificar">Decidir y enviar</option>
          <option value="requiere_resolucion">Crear expediente inicial</option>
          <option value="en_tramite_resolucion">En Secretaría / Dirección</option>
          <option value="sin_expediente">Sin expediente</option>
          <option value="posible_expediente">Con datos para buscar</option>
          <option value="pendiente_adjuntos">Procesando adjuntos</option>
          <option value="error_extraccion">Error tecnico</option>
          <option value="fuera_proceso">Fuera del proceso</option>
          <option value="atendido_con_resolucion">Resolucion confirmada</option>
        </select>
        <select v-model="filtros.estado_operativo" class="input-field" @change="aplicarFiltros">
          <option value="">Activos (trabajo diario)</option>
          <option value="Revision_historica">Revisión histórica</option>
          <option value="Archivado_historico">Archivados históricos</option>
          <option value="Fuera_proceso">Fuera del proceso</option>
          <option value="todos">Todos los destinos</option>
        </select>
        <select v-model="filtros.vinculado" class="input-field" @change="aplicarFiltros">
          <option value="">Con y sin expediente</option>
          <option value="si">Vinculados</option>
          <option value="no">Sin vincular</option>
        </select>
        <select v-model="filtros.adjuntos" class="input-field" @change="aplicarFiltros">
          <option value="">Con y sin adjuntos</option>
          <option value="con">Con adjuntos</option>
          <option value="sin">Sin adjuntos</option>
        </select>
        <button type="button" class="btn-primary justify-center" @click="aplicarFiltros">
          <i class="pi pi-filter"></i>
          Filtrar
        </button>
      </div>

      <details class="group rounded-md border border-slate-200 dark:border-slate-700" :open="hayFiltroAvanzado">
        <summary class="flex cursor-pointer list-none items-center justify-between gap-3 px-3 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300">
          <span><i class="pi pi-sliders-h mr-2"></i>Filtros avanzados</span>
          <i class="pi pi-chevron-down text-[10px] transition-transform group-open:rotate-180"></i>
        </summary>
        <div class="grid grid-cols-1 gap-3 border-t border-slate-200 p-3 sm:grid-cols-2 xl:grid-cols-4 dark:border-slate-700">
          <input v-model="filtros.estudiante" class="input-field" placeholder="Nombre del estudiante" @keyup.enter="aplicarFiltros" />
          <input v-model="filtros.codigo" class="input-field" placeholder="Codigo del estudiante" @keyup.enter="aplicarFiltros" />
          <input v-model="filtros.asunto" class="input-field" placeholder="Texto del asunto" @keyup.enter="aplicarFiltros" />
          <select v-model="filtros.estado" class="input-field" @change="aplicarFiltros">
            <option value="">Todos los estados tecnicos</option>
            <option value="Pendiente_Descarga">Pendiente de descarga</option>
            <option value="Archivos_Descargados">Archivos descargados</option>
            <option value="Datos_Extraidos">Datos extraidos</option>
            <option value="Clasificado">Vinculado</option>
            <option value="Notificado">Cerrado local</option>
            <option value="Error">Error</option>
          </select>
          <select v-model="filtros.decision" class="input-field" @change="aplicarFiltros">
            <option value="">Todas las decisiones</option>
            <option value="requiere_resolucion">Requiere resolucion</option>
            <option value="resolucion_notificada">Resolucion notificada</option>
            <option value="resolucion_cargada">Resolución cargada</option>
            <option value="no_corresponde">No corresponde</option>
            <option value="transferir">Transferir</option>
            <option value="cerrar_interno">Cerrar interno</option>
            <option value="reabrir">Reabierto</option>
          </select>
          <select v-model="filtros.paso_sugerido" class="input-field" @change="aplicarFiltros">
            <option value="">Todos los pasos sugeridos</option>
            <option v-for="numero in 7" :key="numero" :value="numero">Paso {{ numero }}</option>
          </select>
          <label>
            <span class="input-label">Desde</span>
            <input v-model="filtros.fecha_desde" type="date" class="input-field" @change="aplicarFiltros" />
          </label>
          <label>
            <span class="input-label">Hasta</span>
            <input v-model="filtros.fecha_hasta" type="date" class="input-field" @change="aplicarFiltros" />
          </label>
        </div>
      </details>

      <div class="flex flex-col gap-3 border-t border-slate-100 pt-3 sm:flex-row sm:items-center sm:justify-between dark:border-slate-800">
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-xs text-slate-500">Vista</span>
          <div class="inline-flex rounded-md border border-slate-200 p-0.5 dark:border-slate-700">
            <button type="button" :class="densidad === 'compacta' ? 'brand-selection' : 'text-slate-500'" class="rounded px-2.5 py-1 text-xs" @click="densidad = 'compacta'">Compacta</button>
            <button type="button" :class="densidad === 'comoda' ? 'brand-selection' : 'text-slate-500'" class="rounded px-2.5 py-1 text-xs" @click="densidad = 'comoda'">Comoda</button>
          </div>
          <button v-if="filtrosActivos" type="button" class="btn-ghost btn-sm" @click="limpiarFiltros">
            <i class="pi pi-times"></i>
            Limpiar
          </button>
        </div>
        <div class="flex items-center gap-2">
          <select v-model="orden" class="input-field w-44" @change="buscarLocal">
            <option value="fecha:desc">Mas recientes</option>
            <option value="fecha:asc">Mas antiguos</option>
            <option value="estudiante:asc">Estudiante A-Z</option>
            <option value="ticket:desc">Numero de ticket</option>
            <option value="estado:asc">Estado tecnico</option>
            <option value="adjuntos:desc">Mas adjuntos</option>
          </select>
          <select v-model.number="porPagina" class="input-field w-24" @change="buscarLocal">
            <option :value="10">10</option>
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
        </div>
      </div>
    </section>

    <div v-if="error" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
      <i class="pi pi-exclamation-circle mr-2"></i>{{ error }}
    </div>

    <section class="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div class="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <p class="text-xs text-slate-500"><strong class="text-slate-900 dark:text-white">{{ total }}</strong> tickets encontrados</p>
        <p class="text-xs text-slate-500">Pagina {{ pagina }} de {{ totalPaginas }}</p>
      </div>

      <div v-if="cargando" class="space-y-2 p-4">
        <div v-for="numero in 8" :key="numero" class="h-14 animate-pulse rounded bg-slate-100 dark:bg-slate-800"></div>
      </div>

      <div v-else class="overflow-x-auto">
        <table :class="densidad === 'compacta' ? 'table-compact' : ''" class="data-table min-w-[1050px]">
          <thead>
            <tr>
              <th>Ticket / fecha</th>
              <th>Estudiante</th>
              <th>Asunto</th>
              <th>Situacion</th>
              <th>Estado tecnico</th>
              <th>Adjuntos</th>
              <th>Expediente</th>
              <th><span class="sr-only">Abrir</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="tickets.length === 0">
              <td colspan="8" class="py-16 text-center">
                <i class="pi pi-inbox mb-3 block text-3xl text-slate-300"></i>
                <p class="text-sm font-semibold text-slate-700 dark:text-slate-200">No hay tickets con estos filtros</p>
                <button type="button" class="btn-ghost btn-sm mt-2" @click="limpiarFiltros">Limpiar filtros</button>
              </td>
            </tr>
            <tr v-for="ticket in tickets" :key="ticket.uuid || ticket.ticket_id" class="cursor-pointer" @click="abrirTicket(ticket)">
              <td class="whitespace-nowrap">
                <p class="font-mono text-sm font-bold text-sky-700 dark:text-cyan-300">#{{ ticket.numero_visual }}</p>
                <p class="mt-0.5 text-[11px] text-slate-500">{{ formatFecha(ticket.fecha) }}</p>
              </td>
              <td class="max-w-56">
                <p class="truncate text-sm font-semibold text-slate-900 dark:text-white">{{ ticket.nombre_estudiante_osticket || 'Sin nombre' }}</p>
                <p class="mt-0.5 truncate font-mono text-[11px] text-slate-500">{{ ticket.codigo_alumno_osticket || ticket.email_estudiante || 'Sin codigo' }}</p>
              </td>
              <td class="max-w-80">
                <p class="truncate-2 text-sm text-slate-700 dark:text-slate-200" :title="ticket.asunto">{{ ticket.asunto || 'Sin asunto' }}</p>
                <p v-if="ticket.paso_sugerido?.id_paso" class="mt-1 text-[11px] text-sky-700 dark:text-cyan-300">Paso sugerido {{ ticket.paso_sugerido.id_paso }}</p>
              </td>
              <td>
                <span :class="badgeSituacion(ticket.situacion_operativa)">{{ textoSituacion(ticket.situacion_operativa) }}</span>
                <p v-if="ticket.decision_actual?.decision" class="mt-1 max-w-40 truncate text-[10px] text-slate-500">{{ textoDecision(ticket.decision_actual.decision) }}</p>
              </td>
              <td><span :class="badgeEstado(ticket.estado)">{{ textoEstado(ticket.estado) }}</span></td>
              <td class="text-center text-xs text-slate-600 dark:text-slate-300">{{ ticket.adjuntos_count ?? ticket.adjuntos?.length ?? 0 }}</td>
              <td>
                <span v-if="ticket.id_expediente" class="badge-proceso">Exp. {{ ticket.id_expediente }}</span>
                <span v-else class="text-xs text-slate-500">Sin vincular</span>
              </td>
              <td>
                <button type="button" class="icon-btn" title="Abrir ticket" aria-label="Abrir ticket" @click.stop="abrirTicket(ticket)">
                  <i class="pi pi-chevron-right text-xs"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <nav class="flex items-center justify-between gap-3" aria-label="Paginacion">
      <button type="button" class="btn-outline btn-sm" :disabled="pagina <= 1 || cargando" @click="cambiarPagina(pagina - 1)">
        <i class="pi pi-chevron-left"></i>Anterior
      </button>
      <span class="text-xs text-slate-500">Mostrando {{ tickets.length }} de {{ total }}</span>
      <button type="button" class="btn-outline btn-sm" :disabled="pagina >= totalPaginas || cargando" @click="cambiarPagina(pagina + 1)">
        Siguiente<i class="pi pi-chevron-right"></i>
      </button>
    </nav>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api.js'

const route = useRoute()
const router = useRouter()
const tickets = ref([])
const cargando = ref(true)
const error = ref('')
const pagina = ref(1)
const porPagina = ref(25)
const total = ref(0)
const totalPaginas = ref(1)
const orden = ref('fecha:desc')
const densidad = ref(localStorage.getItem('epg_densidad_tickets') || 'compacta')
const filtros = ref(filtrosVacios())

function filtrosVacios() {
  return {
    busqueda: '', situacion: '', estado_operativo: '', vinculado: '', adjuntos: '', estado: '', decision: '',
    paso_sugerido: '', fecha_desde: '', fecha_hasta: '', antiguedad_dias: '', estudiante: '', codigo: '', asunto: '',
  }
}

const filtrosActivos = computed(() => Object.values(filtros.value).some(Boolean))
const hayFiltroAvanzado = computed(() => [
  filtros.value.estado, filtros.value.decision, filtros.value.paso_sugerido,
  filtros.value.fecha_desde, filtros.value.fecha_hasta, filtros.value.estudiante,
  filtros.value.codigo, filtros.value.asunto,
].some(Boolean))

watch(densidad, valor => localStorage.setItem('epg_densidad_tickets', valor))

function hidratarDesdeRuta(query) {
  const nuevos = filtrosVacios()
  for (const clave of Object.keys(nuevos)) nuevos[clave] = query[clave] || ''
  if (query.fecha === 'hoy') {
    const hoy = new Date().toISOString().slice(0, 10)
    nuevos.fecha_desde = hoy
    nuevos.fecha_hasta = hoy
  }
  filtros.value = nuevos
  if (query.orden) orden.value = query.orden
}

function queryActual() {
  const query = {}
  for (const [clave, valor] of Object.entries(filtros.value)) {
    if (valor !== '' && valor !== null) query[clave] = String(valor)
  }
  if (orden.value !== 'fecha:desc') query.orden = orden.value
  return query
}

function aplicarFiltros() {
  pagina.value = 1
  const query = queryActual()
  if (JSON.stringify(query) === JSON.stringify(route.query)) {
    cargar()
    return
  }
  router.replace({ path: '/bandeja', query })
}

function buscarLocal() {
  pagina.value = 1
  aplicarFiltros()
}

function limpiarFiltros() {
  filtros.value = filtrosVacios()
  orden.value = 'fecha:desc'
  pagina.value = 1
  router.replace({ path: '/bandeja' })
}

function cambiarPagina(nuevaPagina) {
  if (nuevaPagina < 1 || nuevaPagina > totalPaginas.value) return
  pagina.value = nuevaPagina
  cargar()
}

function abrirTicket(ticket) {
  router.push(`/bandeja/${ticket.uuid || ticket.ticket_id}`)
}

function textoSituacion(valor) {
  return {
    requiere_resolucion: 'Crear expediente', en_tramite_resolucion: 'En trámite institucional', por_clasificar: 'Decidir y enviar', falta_resolucion: 'Decidir y enviar',
    sin_expediente: 'Sin expediente', posible_expediente: 'Sin expediente',
    pendiente_adjuntos: 'Procesando adjuntos', error_extraccion: 'Revisar error',
    fuera_proceso: 'Fuera del proceso', pendiente_transferencia: 'Transferir',
    atendido_con_resolucion: 'Resolucion confirmada', atendido: 'Atendido',
  }[valor] || 'Revision humana'
}

function badgeSituacion(valor) {
  if (valor === 'atendido_con_resolucion' || valor === 'atendido') return 'badge-graduado'
  if (valor === 'error_extraccion') return 'badge-error'
  if (valor === 'en_tramite_resolucion') return 'badge-proceso'
  if (['falta_resolucion', 'por_clasificar', 'requiere_resolucion'].includes(valor)) return 'badge-observado'
  if (valor === 'fuera_proceso') return 'badge-caduco'
  return 'badge-nuevo'
}

function textoEstado(valor) {
  return {
    Pendiente_Descarga: 'Pendiente descarga', Archivos_Descargados: 'Archivos listos',
    Datos_Extraidos: 'Datos extraidos', Clasificado: 'Vinculado', Notificado: 'Cerrado local', Error: 'Error',
  }[valor] || valor
}

function badgeEstado(valor) {
  return {
    Pendiente_Descarga: 'badge-nuevo', Archivos_Descargados: 'badge-proceso',
    Datos_Extraidos: 'badge-observado', Clasificado: 'badge-proceso',
    Notificado: 'badge-graduado', Error: 'badge-error',
  }[valor] || 'badge'
}

function textoDecision(valor) {
  return {
    requiere_resolucion: 'Decision: requiere resolucion', resolucion_notificada: 'Decision: resolucion notificada', resolucion_cargada: 'Decisión: resolución cargada',
    no_corresponde: 'Decision: no corresponde', transferir: 'Decision: transferir',
    cerrar_interno: 'Decision: cierre interno', reabrir: 'Decision: reabierto',
  }[valor] || valor
}

function formatFecha(fecha) {
  if (!fecha) return 'Sin fecha'
  return new Date(fecha.replace(' ', 'T')).toLocaleString('es-PE', {
    day: '2-digit', month: 'short', year: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    const params = { page: pagina.value, per_page: porPagina.value }
    const [sort_by, sort_dir] = orden.value.split(':')
    params.sort_by = sort_by
    params.sort_dir = sort_dir
    for (const [clave, valor] of Object.entries(filtros.value)) {
      if (valor !== '' && valor !== null) params[clave] = valor
    }
    const res = await api.get('/tickets', { params })
    tickets.value = res.data.data || []
    total.value = res.data.total || 0
    totalPaginas.value = res.data.total_pages || 1
  } catch (err) {
    error.value = err.response?.data?.detail || 'No se pudo cargar la bandeja.'
  } finally {
    cargando.value = false
  }
}

watch(() => route.query, query => {
  hidratarDesdeRuta(query)
  pagina.value = 1
  cargar()
})

onMounted(() => {
  hidratarDesdeRuta(route.query)
  cargar()
})
</script>
