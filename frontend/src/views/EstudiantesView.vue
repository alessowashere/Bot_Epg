<template>
  <div class="page-shell animate-fade-in">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="eyebrow">Consulta académica</p>
        <h2 class="page-title">Estudiantes y trayectorias</h2>
        <p class="page-subtitle">Una persona puede tener varias maestrías, doctorados o trámites; nunca se fusionan por nombre.</p>
      </div>
      <span class="badge badge-proceso">{{ total }} personas</span>
    </div>

    <div class="card flex flex-wrap gap-3 p-4">
      <div class="relative min-w-64 flex-1">
        <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400"></i>
        <input v-model="busqueda" class="input-field pl-9" placeholder="Nombre, DNI, código, programa o tesis..." @keyup.enter="buscar" />
      </div>
      <button class="btn-primary" @click="buscar"><i class="pi pi-search"></i> Buscar</button>
    </div>

    <div class="grid gap-5 xl:grid-cols-[minmax(340px,0.8fr)_minmax(0,1.7fr)]">
      <section class="card overflow-hidden p-0">
        <div class="border-b border-slate-200 px-4 py-3 dark:border-slate-700">
          <p class="text-sm font-bold text-slate-900 dark:text-white">Personas encontradas</p>
          <p class="mt-0.5 text-xs text-slate-500">Selecciona una para revisar sus trayectorias separadas.</p>
        </div>
        <div v-if="cargandoLista" class="space-y-3 p-4"><div v-for="i in 8" :key="i" class="h-14 animate-pulse rounded bg-slate-200 dark:bg-slate-800"></div></div>
        <div v-else class="max-h-[650px] overflow-y-auto p-2">
          <button v-for="persona in personas" :key="persona.id_persona" type="button" :class="['mb-1 w-full rounded-md border p-3 text-left transition-colors', seleccion?.id_persona === persona.id_persona ? 'border-cyan-400 bg-cyan-50 dark:bg-cyan-500/10' : 'border-transparent hover:bg-slate-50 dark:hover:bg-slate-800/70']" @click="seleccionar(persona)">
            <span class="block truncate text-sm font-bold text-slate-900 dark:text-white">{{ persona.nombre }}</span>
            <span class="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500">
              <span v-if="persona.dni">DNI {{ persona.dni }}</span>
              <span>{{ persona.trayectorias }} trayectoria(s)</span>
              <span>{{ persona.maestrias }} M · {{ persona.doctorados }} D</span>
            </span>
          </button>
          <p v-if="!personas.length" class="p-8 text-center text-sm text-slate-500">No hay personas aún. La reconstrucción de trayectorias sigue en curso.</p>
        </div>
        <div class="flex items-center justify-between border-t border-slate-200 px-4 py-3 text-xs dark:border-slate-700">
          <span>Página {{ pagina }} de {{ totalPaginas }}</span>
          <div class="flex gap-2"><button class="btn-ghost btn-sm" :disabled="pagina <= 1" @click="cambiarPagina(-1)">Anterior</button><button class="btn-ghost btn-sm" :disabled="pagina >= totalPaginas" @click="cambiarPagina(1)">Siguiente</button></div>
        </div>
      </section>

      <section class="card min-h-[420px] p-0">
        <div v-if="cargandoDetalle" class="space-y-4 p-5"><div class="h-8 w-2/5 animate-pulse rounded bg-slate-200 dark:bg-slate-800"></div><div v-for="i in 3" :key="i" class="h-44 animate-pulse rounded bg-slate-200 dark:bg-slate-800"></div></div>
        <div v-else-if="detalle" class="p-5">
          <div class="mb-5 flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 pb-4 dark:border-slate-700">
            <div><p class="eyebrow">Estudiante</p><h3 class="text-xl font-bold text-slate-900 dark:text-white">{{ detalle.persona.nombre }}</h3><p class="mt-1 text-sm text-slate-500"><span v-if="detalle.persona.dni">DNI {{ detalle.persona.dni }} · </span>{{ detalle.trayectorias.length }} trayectoria(s) documentada(s)</p></div>
            <span :class="detalle.persona.estado_identidad === 'confirmada_dni' ? 'badge-graduado' : 'badge-observado'">{{ etiquetaIdentidad(detalle.persona.estado_identidad) }}</span>
          </div>
          <div class="space-y-4">
            <article v-for="trayectoria in detalle.trayectorias" :key="trayectoria.id_trayectoria" class="rounded-md border border-slate-200 p-4 dark:border-slate-700">
              <div class="flex flex-wrap items-start justify-between gap-3"><div><div class="flex flex-wrap gap-2"><span :class="trayectoria.grado === 'Doctor' ? 'badge-proceso' : 'badge-nuevo'">{{ trayectoria.grado }}</span><span class="badge">P{{ trayectoria.paso_actual || '?' }}</span><span class="badge badge-archivo">{{ trayectoria.estado }}</span></div><h4 class="mt-3 text-sm font-bold text-slate-900 dark:text-white">{{ trayectoria.programa || 'Programa por confirmar' }}</h4><p v-if="trayectoria.titulo_tesis" class="mt-1 text-xs leading-relaxed text-slate-500">{{ trayectoria.titulo_tesis }}</p></div><button v-for="expediente in trayectoria.expedientes" :key="expediente.uuid" class="btn-ghost btn-sm" @click="abrirExpediente(expediente)"><i class="pi pi-folder-open"></i> Expediente</button></div>
              <div class="mt-4 grid gap-3 border-y border-slate-100 py-3 text-xs dark:border-slate-800 sm:grid-cols-3"><span><b>{{ trayectoria.total_documentos }}</b> resoluciones</span><span><b>{{ trayectoria.tickets.length }}</b> tickets vinculados</span><span>Última: <b>{{ trayectoria.fecha_ultima_resolucion || 'sin fecha' }}</b></span></div>
              <div v-if="trayectoria.documentos.length" class="mt-3"><p class="mb-2 text-[11px] font-semibold uppercase text-slate-500">Resoluciones recientes</p><div class="space-y-1"><p v-for="documento in trayectoria.documentos.slice(0, 4)" :key="documento.id_documento" class="truncate text-xs text-slate-600 dark:text-slate-300">{{ documento.numero || 'Sin número' }} · P{{ documento.paso || '?' }} · {{ documento.fecha || 'sin fecha' }} · {{ documento.archivo }}</p></div></div>
              <div v-if="trayectoria.tickets.length" class="mt-3 flex flex-wrap gap-2"><button v-for="ticket in trayectoria.tickets" :key="ticket.uuid" class="btn-ghost btn-sm" @click="abrirTicket(ticket)">#{{ ticket.numero_visual }} · {{ ticket.estado }}</button></div>
            </article>
          </div>
        </div>
        <div v-else class="flex min-h-[420px] items-center justify-center p-10 text-center text-sm text-slate-500">Selecciona una persona para abrir sus expedientes y trayectorias.</div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api.js'

const router = useRouter()
const busqueda = ref('')
const personas = ref([])
const seleccion = ref(null)
const detalle = ref(null)
const cargandoLista = ref(false)
const cargandoDetalle = ref(false)
const pagina = ref(1)
const total = ref(0)
const totalPaginas = ref(1)

async function cargarLista() {
  cargandoLista.value = true
  try {
    const { data } = await api.get('/estudiantes', { params: { q: busqueda.value.trim() || undefined, page: pagina.value, per_page: 25 } })
    personas.value = data.data || []
    total.value = data.total || 0
    totalPaginas.value = data.total_pages || 1
    if (personas.value.length && (!seleccion.value || !personas.value.some(item => item.id_persona === seleccion.value.id_persona))) await seleccionar(personas.value[0])
  } finally { cargandoLista.value = false }
}
async function seleccionar(persona) {
  seleccion.value = persona
  cargandoDetalle.value = true
  try { detalle.value = (await api.get(`/estudiantes/${persona.id_persona}`)).data } finally { cargandoDetalle.value = false }
}
function buscar() { pagina.value = 1; seleccion.value = null; detalle.value = null; cargarLista() }
function cambiarPagina(delta) { pagina.value += delta; seleccion.value = null; detalle.value = null; cargarLista() }
function abrirExpediente(expediente) { router.push(`/expedientes/${expediente.uuid || expediente.id_expediente}`) }
function abrirTicket(ticket) { router.push(`/bandeja/${ticket.uuid || ticket.ticket_id}`) }
function etiquetaIdentidad(estado) { return estado === 'confirmada_dni' ? 'Identidad confirmada' : estado === 'nombre_ambiguo' ? 'Nombre por verificar' : 'Identidad consensuada' }
onMounted(cargarLista)
</script>
