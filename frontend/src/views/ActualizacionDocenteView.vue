<template>
  <main class="min-h-screen bg-slate-100 p-4 dark:bg-slate-950 md:p-8">
    <section class="mx-auto max-w-4xl rounded-md border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <header class="border-b border-slate-200 pb-5 dark:border-slate-700">
        <p class="eyebrow">Universidad Andina del Cusco · EPG</p>
        <h1 class="mt-1 text-2xl font-bold text-slate-950 dark:text-white">Actualización de ficha docente</h1>
        <p class="mt-2 text-sm text-slate-600 dark:text-slate-300">Actualiza tus datos y adjunta la evidencia. Coordinación revisará cada cambio antes de incorporarlo.</p>
      </header>

      <div v-if="cargando" class="py-14 text-center text-slate-500">Validando enlace...</div>
      <div v-else-if="error" class="mt-5 rounded border border-red-300 bg-red-50 p-4 text-sm text-red-800 dark:bg-red-950/30 dark:text-red-200">{{ error }}</div>
      <div v-else-if="enviado" class="mt-5 rounded border border-emerald-300 bg-emerald-50 p-5 text-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100">
        <strong>Información recibida</strong><p class="mt-1 text-sm">Tus datos y documentos quedaron en la mesa de revisión de Coordinación EPG.</p>
      </div>

      <form v-else class="mt-5 space-y-6" @submit.prevent="enviar">
        <div><p class="input-label">Docente</p><p class="font-semibold text-slate-950 dark:text-white">{{ ficha.docente }}</p><p class="text-xs text-slate-500">Enlace vigente hasta {{ fecha(ficha.fecha_expiracion) }}</p></div>
        <section>
          <h2 class="font-semibold text-slate-950 dark:text-white">Datos de contacto y formación</h2>
          <div class="mt-3 grid gap-4 md:grid-cols-2">
            <label><span class="input-label">DNI</span><input v-model="form.dni" inputmode="numeric" maxlength="8" class="input-field mt-1" /></label>
            <label><span class="input-label">Teléfono</span><input v-model="form.telefono" class="input-field mt-1" /></label>
            <label><span class="input-label">Correo institucional</span><input v-model="form.correo_institucional" type="email" class="input-field mt-1" /></label>
            <label><span class="input-label">Correo personal</span><input v-model="form.correo_personal" type="email" class="input-field mt-1" /></label>
            <label><span class="input-label">Título profesional</span><input v-model="form.titulo_profesional" class="input-field mt-1" /></label>
            <label><span class="input-label">Especialidad principal</span><input v-model="form.especialidad" class="input-field mt-1" /></label>
          </div>
          <label class="mt-4 block"><span class="input-label">Universidad de procedencia</span><input v-model="form.universidad_procedencia" class="input-field mt-1" /></label>
          <label class="mt-4 block"><span class="input-label">Dirección</span><input v-model="form.direccion" class="input-field mt-1" /></label>
        </section>

        <section class="rounded-md border border-slate-200 p-4 dark:border-slate-700">
          <div class="flex flex-wrap items-center justify-between gap-3"><div><h2 class="font-semibold text-slate-950 dark:text-white">Documentos de respaldo</h2><p class="text-xs text-slate-500">Adjunta CV, ficha SUNEDU o constancias. El sistema propondrá datos; Coordinación decidirá cuáles validar.</p></div><select v-model="tipoDocumento" class="input-field w-44"><option>CV</option><option>SUNEDU</option><option>Constancia</option><option>Otro</option></select></div>
          <label :class="['mt-4 flex min-h-32 cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed p-5 text-center transition',arrastrando?'border-cyan-500 bg-cyan-50 dark:bg-cyan-950/30':'border-slate-300 hover:border-cyan-400 dark:border-slate-700']" @dragenter.prevent="arrastrando=true" @dragleave.prevent="arrastrando=false" @dragover.prevent @drop.prevent="soltar">
            <i class="pi pi-cloud-upload text-2xl text-cyan-600"></i><strong class="mt-2 text-sm">Arrastra archivos aquí o selecciónalos</strong><span class="mt-1 text-xs text-slate-500">PDF, Word, Excel o imagen · máximo 50 MB por archivo</span>
            <input type="file" multiple class="hidden" accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png" @change="seleccionar" />
          </label>
          <div v-if="subiendo" class="mt-3 text-xs text-cyan-700">Procesando documento y buscando datos...</div>
          <div class="mt-3 space-y-2">
            <article v-for="d in documentos" :key="d.uuid" class="rounded border border-slate-200 p-3 text-xs dark:border-slate-700"><div class="flex justify-between gap-3"><strong class="truncate">{{ d.nombre_archivo }}</strong><span class="badge-proceso">{{ d.estado_revision }}</span></div><p class="mt-1 text-slate-500">{{ d.tipo }} · {{ fecha(d.fecha_carga) }}</p><div v-if="Object.keys(d.datos_sugeridos||{}).length" class="mt-2 flex flex-wrap gap-1"><span v-for="(valor,campo) in d.datos_sugeridos" :key="campo" class="badge">{{ etiqueta(campo) }}: {{ resumenValor(valor) }}</span></div></article>
          </div>
        </section>

        <label class="block"><span class="input-label">Nota para Coordinación</span><textarea v-model="form.nota" class="input-field mt-1 min-h-24" placeholder="Aclara cambios, grados o especialidades pendientes"></textarea></label>
        <div class="flex justify-end"><button class="btn-primary" :disabled="guardando||subiendo"><i class="pi pi-send"></i>{{ guardando?'Enviando...':'Enviar para revisión' }}</button></div>
      </form>
    </section>
  </main>
</template>

<script setup>
import {onMounted,reactive,ref} from 'vue';import {useRoute} from 'vue-router';import api from '../api.js'
const route=useRoute(),cargando=ref(true),guardando=ref(false),subiendo=ref(false),arrastrando=ref(false),enviado=ref(false),error=ref(''),ficha=ref({}),documentos=ref([]),tipoDocumento=ref('CV')
const form=reactive({dni:'',correo_institucional:'',correo_personal:'',telefono:'',direccion:'',especialidad:'',titulo_profesional:'',universidad_procedencia:'',nota:''})
onMounted(cargar)
async function cargar(){try{ficha.value=(await api.get(`/actualizacion-docente/${route.params.token}`)).data;documentos.value=ficha.value.documentos||[];for(const campo of Object.keys(form))form[campo]=ficha.value[campo]||''}catch(e){error.value=e.response?.data?.detail||'El enlace no es válido o ya venció.'}finally{cargando.value=false}}
function seleccionar(e){subir([...e.target.files]);e.target.value=''} function soltar(e){arrastrando.value=false;subir([...e.dataTransfer.files])}
async function subir(archivos){if(!archivos.length)return;subiendo.value=true;error.value='';try{for(const archivo of archivos){const data=new FormData();data.append('tipo',tipoDocumento.value);data.append('archivo',archivo);const r=(await api.post(`/actualizacion-docente/${route.params.token}/documentos`,data)).data;for(const [campo,valor] of Object.entries(r.datos_sugeridos||{})){if(campo in form&&!form[campo]&&typeof valor==='string')form[campo]=valor}}await cargar()}catch(e){error.value=e.response?.data?.detail||'No se pudo cargar uno de los documentos.'}finally{subiendo.value=false}}
async function enviar(){guardando.value=true;error.value='';try{await api.post(`/actualizacion-docente/${route.params.token}`,form);enviado.value=true}catch(e){error.value=e.response?.data?.detail||'No se pudo enviar la información.'}finally{guardando.value=false}}
function fecha(v){return v?new Date(v).toLocaleString('es-PE'):'-'} function etiqueta(v){return v.replaceAll('_',' ')} function resumenValor(v){return Array.isArray(v)?v.slice(0,2).join(' · '):String(v)}
</script>
