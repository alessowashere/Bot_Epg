<template>
  <section class="rounded-lg border border-sky-200 bg-white shadow-sm dark:border-cyan-500/25 dark:bg-slate-900">
    <header class="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
      <div class="flex items-start justify-between gap-3">
        <div>
          <p class="eyebrow">Mesa de trámite</p>
          <h3 class="section-title">Clasificar y enviar</h3>
          <p class="mt-1 text-xs text-slate-500">Paso, documentos y derivación en un solo lugar.</p>
        </div>
        <span v-if="mesa?.inferencia" :class="confianza >= 0.8 ? 'badge-graduado' : 'badge-observado'">
          {{ Math.round(confianza * 100) }}% detectado
        </span>
      </div>
    </header>

    <div v-if="cargando" class="space-y-3 p-5"><div v-for="i in 4" :key="i" class="h-14 animate-pulse rounded-md bg-slate-100 dark:bg-slate-800"></div></div>
    <div v-else-if="error" class="p-5 text-sm text-red-700 dark:text-red-300">{{ error }}</div>
    <div v-else-if="mesa" class="space-y-5 p-5">
      <div v-if="mesa.tramite_activo" class="rounded-md border border-emerald-200 bg-emerald-50 p-3 dark:border-emerald-500/30 dark:bg-emerald-500/10">
        <p class="text-xs font-semibold text-emerald-800 dark:text-emerald-200">Ya está en Secretaría</p>
        <p class="mt-1 text-xs text-emerald-700 dark:text-emerald-300">P{{ mesa.tramite_activo.id_paso }} · {{ mesa.tramite_activo.tipo_resolucion }} · {{ etiquetaEstado(mesa.tramite_activo.estado) }}</p>
      </div>

      <template v-else>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <label><span class="input-label">Paso que se tramitará</span><select v-model.number="idPaso" class="input-field" @change="cambiarPaso"><option v-for="paso in 7" :key="paso" :value="paso">P{{ paso }} · {{ nombrePaso(paso) }}</option></select></label>
          <label><span class="input-label">Tipo de resolución</span><select v-model="tipoResolucion" class="input-field"><option v-for="tipo in tiposDelPaso" :key="tipo.codigo" :value="tipo.nombre">{{ tipo.nombre }}</option></select></label>
        </div>

        <div v-if="mesa.inferencia.fuentes?.length" class="rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800/60">
          <p v-for="fuente in mesa.inferencia.fuentes" :key="fuente" class="text-[11px] leading-5 text-slate-600 dark:text-slate-300"><i class="pi pi-check-circle mr-1 text-emerald-500"></i>{{ fuente }}</p>
          <p v-for="aviso in mesa.inferencia.discrepancias" :key="aviso" class="mt-1 text-[11px] leading-5 text-amber-700 dark:text-amber-300"><i class="pi pi-exclamation-triangle mr-1"></i>{{ aviso }}</p>
        </div>

        <div>
          <div class="flex items-end justify-between gap-3">
            <div><h4 class="text-sm font-semibold text-slate-900 dark:text-white">Archivos recibidos</h4><p class="mt-0.5 text-[11px] text-slate-500">Arrastra cada archivo a una o varias cajas. También puedes elegir la caja.</p></div>
            <span class="text-xs text-slate-500">{{ mesa.adjuntos.length }} archivo(s)</span>
          </div>
          <div v-if="mesa.adjuntos.length" class="mt-3 grid grid-cols-1 gap-2">
            <article v-for="adjunto in mesa.adjuntos" :key="adjunto.id_adjunto" draggable="true" class="rounded-md border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-950/50" @dragstart="iniciarArrastre($event, adjunto)">
              <div class="flex items-center gap-2"><i class="pi pi-file text-red-500"></i><p class="min-w-0 flex-1 truncate text-xs font-semibold text-slate-800 dark:text-slate-100">{{ adjunto.nombre }}</p><button type="button" class="icon-btn h-7 w-7" title="Abrir archivo" @click="abrir(adjunto.api_archivo_url)"><i class="pi pi-eye"></i></button></div>
              <div class="mt-2 flex gap-2"><select v-model="destinos[adjunto.id_adjunto]" class="input-field min-w-0 flex-1 !py-1.5 text-xs"><option value="">Elegir caja</option><option v-for="requisito in requisitos" :key="requisito.id_expediente_requisito" :value="requisito.id_expediente_requisito">{{ requisito.nombre }}</option></select><button type="button" class="btn-outline btn-sm" :disabled="!destinos[adjunto.id_adjunto] || procesando" @click="asignar(adjunto.id_adjunto, destinos[adjunto.id_adjunto])"><i class="pi pi-arrow-down"></i></button></div>
            </article>
          </div>
          <p v-else class="mt-3 rounded-md border border-dashed border-slate-300 p-4 text-center text-xs text-slate-500 dark:border-slate-700">El ticket no contiene archivos.</p>
        </div>

        <div>
          <h4 class="text-sm font-semibold text-slate-900 dark:text-white">Requisitos de P{{ idPaso }}</h4>
          <div class="mt-3 grid grid-cols-1 gap-3">
            <article v-for="requisito in requisitos" :key="requisito.id_expediente_requisito" class="rounded-md border border-slate-200 p-3 transition-colors dark:border-slate-700" @dragover.prevent @drop.prevent="soltarEnCaja($event, requisito)">
              <div class="flex items-start justify-between gap-3"><div><p class="text-xs font-semibold text-slate-900 dark:text-white">{{ requisito.nombre }}</p><p class="mt-0.5 text-[10px] text-slate-500">{{ requisito.obligatorio ? 'Obligatorio' : 'Según corresponda' }} · {{ requisito.tipo_evidencia }}</p></div><span :class="requisito.archivos?.length ? 'badge-proceso' : 'badge'">{{ requisito.archivos?.length || 0 }}</span></div>
              <div v-if="requisito.archivos?.length" class="mt-2 divide-y divide-slate-100 dark:divide-slate-800">
                <div v-for="archivo in requisito.archivos" :key="archivo.id_requisito_archivo" class="flex items-center gap-2 py-2"><i class="pi pi-paperclip text-sky-600"></i><button type="button" class="min-w-0 flex-1 truncate text-left text-[11px] text-sky-700 hover:underline dark:text-cyan-300" @click="abrir(archivo.api_archivo_url)">{{ archivo.archivo_nombre }}</button><button type="button" class="icon-btn h-7 w-7" title="Quitar de esta caja" @click="quitar(requisito, archivo)"><i class="pi pi-times"></i></button></div>
              </div>
              <label class="mt-2 flex cursor-pointer items-center justify-center gap-2 rounded-md border border-dashed border-slate-300 px-3 py-2 text-[11px] text-slate-500 hover:border-sky-400 hover:text-sky-700 dark:border-slate-700 dark:hover:border-cyan-500 dark:hover:text-cyan-300"><i class="pi pi-upload"></i>Arrastra aquí o carga un archivo<input type="file" class="hidden" multiple @change="subir($event, requisito)" /></label>
            </article>
          </div>
          <p v-if="!requisitos.length" class="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300">No existe catálogo de requisitos para este paso. Puedes derivar, pero Secretaría deberá validar los documentos manualmente.</p>
        </div>

        <label v-if="[4, 7].includes(idPaso)"><span class="input-label">Referencia del ERP</span><input v-model="referenciaOrigen" class="input-field" placeholder="Número o referencia del trámite en ERP" /></label>
        <label v-if="mesa.inferencia.tramite_intermedio" class="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200"><input v-model="confirmarIntermedio" type="checkbox" class="mt-0.5 h-4 w-4 accent-cyan-600" /><span>El texto parece levantamiento, subsanación u otro trámite intermedio. Confirmo que excepcionalmente debe producir una resolución.</span></label>
        <button type="button" class="btn-primary w-full justify-center" :disabled="procesando || (mesa.inferencia.tramite_intermedio && !confirmarIntermedio)" @click="derivar"><i :class="procesando ? 'pi-spin pi-spinner' : 'pi-send'" class="pi"></i>Enviar a Secretaría como P{{ idPaso }}</button>
      </template>
      <p v-if="mensaje" :class="mensajeError ? 'text-red-600 dark:text-red-300' : 'text-emerald-700 dark:text-emerald-300'" class="text-xs">{{ mensaje }}</p>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import api from '../api.js'

const props = defineProps({ ticketRef: { type: String, required: true }, expediente: { type: Object, default: null } })
const emit = defineEmits(['actualizado'])
const mesa = ref(null)
const requisitos = ref([])
const cargando = ref(true)
const procesando = ref(false)
const error = ref('')
const mensaje = ref('')
const mensajeError = ref(false)
const idPaso = ref(1)
const tipoResolucion = ref('')
const referenciaOrigen = ref('')
const confirmarIntermedio = ref(false)
const destinos = reactive({})
const confianza = computed(() => Number(mesa.value?.inferencia?.confianza || 0))
const tiposDelPaso = computed(() => (mesa.value?.tipos_resolucion || []).filter(item => item.id_paso === idPaso.value))

const PASOS = { 1: 'Nombramiento de asesor', 2: 'Dictamen de proyecto', 3: 'Inscripción del proyecto', 4: 'Declarado apto', 5: 'Dictamen de tesis', 6: 'Sustentación', 7: 'Diploma' }
function nombrePaso(paso) { return PASOS[paso] }
function etiquetaEstado(estado) { return ({ derivado_secretaria: 'Pendiente de revisión', en_elaboracion_secretaria: 'En elaboración', consulta_previa: 'Consulta previa', listo_para_direccion: 'En Dirección' })[estado] || estado }

async function cargar() {
  if (!props.expediente) { cargando.value = false; return }
  cargando.value = true; error.value = ''
  try {
    mesa.value = (await api.get(`/tickets/${props.ticketRef}/mesa-tramite`)).data
    idPaso.value = mesa.value.inferencia.id_paso
    tipoResolucion.value = mesa.value.inferencia.tipo_resolucion
    requisitos.value = mesa.value.requisitos || []
  } catch (e) { error.value = e.response?.data?.detail || 'No se pudo preparar la mesa de trámite.' } finally { cargando.value = false }
}
async function cambiarPaso() {
  tipoResolucion.value = tiposDelPaso.value[0]?.nombre || nombrePaso(idPaso.value)
  try { requisitos.value = (await api.get(`/expedientes/${props.expediente.uuid}/requisitos`, { params: { id_paso: idPaso.value } })).data.data || [] } catch (e) { mostrar(e) }
}
function iniciarArrastre(evento, adjunto) { evento.dataTransfer.effectAllowed = 'copy'; evento.dataTransfer.setData('text/plain', `adjunto:${adjunto.id_adjunto}`) }
function soltarEnCaja(evento, requisito) {
  const referencia = evento.dataTransfer.getData('text/plain')
  if (referencia.startsWith('adjunto:')) asignar(Number(referencia.split(':')[1]), requisito.id_expediente_requisito)
  else if (evento.dataTransfer.files?.length) subirArchivos([...evento.dataTransfer.files], requisito)
}
async function asignar(idAdjunto, idRequisito) {
  procesando.value = true
  try { await api.post(`/expedientes/${props.expediente.uuid}/requisitos/${idRequisito}/archivos/asignar`, { id_adjunto: Number(idAdjunto), estado: 'Presentado' }); await cambiarPaso(); mensajeError.value = false; mensaje.value = 'Archivo clasificado.' } catch (e) { mostrar(e) } finally { procesando.value = false }
}
function subir(evento, requisito) { const archivos = [...(evento.target.files || [])]; evento.target.value = ''; subirArchivos(archivos, requisito) }
async function subirArchivos(archivos, requisito) {
  procesando.value = true
  try { for (const archivo of archivos) { const form = new FormData(); form.append('archivo', archivo); await api.post(`/expedientes/${props.expediente.uuid}/requisitos/${requisito.id_expediente_requisito}/archivos/subir`, form) } await cambiarPaso(); mensajeError.value = false; mensaje.value = `${archivos.length} archivo(s) cargado(s).` } catch (e) { mostrar(e) } finally { procesando.value = false }
}
async function quitar(requisito, archivo) {
  procesando.value = true
  try { await api.delete(`/expedientes/${props.expediente.uuid}/requisitos/${requisito.id_expediente_requisito}/archivos/${archivo.id_requisito_archivo}`); await cambiarPaso() } catch (e) { mostrar(e) } finally { procesando.value = false }
}
async function abrir(url) {
  try { const respuesta = await api.get(url, { responseType: 'blob' }); const objeto = URL.createObjectURL(respuesta.data); window.open(objeto, '_blank', 'noopener'); window.setTimeout(() => URL.revokeObjectURL(objeto), 60000) } catch (e) { mostrar(e) }
}
async function derivar() {
  procesando.value = true; mensaje.value = ''
  try {
    const respuesta = await api.post(`/tickets/${props.ticketRef}/preparar-derivacion`, { id_paso: idPaso.value, tipo_resolucion: tipoResolucion.value, referencia_origen: referenciaOrigen.value || null, confirmar_tramite_intermedio: confirmarIntermedio.value })
    mensajeError.value = false; mensaje.value = respuesta.data.mensaje; await cargar(); emit('actualizado')
  } catch (e) { mostrar(e) } finally { procesando.value = false }
}
function mostrar(e) { mensajeError.value = true; mensaje.value = e.response?.data?.detail || 'No se pudo completar la acción.' }

watch(() => props.expediente?.uuid, cargar)
onMounted(cargar)
</script>
