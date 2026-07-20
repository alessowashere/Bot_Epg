<template>
  <main class="min-h-screen bg-slate-950 px-4 py-10 text-slate-100">
    <section class="mx-auto max-w-2xl border-t-4 border-cyan-500 bg-slate-900 p-6 shadow-xl sm:p-8">
      <div class="flex items-center gap-3 border-b border-slate-700 pb-5">
        <img src="https://uandina.edu.pe/assets/logo-uandina-icono.svg" alt="UAC" class="h-12 w-12 object-contain" />
        <div><p class="text-xs font-semibold uppercase text-cyan-300">Escuela de Posgrado</p><h1 class="text-xl font-bold">Consulta de disponibilidad</h1></div>
      </div>
      <div v-if="cargando" class="py-14 text-center text-sm text-slate-400"><i class="pi pi-spin pi-spinner mr-2"></i>Verificando consulta</div>
      <div v-else-if="error" class="py-10 text-center"><i class="pi pi-exclamation-circle text-3xl text-red-300"></i><p class="mt-3 text-sm text-red-200">{{ error }}</p></div>
      <div v-else-if="datos" class="pt-6">
        <p class="text-sm text-slate-300">Docente</p><p class="font-semibold text-white">{{ datos.consulta.docente }}</p>
        <dl class="mt-5 grid grid-cols-1 gap-4 border-y border-slate-700 py-5 sm:grid-cols-2">
          <div><dt class="text-xs text-slate-500">Participación consultada</dt><dd class="mt-1 text-sm text-white">{{ datos.consulta.tipo_participacion }}</dd></div>
          <div><dt class="text-xs text-slate-500">Paso</dt><dd class="mt-1 text-sm text-white">{{ datos.tramite.paso }}</dd></div>
          <div><dt class="text-xs text-slate-500">Estudiante</dt><dd class="mt-1 text-sm text-white">{{ datos.tramite.estudiante }}</dd></div>
          <div><dt class="text-xs text-slate-500">Tipo de resolución</dt><dd class="mt-1 text-sm text-white">{{ datos.tramite.tipo_resolucion }}</dd></div>
          <div><dt class="text-xs text-slate-500">Enlace válido hasta</dt><dd class="mt-1 text-sm text-white">{{ fecha(datos.consulta.fecha_expiracion) }}</dd></div>
          <div><dt class="text-xs text-slate-500">Respuesta requerida</dt><dd class="mt-1 text-sm text-white">{{ datos.consulta.modalidad_respuesta }}</dd></div>
        </dl>
        <p v-if="datos.tramite.titulo_tesis" class="mt-5 text-sm leading-6 text-slate-300">{{ datos.tramite.titulo_tesis }}</p>
        <div v-if="datos.consulta.estado !== 'Pendiente'" class="mt-6 rounded-md border border-emerald-500/30 bg-emerald-950/30 p-4 text-sm text-emerald-200">La consulta ya fue respondida: <strong>{{ datos.consulta.estado }}</strong>.</div>
        <form v-else class="mt-6" @submit.prevent>
          <label for="nota-consulta" class="input-label">Comentario opcional</label>
          <textarea id="nota-consulta" v-model="nota" class="input-field mt-1 resize-none" rows="3" placeholder="Indique alguna precisión sobre su disponibilidad"></textarea>
          <div v-if="datos.consulta.modalidad_respuesta === 'Documento'" class="mt-4"><label for="evidencia-consulta" class="input-label">Documento de respuesta</label><input id="evidencia-consulta" type="file" accept=".pdf,.doc,.docx,application/pdf" class="input-field mt-1 text-xs" @change="archivo = $event.target.files?.[0] || null" /></div>
          <label v-if="datos.consulta.modalidad_respuesta === 'Constancia'" class="mt-4 flex items-start gap-2 text-xs text-slate-300"><input v-model="constancia" type="checkbox" class="mt-0.5 h-4 w-4 accent-cyan-500" /> Declaro que la respuesta registrada expresa mi disponibilidad. Esta constancia no sustituye una firma electrónica certificada.</label>
          <p class="mt-3 text-xs text-slate-500">Esta respuesta solo confirma disponibilidad. No constituye una designación.</p>
          <div class="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <button type="button" class="btn-success justify-center" :disabled="procesando || !puedeAceptar" @click="responder('Aceptar')"><i class="pi pi-check"></i> Tengo disponibilidad</button>
            <button type="button" class="btn-danger justify-center" :disabled="procesando" @click="responder('Rechazar')"><i class="pi pi-times"></i> No tengo disponibilidad</button>
          </div>
        </form>
      </div>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api.js'
const route = useRoute(); const datos = ref(null); const cargando = ref(true); const procesando = ref(false); const error = ref(''); const nota = ref(''); const archivo = ref(null); const constancia = ref(false)
const puedeAceptar = computed(() => {
  const modalidad = datos.value?.consulta.modalidad_respuesta
  if (modalidad === 'Documento') return Boolean(archivo.value)
  if (modalidad === 'Constancia') return constancia.value
  return true
})
function fecha(valor) { return valor ? new Date(valor).toLocaleString('es-PE', { dateStyle: 'medium', timeStyle: 'short' }) : 'No definida' }
async function cargar() { try { const res = await api.get(`/consultas-resolucion/${route.params.token}`); datos.value = res.data } catch (e) { error.value = e.response?.data?.detail || 'No se pudo abrir la consulta.' } finally { cargando.value = false } }
async function responder(respuesta) { procesando.value = true; try { const form = new FormData(); form.append('respuesta', respuesta); if (nota.value) form.append('nota', nota.value); form.append('constancia_aceptada', constancia.value); if (archivo.value) form.append('archivo', archivo.value); await api.post(`/consultas-resolucion/${route.params.token}/responder-con-evidencia`, form); await cargar() } catch (e) { error.value = e.response?.data?.detail || 'No se pudo registrar la respuesta.' } finally { procesando.value = false } }
onMounted(cargar)
</script>
