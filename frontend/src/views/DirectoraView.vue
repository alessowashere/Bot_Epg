<template>
  <div class="page-shell animate-fade-in">
    <header class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="eyebrow">Dirección</p>
        <h2 class="page-title">Resoluciones para firma</h2>
        <p class="page-subtitle">Revisa el Word, firma con ReFirma y devuelve el PDF al tramitador.</p>
      </div>
      <button type="button" class="btn-ghost btn-sm" @click="cargar"><i class="pi pi-refresh"></i> Actualizar</button>
    </header>

    <div v-if="mensaje" :class="['rounded-md border px-3 py-2 text-xs', error ? 'border-red-500/30 bg-red-950/30 text-red-200' : 'border-emerald-500/30 bg-emerald-950/30 text-emerald-200']">{{ mensaje }}</div>

    <div v-if="cargando" class="card py-14 text-center text-sm text-slate-500"><i class="pi pi-spin pi-spinner mr-2"></i>Cargando bandeja</div>
    <div v-else-if="!tramites.length" class="card py-14 text-center"><i class="pi pi-check-circle text-3xl text-emerald-300"></i><p class="mt-3 text-sm text-slate-400">No hay resoluciones pendientes de firma.</p></div>
    <div v-else class="space-y-4">
      <article v-for="tramite in tramites" :key="tramite.uuid" class="card">
        <div class="grid grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div class="min-w-0">
            <div class="flex flex-wrap items-start justify-between gap-2">
              <div><p class="eyebrow">{{ tramite.numero_resolucion }} · Paso {{ tramite.id_paso }}</p><h3 class="text-base font-semibold text-slate-900 dark:text-white">{{ tramite.estudiante }}</h3><p class="mt-1 text-xs text-slate-600 dark:text-slate-400">{{ tramite.codigo_alumno }} · {{ tramite.tipo_resolucion }}</p></div>
              <span class="badge-observado">Pendiente de firma</span>
            </div>
            <p v-if="tramite.titulo_tesis" class="mt-4 text-sm leading-6 text-slate-700 dark:text-slate-300">{{ tramite.titulo_tesis }}</p>
            <dl class="mt-4 grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
              <div><dt class="text-slate-500">Fecha</dt><dd class="mt-1 text-slate-900 dark:text-white">{{ tramite.fecha_resolucion }}</dd></div>
              <div><dt class="text-slate-500">Origen</dt><dd class="mt-1 text-slate-900 dark:text-white">{{ tramite.sistema_origen }}</dd></div>
              <div><dt class="text-slate-500">Consulta</dt><dd class="mt-1 text-slate-900 dark:text-white">{{ tramite.requiere_consulta_previa ? `${tramite.consultas_resumen.aceptadas} aceptada(s)` : 'No requerida' }}</dd></div>
              <div><dt class="text-slate-500">Word</dt><dd class="mt-1 text-slate-900 dark:text-white">Versión {{ tramite.borrador_version }}</dd></div>
            </dl>
            <div class="mt-5 flex flex-wrap gap-2">
              <a :href="tramite.borrador_word_url" target="_blank" rel="noopener" class="btn-primary"><i class="pi pi-file-word"></i> Abrir Word para revisión</a>
              <router-link :to="`/expedientes/${tramite.expediente_uuid}`" class="btn-ghost"><i class="pi pi-folder-open"></i> Ver expediente</router-link>
            </div>
          </div>

          <div class="border-t border-slate-700 pt-4 lg:border-l lg:border-t-0 lg:pl-5 lg:pt-0">
            <label :for="`nota-${tramite.uuid}`" class="input-label">Nota de revisión</label>
            <textarea :id="`nota-${tramite.uuid}`" v-model="formularios[tramite.uuid].nota" class="input-field mt-1 resize-none text-xs" rows="3" placeholder="Obligatoria si devuelve con observaciones"></textarea>
            <label :for="`pdf-${tramite.uuid}`" class="input-label mt-4">PDF firmado con ReFirma</label>
            <input :id="`pdf-${tramite.uuid}`" type="file" accept="application/pdf,.pdf" class="input-field mt-1 text-xs" @change="formularios[tramite.uuid].archivo = $event.target.files?.[0] || null" />
            <div class="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
              <button type="button" class="btn-danger justify-center" :disabled="procesando || !formularios[tramite.uuid].nota.trim()" @click="observar(tramite)"><i class="pi pi-undo"></i> Devolver</button>
              <button type="button" class="btn-success justify-center" :disabled="procesando || !formularios[tramite.uuid].archivo" @click="firmar(tramite)"><i class="pi pi-check"></i> Subir y devolver PDF</button>
            </div>
            <p class="mt-3 text-[11px] leading-4 text-slate-500">El sistema no firma el documento. La firma se realiza externamente con ReFirma y aquí se conserva el PDF resultante con su huella SHA-256.</p>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import api from '../api.js'

const tramites = ref([])
const formularios = reactive({})
const cargando = ref(true)
const procesando = ref(false)
const mensaje = ref('')
const error = ref(false)

async function cargar() {
  cargando.value = true
  try {
    const res = await api.get('/resolucion-tramites', { params: { estado: 'listo_para_direccion', per_page: 100 } })
    tramites.value = res.data.data
    for (const item of tramites.value) if (!formularios[item.uuid]) formularios[item.uuid] = { nota: '', archivo: null }
  } catch (e) { mostrarError(e) } finally { cargando.value = false }
}

function mostrarError(e) { error.value = true; mensaje.value = e.response?.data?.detail || 'No se pudo completar la acción.' }
async function ejecutar(fn, texto) { procesando.value = true; mensaje.value = ''; try { await fn(); error.value = false; mensaje.value = texto; await cargar() } catch (e) { mostrarError(e) } finally { procesando.value = false } }
function observar(tramite) { ejecutar(() => api.post(`/resolucion-tramites/${tramite.uuid}/observar-direccion`, { nota: formularios[tramite.uuid].nota }), 'La resolución volvió a Secretaría con observaciones.') }
function firmar(tramite) { const form = new FormData(); form.append('archivo_pdf', formularios[tramite.uuid].archivo); if (formularios[tramite.uuid].nota) form.append('nota', formularios[tramite.uuid].nota); ejecutar(() => api.post(`/resolucion-tramites/${tramite.uuid}/firmar`, form), 'PDF firmado cargado y devuelto al tramitador.') }

onMounted(cargar)
</script>
