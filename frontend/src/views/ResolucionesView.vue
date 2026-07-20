<template>
  <div class="page-shell animate-fade-in">
    <header class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <p class="eyebrow">Administración</p>
        <h2 class="page-title">Archivo documental de resoluciones</h2>
        <p class="page-subtitle">Repositorio histórico para consulta y calidad documental. La emisión y numeración se gestionan en Secretaría Académica.</p>
      </div>
      <div class="flex flex-wrap gap-2">
        <select v-model="anio" class="input-field w-40" @change="buscar">
          <option value="">Todos los años</option>
          <option v-for="valor in anios" :key="valor" :value="valor">{{ valor }}</option>
        </select>
        <button type="button" class="btn-outline" :disabled="cargando" @click="cargar">
          <i :class="cargando ? 'pi-spin pi-spinner' : 'pi-refresh'" class="pi"></i>Actualizar
        </button>
      </div>
    </header>

    <section class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4" aria-label="Resumen documental">
      <button v-for="item in resumenItems" :key="item.vista" type="button" :class="['control-card', vista === item.vista ? 'control-card-active' : '']" @click="seleccionarVista(item.vista)">
        <span :class="item.iconClass" class="control-icon"><i :class="item.icon" class="pi"></i></span>
        <span class="min-w-0">
          <span class="block text-xs font-semibold text-slate-900 dark:text-white">{{ item.label }}</span>
          <span class="mt-1 block text-[11px] leading-4 text-slate-500 dark:text-slate-400">{{ item.detalle }}</span>
        </span>
        <strong class="ml-auto text-2xl text-slate-950 dark:text-white">{{ item.total }}</strong>
      </button>
    </section>

    <div v-if="vista === 'diagnostico' || vista === 'descartado'" class="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-950 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100">
      <i class="pi pi-info-circle mr-2"></i><strong>No es una cola operativa.</strong>
      <template v-if="vista === 'descartado'"> Son actas, oficios u otros documentos conservados para auditoría que no corresponden al catálogo de resoluciones.</template>
      <template v-else> Son resoluciones o compilados cuya extracción no alcanzó evidencia suficiente; no representan resoluciones pendientes de elaboración en Secretaría.</template>
    </div>

    <section class="filter-bar">
      <div class="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(280px,1fr)_150px_170px_150px_auto]">
        <label class="relative block">
          <span class="sr-only">Buscar resolucion</span>
          <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400"></i>
          <input v-model="busqueda" class="input-field pl-9" placeholder="Resolución, estudiante, código o programa" @keyup.enter="buscar" />
        </label>
        <select v-model="paso" class="input-field" @change="buscar"><option value="">Todos los pasos</option><option v-for="numero in 7" :key="numero" :value="numero">Paso {{ numero }}</option></select>
        <select v-model="orden" class="input-field" @change="buscar"><option value="fecha_desc">Más recientes</option><option value="fecha_asc">Más antiguas</option><option value="numero_desc">Número: mayor primero</option><option value="numero_asc">Número: menor primero</option><option value="estudiante_asc">Estudiante A-Z</option><option value="programa_asc">Programa A-Z</option></select>
        <select v-model.number="porPagina" class="input-field" @change="buscar"><option :value="25">25 por pagina</option><option :value="50">50 por pagina</option><option :value="100">100 por pagina</option></select>
        <button type="button" class="btn-primary justify-center" @click="buscar"><i class="pi pi-filter"></i>Filtrar</button>
      </div>
    </section>

    <section class="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div class="flex flex-col gap-1 border-b border-slate-200 px-5 py-4 sm:flex-row sm:items-center sm:justify-between dark:border-slate-800">
        <div><h3 class="section-title">{{ vistaActual.label }}</h3><p class="mt-0.5 text-xs text-slate-500">{{ vistaActual.detalle }}</p></div>
        <span class="text-xs text-slate-500">{{ total }} registro(s)</span>
      </div>
      <div v-if="cargando" class="space-y-2 p-4"><div v-for="numero in 8" :key="numero" class="h-14 animate-pulse rounded bg-slate-100 dark:bg-slate-800"></div></div>
      <div v-else class="overflow-x-auto">
        <table class="data-table min-w-[980px]">
          <thead><tr><th>Resolución</th><th>Estudiante</th><th>Programa</th><th>Paso</th><th>Calidad documental</th><th>Archivo</th></tr></thead>
          <tbody>
            <tr v-if="resoluciones.length === 0"><td colspan="6" class="py-16 text-center"><i class="pi pi-check-circle mb-3 block text-3xl text-emerald-400"></i><p class="text-sm font-semibold text-slate-700 dark:text-slate-200">No hay registros en esta vista</p></td></tr>
            <tr v-for="item in resoluciones" :key="item.id_documento" class="cursor-pointer" @click="seleccionar(item)">
              <td><p class="font-mono text-sm font-bold text-sky-700 dark:text-cyan-300">{{ numeroResolucion(item) }}</p><p class="mt-0.5 text-[11px] text-slate-500">{{ formatFecha(item.fecha_resolucion) }}</p></td>
              <td class="max-w-64"><p class="truncate text-sm font-semibold text-slate-900 dark:text-white">{{ item.nombre_alumno || 'Sin nombre extraido' }}</p><p class="truncate font-mono text-[11px] text-slate-500">{{ item.codigo_alumno || 'Sin codigo extraido' }}</p></td>
              <td class="max-w-80"><p class="truncate text-sm text-slate-700 dark:text-slate-200">{{ item.programa || 'Sin programa extraido' }}</p><p class="text-[11px] text-slate-500">{{ item.grado_postula || 'Grado no determinado' }}</p></td>
              <td><span class="badge badge-nuevo">P{{ item.id_paso_inferido || '-' }}</span></td>
              <td><span :class="badgeEstado(item.estado_revision)">{{ textoEstado(item.estado_revision) }}</span><p v-if="vista !== 'oficial'" class="mt-1 max-w-56 truncate text-[10px] text-slate-500">{{ item.observaciones || 'Extraccion incompleta' }}</p></td>
              <td><button type="button" class="icon-btn" title="Ver detalle" aria-label="Ver detalle" @click.stop="seleccionar(item)"><i class="pi pi-eye"></i></button></td>
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

    <div v-if="seleccionada" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm" @click.self="seleccionada = null">
      <section class="card max-h-[90vh] w-full max-w-4xl overflow-y-auto">
        <header class="flex items-start justify-between gap-4"><div><p class="eyebrow">Detalle documental</p><h3 class="section-title mt-1">{{ numeroResolucion(seleccionada) }}</h3><p class="mt-1 break-all text-[11px] text-slate-500">{{ seleccionada.source_path }}</p></div><button type="button" class="icon-btn" title="Cerrar" aria-label="Cerrar" @click="seleccionada = null"><i class="pi pi-times"></i></button></header>
        <div class="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3"><div><span class="input-label">Estudiante</span><p class="text-sm font-semibold text-slate-900 dark:text-white">{{ seleccionada.nombre_alumno || 'Sin nombre' }}</p></div><div><span class="input-label">Programa</span><p class="text-sm text-slate-900 dark:text-white">{{ seleccionada.programa || 'Sin programa' }}</p></div><div><span class="input-label">Clasificacion</span><p class="text-sm text-slate-900 dark:text-white">Paso {{ seleccionada.id_paso_inferido || '-' }} · {{ seleccionada.tipo_resolucion || 'Sin tipo' }}</p></div></div>
        <div class="mt-5"><span class="input-label">Texto extraido</span><p class="max-h-80 overflow-y-auto whitespace-pre-wrap rounded-md border border-slate-200 bg-slate-50 p-4 text-xs leading-6 text-slate-700 dark:border-slate-700 dark:bg-slate-950/50 dark:text-slate-300">{{ seleccionada.texto_preview || 'Sin texto extraido' }}</p></div>
        <div class="mt-5 flex justify-end"><button type="button" class="btn-outline" @click="abrirArchivo(seleccionada)"><i class="pi pi-external-link"></i>Abrir archivo</button></div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../api.js'

const resoluciones = ref([])
const resumenControl = ref({})
const vista = ref('oficial')
const anio = ref('')
const paso = ref('')
const orden = ref('fecha_desc')
const busqueda = ref('')
const pagina = ref(1)
const porPagina = ref(25)
const total = ref(0)
const totalPaginas = ref(1)
const cargando = ref(true)
const seleccionada = ref(null)
const actual = new Date().getFullYear()
const anios = Array.from({ length: 14 }, (_, indice) => actual - indice)

const resumenItems = computed(() => [
  { vista: 'oficial', label: 'Archivo utilizable', detalle: 'Resoluciones importadas o verificadas', total: resumenControl.value.utilizables || 0, icon: 'pi-verified', iconClass: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300' },
  { vista: 'revision', label: 'Revisión prioritaria', detalle: 'Resoluciones reconocibles con un dato pendiente', total: resumenControl.value.revision_prioritaria || 0, icon: 'pi-pencil', iconClass: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300' },
  { vista: 'diagnostico', label: 'Diagnóstico de extracción', detalle: 'Actas, compilados o PDFs incompletos; no es trabajo diario', total: resumenControl.value.diagnostico_extraccion || 0, icon: 'pi-wrench', iconClass: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200' },
  { vista: 'descartado', label: 'Fuera del catálogo', detalle: 'Actas, oficios u otros documentos conservados sin mezclarlos', total: resumenControl.value.documentos_ajenos || 0, icon: 'pi-ban', iconClass: 'bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300' },
])
const vistaActual = computed(() => resumenItems.value.find(item => item.vista === vista.value) || resumenItems.value[0])

function seleccionarVista(valor) { vista.value = valor; pagina.value = 1; cargar() }
function buscar() { pagina.value = 1; cargar() }
function cambiarPagina(valor) { if (valor < 1 || valor > totalPaginas.value) return; pagina.value = valor; cargar() }
function seleccionar(item) { seleccionada.value = item }
function numeroResolucion(item) { return item.resolucion_numero ? `${item.resolucion_numero}-${item.resolucion_anio || '----'}` : 'Sin numero extraido' }
function formatFecha(valor) { if (!valor) return 'Fecha no extraida'; const fecha = new Date(valor); return Number.isNaN(fecha.getTime()) ? 'Fecha no extraida' : fecha.toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric' }) }
function textoEstado(valor) { return valor === 'Importado' ? 'Vinculada al sistema' : valor === 'OK' ? 'Verificada' : valor === 'Descartado' ? 'Fuera del catálogo' : 'Extracción incompleta' }
function badgeEstado(valor) { return valor === 'Importado' ? 'badge badge-graduado' : valor === 'OK' ? 'badge badge-proceso' : valor === 'Descartado' ? 'badge badge-caducado' : 'badge badge-observado' }

async function abrirArchivo(item) {
  try {
    const respuesta = await api.get(item.api_archivo_url, { responseType: 'blob' })
    const url = URL.createObjectURL(respuesta.data)
    window.open(url, '_blank', 'noopener')
    window.setTimeout(() => URL.revokeObjectURL(url), 60000)
  } catch (error) { console.error(error) }
}

async function cargar() {
  cargando.value = true
  try {
    const params = { vista: vista.value, page: pagina.value, per_page: porPagina.value, orden: orden.value }
    if (anio.value) params.anio = anio.value
    if (paso.value) params.id_paso = paso.value
    if (busqueda.value.trim()) params.busqueda = busqueda.value.trim()
    const respuesta = (await api.get('/resoluciones', { params })).data
    resoluciones.value = respuesta.data || []
    resumenControl.value = respuesta.resumen_control || {}
    total.value = respuesta.total || 0
    totalPaginas.value = respuesta.total_pages || 1
  } catch (error) { console.error(error) } finally { cargando.value = false }
}

onMounted(cargar)
</script>

<style scoped>
.control-card { align-items: center; background: white; border: 1px solid rgb(226 232 240); display: flex; gap: .8rem; min-height: 88px; padding: .9rem; text-align: left; }
.control-card:hover { border-color: rgb(125 211 252); }
.control-card-active { border-color: rgb(14 116 144); box-shadow: inset 0 0 0 1px rgb(14 116 144); }
.control-icon { align-items: center; border-radius: .375rem; display: inline-flex; flex: 0 0 auto; height: 2.25rem; justify-content: center; width: 2.25rem; }
:global(html.dark .control-card) { background: rgb(15 23 42); border-color: rgb(51 65 85); }
:global(html.dark .control-card:hover), :global(html.dark .control-card-active) { border-color: rgb(34 211 238); }
</style>
