<template>
  <div class="page-shell animate-fade-in">
    <header class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p class="text-xs font-semibold uppercase text-sky-700 dark:text-cyan-300">Trabajo diario de Tramitacion</p>
        <h2 class="page-title">Mesa de tickets</h2>
        <p class="page-subtitle">Esta es la pantalla para decidir el destino de cada ingreso y enviarlo al siguiente rol. Solo muestra trabajo que requiere accion.</p>
      </div>
      <router-link to="/bandeja" class="btn-outline self-start sm:self-auto">
        <i class="pi pi-inbox"></i>
        Buscar en el archivo
      </router-link>
    </header>

    <nav class="overflow-x-auto border-b border-slate-200 dark:border-slate-700" aria-label="Colas de revision">
      <div class="flex min-w-max gap-1">
        <button
          v-for="item in colas"
          :key="item.clave"
          type="button"
          :class="cola === item.clave ? 'border-[#132e66] text-[#132e66] dark:border-cyan-300 dark:text-cyan-300' : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-white'"
          class="flex min-h-11 items-center gap-2 border-b-2 px-3 text-xs font-semibold transition-colors"
          @click="seleccionarCola(item.clave)"
        >
          <i :class="item.icon" class="pi"></i>
          {{ item.label }}
          <span class="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-700 dark:bg-slate-800 dark:text-slate-300">{{ conteoCola(item.clave) }}</span>
        </button>
      </div>
    </nav>

    <div class="grid gap-3 rounded-lg border border-sky-200 bg-sky-50 p-4 text-xs leading-5 text-sky-950 dark:border-cyan-500/25 dark:bg-cyan-500/10 dark:text-cyan-50 md:grid-cols-3">
      <p><strong>Decidir y enviar:</strong> ya tiene expediente; decide si corresponde y, al requerir resolución, se envía a Secretaría.</p>
      <p><strong>Sin expediente:</strong> el sistema no encontró uno. Revisa el ticket para vincular uno existente o crear el primero.</p>
      <p><strong>Procesando adjuntos:</strong> no requiere acción humana salvo que permanezca en error; el sincronizador descarga y lee los archivos.</p>
    </div>

    <section class="filter-bar space-y-3">
      <div class="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(280px,1fr)_170px_170px_auto]">
        <label class="relative block">
          <span class="sr-only">Buscar en la cola</span>
          <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400"></i>
          <input v-model="filtros.busqueda" class="input-field pl-9" placeholder="Ticket, persona, tesis, resolución, docente o adjunto" @keyup.enter="buscar" />
        </label>
        <select v-model="filtros.vinculado" class="input-field" @change="buscar"><option value="">Con y sin expediente</option><option value="si">Vinculados</option><option value="no">Sin vincular</option></select>
        <select v-model="filtros.adjuntos" class="input-field" @change="buscar">
          <option value="">Con y sin adjuntos</option>
          <option value="con">Con adjuntos</option>
          <option value="sin">Sin adjuntos</option>
        </select>
        <button type="button" class="btn-primary justify-center" @click="buscar"><i class="pi pi-filter"></i>Filtrar</button>
      </div>
      <details class="group rounded-md border border-slate-200 dark:border-slate-700">
        <summary class="flex cursor-pointer list-none items-center justify-between gap-3 px-3 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300"><span><i class="pi pi-sliders-h mr-2"></i>Filtros avanzados</span><i class="pi pi-chevron-down text-[10px] transition-transform group-open:rotate-180"></i></summary>
        <div class="grid grid-cols-1 gap-3 border-t border-slate-200 p-3 sm:grid-cols-2 xl:grid-cols-4 dark:border-slate-700">
          <input v-model="filtros.estudiante" class="input-field" placeholder="Nombre del estudiante" @keyup.enter="buscar" />
          <input v-model="filtros.codigo" class="input-field" placeholder="Código del estudiante" @keyup.enter="buscar" />
          <input v-model="filtros.asunto" class="input-field" placeholder="Texto del asunto" @keyup.enter="buscar" />
          <select v-model="filtros.estado" class="input-field" @change="buscar"><option value="">Todos los estados técnicos</option><option value="Pendiente_Descarga">Pendiente de descarga</option><option value="Archivos_Descargados">Archivos descargados</option><option value="Datos_Extraidos">Datos extraídos</option><option value="Clasificado">Vinculado</option><option value="Notificado">Cerrado local</option><option value="Error">Error</option></select>
          <select v-model="filtros.decision" class="input-field" @change="buscar"><option value="">Todas las decisiones</option><option value="requiere_resolucion">Requiere resolución</option><option value="resolucion_notificada">Resolución notificada</option><option value="no_corresponde">No corresponde</option><option value="transferir">Transferir</option><option value="cerrar_interno">Cerrar interno</option><option value="reabrir">Reabierto</option></select>
          <select v-model="filtros.paso_sugerido" class="input-field" @change="buscar"><option value="">Todos los pasos sugeridos</option><option v-for="paso in 7" :key="paso" :value="paso">Paso {{ paso }}</option></select>
          <label><span class="input-label">Desde</span><input v-model="filtros.fecha_desde" type="date" class="input-field" @change="buscar" /></label>
          <label><span class="input-label">Hasta</span><input v-model="filtros.fecha_hasta" type="date" class="input-field" @change="buscar" /></label>
        </div>
      </details>
      <div class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-3 dark:border-slate-800">
        <button v-if="filtrosActivos" type="button" class="btn-ghost btn-sm" @click="limpiarFiltros"><i class="pi pi-times"></i>Limpiar filtros</button><span v-else class="text-xs text-slate-500">Filtros de la misma potencia que la Bandeja general.</span>
        <div class="flex items-center gap-2"><select v-model="orden" class="input-field w-44" @change="buscar"><option value="fecha:desc">Más recientes</option><option value="fecha:asc">Más antiguos</option><option value="estudiante:asc">Estudiante A-Z</option><option value="ticket:desc">Número de ticket</option><option value="estado:asc">Estado técnico</option><option value="adjuntos:desc">Más adjuntos</option></select><select v-model.number="porPagina" class="input-field w-24" @change="buscar"><option :value="10">10</option><option :value="25">25</option><option :value="50">50</option><option :value="100">100</option></select></div>
      </div>
    </section>

    <div v-if="error" class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
      <i class="pi pi-exclamation-circle mr-2"></i>{{ error }}
    </div>

    <section class="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div class="flex flex-col gap-1 border-b border-slate-200 px-5 py-4 sm:flex-row sm:items-center sm:justify-between dark:border-slate-800">
        <div>
          <h3 class="section-title">{{ colaActiva.label }}</h3>
          <p class="mt-0.5 text-xs text-slate-500">{{ colaActiva.detalle }}</p>
        </div>
        <span class="text-xs text-slate-500">{{ total }} ticket(s)</span>
      </div>

      <div v-if="cargando" class="space-y-2 p-4">
        <div v-for="numero in 9" :key="numero" class="h-14 animate-pulse rounded bg-slate-100 dark:bg-slate-800"></div>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="data-table table-compact min-w-[960px]">
          <thead>
            <tr>
              <th>Ticket</th>
              <th>Estudiante</th>
              <th>Asunto</th>
              <th>Senal</th>
              <th>Adjuntos</th>
              <th>Expediente</th>
              <th><span class="sr-only">Acciones</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="tickets.length === 0">
              <td colspan="7" class="py-16 text-center">
                <i class="pi pi-check-circle mb-3 block text-3xl text-emerald-400"></i>
                <p class="text-sm font-semibold text-slate-700 dark:text-slate-200">No hay tickets en esta cola</p>
                <p class="mt-1 text-xs text-slate-500">Prueba otra cola o limpia la busqueda.</p>
              </td>
            </tr>
            <tr v-for="ticket in tickets" :key="ticket.uuid || ticket.ticket_id">
              <td class="whitespace-nowrap">
                <button type="button" class="font-mono text-sm font-bold text-sky-700 hover:underline dark:text-cyan-300" @click="abrirTicket(ticket)">#{{ ticket.numero_visual }}</button>
                <p class="text-[10px] text-slate-500">{{ formatFecha(ticket.fecha) }}</p>
              </td>
              <td class="max-w-56">
                <p class="truncate text-sm font-semibold text-slate-900 dark:text-white">{{ ticket.nombre_estudiante_osticket || 'Sin nombre' }}</p>
                <p class="truncate font-mono text-[10px] text-slate-500">{{ ticket.codigo_alumno_osticket || ticket.email_estudiante || 'Sin codigo' }}</p>
              </td>
              <td class="max-w-80"><p class="truncate-2 text-sm text-slate-700 dark:text-slate-200">{{ ticket.asunto || 'Sin asunto' }}</p></td>
              <td><span :class="badgeMotivo(ticket.situacion_operativa || ticket.motivo)">{{ textoMotivo(ticket.situacion_operativa || ticket.motivo) }}</span></td>
              <td class="text-center text-xs">{{ ticket.adjuntos_count ?? ticket.adjuntos?.length ?? 0 }}</td>
              <td>
                <span v-if="ticket.id_expediente" class="badge-proceso">Exp. {{ ticket.id_expediente }}</span>
                <span v-else class="text-xs text-slate-500">No vinculado</span>
              </td>
              <td>
                <div class="flex justify-end gap-1">
                  <button type="button" class="icon-btn" title="Registrar decision" aria-label="Registrar decision" @click="seleccionarTicket(ticket)"><i class="pi pi-pencil text-xs"></i></button>
                  <button type="button" class="icon-btn" title="Abrir detalle" aria-label="Abrir detalle" @click="abrirTicket(ticket)"><i class="pi pi-chevron-right text-xs"></i></button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <nav class="flex items-center justify-between gap-3" aria-label="Paginacion">
      <button type="button" class="btn-outline btn-sm" :disabled="pagina <= 1 || cargando" @click="cambiarPagina(pagina - 1)"><i class="pi pi-chevron-left"></i>Anterior</button>
      <span class="text-xs text-slate-500">Pagina {{ pagina }} de {{ totalPaginas }}</span>
      <button type="button" class="btn-outline btn-sm" :disabled="pagina >= totalPaginas || cargando" @click="cambiarPagina(pagina + 1)">Siguiente<i class="pi pi-chevron-right"></i></button>
    </nav>

    <div v-if="ticketSeleccionado" class="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/55 p-4" @click.self="cerrarDecision">
      <section class="w-full max-w-lg rounded-lg border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-900" role="dialog" aria-modal="true" aria-labelledby="decision-title">
        <div class="flex items-start justify-between gap-3 border-b border-slate-200 p-5 dark:border-slate-800">
          <div class="min-w-0">
            <p class="font-mono text-xs font-bold text-sky-700 dark:text-cyan-300">#{{ ticketSeleccionado.numero_visual }}</p>
            <h3 id="decision-title" class="mt-1 truncate text-base font-bold text-slate-950 dark:text-white">Registrar decision local</h3>
            <p class="mt-1 truncate text-xs text-slate-500">{{ ticketSeleccionado.asunto }}</p>
          </div>
          <button type="button" class="icon-btn" title="Cerrar" aria-label="Cerrar" @click="cerrarDecision"><i class="pi pi-times"></i></button>
        </div>
        <form class="space-y-4 p-5" @submit.prevent="guardarDecision">
          <div>
            <label class="input-label">Decision</label>
            <select v-model="formDecision.decision" class="input-field" required>
              <option value="">Seleccionar</option>
              <option value="requiere_resolucion">Requiere resolucion</option>
              <option value="no_corresponde">No corresponde al proceso</option>
              <option value="transferir">Transferir</option>
              <option value="cerrar_interno">Cerrar internamente</option>
              <option value="reabrir">Reabrir</option>
            </select>
          </div>
          <div v-if="formDecision.decision === 'transferir'">
            <label class="input-label">Destino</label>
            <input v-model="formDecision.destino" class="input-field" placeholder="Area o unidad de destino" required />
          </div>
          <div>
            <label class="input-label">Nota interna</label>
            <textarea v-model="formDecision.nota" class="input-field resize-none" rows="4" placeholder="Motivo, verificacion realizada o siguiente accion"></textarea>
          </div>
          <div class="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300">
            Esta decision solo afecta el sistema local. No cierra ni transfiere el ticket real de osTicket.
          </div>
          <p v-if="errorDecision" class="text-xs text-red-600 dark:text-red-300">{{ errorDecision }}</p>
          <div class="flex justify-end gap-2">
            <button type="button" class="btn-ghost" @click="cerrarDecision">Cancelar</button>
            <button type="submit" class="btn-primary" :disabled="guardandoDecision || !formDecision.decision">
              <i :class="guardandoDecision ? 'pi-spin pi-spinner' : 'pi-check'" class="pi"></i>
              Guardar decision
            </button>
          </div>
        </form>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import api from '../api.js'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const tickets = ref([])
const resumen = ref({ colas: {}, estados: {} })
const cargando = ref(true)
const error = ref('')
const cola = ref(route.query.cola || 'por_clasificar')
const filtros = reactive({ busqueda: '', vinculado: '', adjuntos: '', estudiante: '', codigo: '', asunto: '', estado: '', decision: '', paso_sugerido: '', fecha_desde: '', fecha_hasta: '' })
const orden = ref('fecha:desc')
const pagina = ref(1)
const porPagina = ref(25)
const total = ref(0)
const totalPaginas = ref(1)
const ticketSeleccionado = ref(null)
const guardandoDecision = ref(false)
const errorDecision = ref('')
const formDecision = ref({ decision: '', nota: '', destino: '' })

const colas = [
  { clave: 'por_clasificar', label: 'Decidir y enviar', icon: 'pi-list-check', detalle: 'El ticket ya pertenece a un expediente. Decide el destino de este ingreso.' },
  { clave: 'sin_expediente', label: 'Sin expediente', icon: 'pi-folder-open', detalle: 'No hubo coincidencia automática; puede ser un antecedente no cargado o un expediente nuevo.' },
  { clave: 'requiere_resolucion', label: 'Crear expediente', icon: 'pi-folder-plus', detalle: 'Ya se confirmó que requiere resolución; falta registrar el primer expediente para remitirlo.' },
  { clave: 'pendiente_adjuntos', label: 'Procesando adjuntos', icon: 'pi-cog', detalle: 'El sistema está descargando o leyendo archivos. No clasifiques todavía.' },
  { clave: 'error_extraccion', label: 'Revisar error', icon: 'pi-exclamation-triangle', detalle: 'La descarga o lectura falló y necesita una revisión técnica o un reintento.' },
]

const colaActiva = computed(() => colas.find(item => item.clave === cola.value) || colas[0])
const filtrosActivos = computed(() => Object.values(filtros).some(Boolean))

function conteoCola(clave) {
  return resumen.value.colas?.[clave] ?? 0
}

function seleccionarCola(clave) {
  if (clave === cola.value) return
  router.replace({ path: '/tickets-pendientes', query: { cola: clave } })
}

function buscar() {
  pagina.value = 1
  cargar()
}

function limpiarFiltros() {
  Object.keys(filtros).forEach(clave => { filtros[clave] = '' })
  orden.value = 'fecha:desc'
  buscar()
}

function cambiarPagina(nuevaPagina) {
  if (nuevaPagina < 1 || nuevaPagina > totalPaginas.value) return
  pagina.value = nuevaPagina
  cargar()
}

function abrirTicket(ticket) {
  router.push(`/bandeja/${ticket.uuid || ticket.ticket_id}`)
}

function seleccionarTicket(ticket) {
  ticketSeleccionado.value = ticket
  formDecision.value = { decision: '', nota: '', destino: '' }
  errorDecision.value = ''
}

function cerrarDecision() {
  ticketSeleccionado.value = null
  errorDecision.value = ''
}

async function guardarDecision() {
  if (!ticketSeleccionado.value || !formDecision.value.decision) return
  guardandoDecision.value = true
  errorDecision.value = ''
  try {
    await api.post(`/tickets/${ticketSeleccionado.value.uuid || ticketSeleccionado.value.ticket_id}/decision`, null, {
      params: {
        decision: formDecision.value.decision,
        nota: formDecision.value.nota || undefined,
        destino: formDecision.value.destino || undefined,
        usuario_nombre: auth.nombre,
      },
    })
    cerrarDecision()
    await cargar()
  } catch (err) {
    errorDecision.value = err.response?.data?.detail || 'No se pudo guardar la decision.'
  } finally {
    guardandoDecision.value = false
  }
}

function textoMotivo(valor) {
  return {
    requiere_resolucion: 'Crear expediente', en_tramite_resolucion: 'En trámite institucional', por_clasificar: 'Decidir y enviar', falta_resolucion: 'Decidir y enviar',
    sin_expediente: 'Sin expediente', posible_expediente: 'Sin expediente',
    pendiente_adjuntos: 'Procesando adjuntos', error_extraccion: 'Revisar error',
    fuera_proceso: 'Fuera del proceso', pendiente_transferencia: 'Transferir',
    atendido_con_resolucion: 'Resolucion confirmada',
    adjuntos_leidos_sin_coincidencia: 'Sin coincidencia',
    sin_coincidencia_con_expediente_oficial: 'Sin expediente oficial',
  }[valor] || 'Revision humana'
}

function badgeMotivo(valor) {
  if (valor === 'error_extraccion') return 'badge-error'
  if (valor === 'atendido_con_resolucion') return 'badge-graduado'
  if (valor === 'fuera_proceso') return 'badge-caduco'
  if (valor === 'en_tramite_resolucion') return 'badge-proceso'
  if (['requiere_resolucion', 'falta_resolucion', 'por_clasificar'].includes(valor)) return 'badge-observado'
  return 'badge-nuevo'
}

function formatFecha(fecha) {
  if (!fecha) return 'Sin fecha'
  return new Date(fecha.replace(' ', 'T')).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: '2-digit' })
}

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    const [sortBy, sortDir] = orden.value.split(':')
    const params = { situacion: cola.value, page: pagina.value, per_page: porPagina.value, sort_by: sortBy, sort_dir: sortDir }
    Object.entries(filtros).forEach(([clave, valor]) => { if (valor) params[clave] = valor })
    const [res, resumenRes] = await Promise.all([
      api.get('/tickets', { params }),
      api.get('/tickets/revision', { params: { cola: cola.value, page: 1, per_page: 1 } }),
    ])
    tickets.value = res.data.data || []
    resumen.value = resumenRes.data.resumen || { colas: {}, estados: {} }
    total.value = res.data.total || 0
    totalPaginas.value = res.data.total_pages || 1
  } catch (err) {
    error.value = err.response?.data?.detail || 'No se pudo cargar la cola.'
  } finally {
    cargando.value = false
  }
}

watch(() => route.query.cola, valor => {
  cola.value = valor || 'por_clasificar'
  pagina.value = 1
  cargar()
})

onMounted(cargar)
</script>
