<template>
  <!-- Modal de previsualización universal -->
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex flex-col"
      @click.self="$emit('update:modelValue', null)"
    >
      <!-- Barra superior del visor -->
      <div class="flex items-center gap-3 px-4 py-3 bg-slate-900/95 border-b border-slate-700/50 flex-shrink-0">
        <!-- Ícono de tipo de archivo -->
        <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" :class="iconoBg">
          <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path v-if="tipoArchivo === 'pdf'" stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625A3.375 3.375 0 0016.125 8.25h-1.5A1.125 1.125 0 0113.5 7.125v-1.5A3.375 3.375 0 0010.125 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            <path v-else-if="tipoArchivo === 'imagen'" stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
            <path v-else stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625A3.375 3.375 0 0016.125 8.25h-1.5A1.125 1.125 0 0113.5 7.125v-1.5A3.375 3.375 0 0010.125 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
        </div>

        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-white truncate">{{ modelValue?.nombre || modelValue?.nombre_archivo }}</p>
          <p class="text-xs text-slate-400">{{ etiquetaTipo }}</p>
        </div>

        <div class="flex items-center gap-2 flex-shrink-0">
          <!-- Botón abrir en nueva pestaña -->
          <button
            type="button"
            class="btn-ghost btn-sm"
            title="Abrir en nueva pestaña"
            :disabled="!urlVisor"
            @click="abrirEnNuevaPestana"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
            </svg>
          </button>
          <!-- Botón descargar -->
          <button
            type="button"
            class="btn-outline btn-sm"
            :disabled="!urlVisor"
            @click="descargarArchivo"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            Descargar
          </button>
          <!-- Cerrar -->
          <button @click="$emit('update:modelValue', null)" class="btn-ghost btn-sm text-slate-400 hover:text-white">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Área de visualización -->
      <div class="flex-1 overflow-auto flex items-center justify-center p-4">

        <!-- IMAGEN: renderizado nativo con lightbox -->
        <div v-if="tipoArchivo === 'imagen'" class="flex items-center justify-center w-full h-full">
          <img
            v-if="urlVisor && !cargandoArchivo && !errorCargando"
            :src="urlVisor"
            :alt="modelValue?.nombre"
            class="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
            @error="errorCargando = true"
          />
          <p v-else-if="cargandoArchivo" class="text-sm text-slate-300">Cargando archivo seguro...</p>
          <div v-if="errorCargando" class="text-slate-400 text-sm text-center">
            <p>No se pudo cargar la imagen.</p>
            <button type="button" class="mt-2 text-indigo-400 underline" @click="abrirEnNuevaPestana">Abrir directamente</button>
          </div>
        </div>

        <!-- PDF: iframe directo (si URL local) o Google Docs Viewer (si URL externa) -->
        <div v-else-if="tipoArchivo === 'pdf'" class="w-full h-full flex flex-col">
          <p v-if="cargandoArchivo" class="py-8 text-center text-sm text-slate-300">Cargando archivo seguro...</p>
          <iframe
            v-else-if="urlIframePdf && !errorCargando"
            :src="urlIframePdf"
            class="w-full flex-1 rounded-lg border-0 bg-white"
            :title="modelValue?.nombre"
            @error="errorCargando = true"
          ></iframe>
          <div v-if="errorCargando" class="text-slate-400 text-sm text-center py-8">
            <p>No se pudo cargar el PDF en el visor.</p>
            <button type="button" class="btn-primary mt-4" @click="descargarArchivo">Descargar PDF</button>
          </div>
        </div>

        <!-- Word / Excel / otros: Google Docs Viewer iframe -->
        <div v-else-if="tipoArchivo === 'office'" class="w-full h-full flex flex-col">
          <div class="mb-3 text-center"><p class="text-xs text-slate-400">Los documentos Office se descargan de forma segura para abrirlos localmente.</p></div>
          <iframe
            v-if="!esArchivoProtegido"
            :src="`https://docs.google.com/gview?url=${encodeURIComponent(urlVisor)}&embedded=true`"
            class="w-full flex-1 rounded-lg border-0 bg-white"
            :title="modelValue?.nombre"
          ></iframe>
        </div>

        <!-- Formato no soportado -->
        <div v-else class="text-center py-12">
          <div class="w-16 h-16 rounded-2xl bg-slate-800 flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625A3.375 3.375 0 0016.125 8.25h-1.5A1.125 1.125 0 0113.5 7.125v-1.5A3.375 3.375 0 0010.125 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
          </div>
          <p class="text-slate-300 font-semibold">No hay previsualización disponible</p>
          <p class="text-slate-500 text-sm mt-1 mb-4">Este tipo de archivo no puede visualizarse en el navegador.</p>
          <button type="button" class="btn-primary" @click="descargarArchivo">Descargar archivo</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import api from '../api.js'

const props = defineProps({
  modelValue: {
    type: Object,
    default: null,
    // Espera: { nombre: string, url_visor: string } o { nombre_archivo: string, ruta_local: string }
  }
})

defineEmits(['update:modelValue'])

const errorCargando = ref(false)
const urlObjeto = ref('')
const cargandoArchivo = ref(false)

// Resetear error al cambiar el archivo
watch(() => props.modelValue, async () => {
  errorCargando.value = false
  if (urlObjeto.value) URL.revokeObjectURL(urlObjeto.value)
  urlObjeto.value = ''
  const archivo = props.modelValue
  if (!archivo?.api_archivo_url) return
  cargandoArchivo.value = true
  try {
    const respuesta = await api.get(archivo.api_archivo_url, { responseType: 'blob' })
    urlObjeto.value = URL.createObjectURL(respuesta.data)
  } catch {
    errorCargando.value = true
  } finally {
    cargandoArchivo.value = false
  }
}, { immediate: true })

onBeforeUnmount(() => { if (urlObjeto.value) URL.revokeObjectURL(urlObjeto.value) })

// URL a visualizar (compatibilidad con diferentes campos)
const urlVisor = computed(() => {
  const obj = props.modelValue
  if (!obj) return ''
  if (obj.api_archivo_url) return urlObjeto.value
  return obj.url_visor || obj.ruta_local || obj.archivo_drive_url || ''
})

const esArchivoProtegido = computed(() => Boolean(props.modelValue?.api_archivo_url))

function abrirEnNuevaPestana() {
  if (urlVisor.value) window.open(urlVisor.value, '_blank', 'noopener')
}

function descargarArchivo() {
  if (!urlVisor.value) return
  const enlace = document.createElement('a')
  enlace.href = urlVisor.value
  enlace.download = props.modelValue?.nombre || props.modelValue?.nombre_archivo || 'archivo'
  enlace.click()
}

// Detectar tipo de archivo
const tipoArchivo = computed(() => {
  const nombre = (props.modelValue?.nombre || props.modelValue?.nombre_archivo || '').toLowerCase()
  if (/\.(pdf)$/.test(nombre)) return 'pdf'
  if (/\.(jpg|jpeg|png|gif|webp|bmp|svg)$/.test(nombre)) return 'imagen'
  if (/\.(docx?|xlsx?|pptx?)$/.test(nombre)) return 'office'
  return 'otro'
})

// Para PDF: si la URL es relativa/local, usarla directamente; si es externa, usar Google Docs Viewer
const urlIframePdf = computed(() => {
  const url = urlVisor.value
  if (!url) return ''
  // Si es URL de Drive, usar Google Docs Viewer para mejor experiencia
  if (url.includes('drive.google.com') || url.includes('docs.google.com')) {
    return `https://docs.google.com/gview?url=${encodeURIComponent(url)}&embedded=true`
  }
  // Si es una URL relativa o del servidor local, usarla directamente en iframe
  return url
})

const etiquetaTipo = computed(() => {
  const tipos = {
    pdf: 'Documento PDF',
    imagen: 'Imagen',
    office: 'Documento Office (Word / Excel)',
    otro: 'Archivo adjunto',
  }
  return tipos[tipoArchivo.value] || 'Archivo'
})

const iconoBg = computed(() => {
  const colores = {
    pdf: 'bg-red-500',
    imagen: 'bg-emerald-500',
    office: 'bg-blue-500',
    otro: 'bg-slate-500',
  }
  return colores[tipoArchivo.value] || 'bg-slate-500'
})
</script>
