<template>
  <div class="page-shell animate-fade-in">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="eyebrow">Configuración institucional</p>
        <h1 class="page-title">Reglas por paso</h1>
        <p class="page-subtitle">Catálogo versionado para revisar antes de formalizar cada circuito.</p>
      </div>
      <button type="button" class="icon-btn" title="Actualizar" aria-label="Actualizar" :disabled="cargando" @click="cargar"><i :class="cargando ? 'pi pi-spin pi-spinner' : 'pi pi-refresh'"></i></button>
    </div>

    <p v-if="error" role="alert" class="mt-5 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-500/30 dark:bg-red-950/30 dark:text-red-200">{{ error }}</p>
    <section class="mt-5 grid gap-px overflow-hidden border border-slate-200 bg-slate-200 dark:border-slate-700 dark:bg-slate-700 sm:grid-cols-4">
      <div class="bg-white px-4 py-3 dark:bg-slate-900"><p class="text-[11px] font-semibold uppercase text-slate-500 dark:text-slate-400">Inicio</p><p class="mt-1 text-sm font-semibold text-slate-900 dark:text-white">Tramitador deriva</p></div>
      <div class="bg-white px-4 py-3 dark:bg-slate-900"><p class="text-[11px] font-semibold uppercase text-slate-500 dark:text-slate-400">Elaboración</p><p class="mt-1 text-sm font-semibold text-slate-900 dark:text-white">Secretaría prepara</p></div>
      <div class="bg-white px-4 py-3 dark:bg-slate-900"><p class="text-[11px] font-semibold uppercase text-slate-500 dark:text-slate-400">Emisión</p><p class="mt-1 text-sm font-semibold text-slate-900 dark:text-white">Dirección firma</p></div>
      <div class="bg-white px-4 py-3 dark:bg-slate-900"><p class="text-[11px] font-semibold uppercase text-slate-500 dark:text-slate-400">Cierre local</p><p class="mt-1 text-sm font-semibold text-slate-900 dark:text-white">Tramitador registra notificación</p></div>
    </section>
    <div class="mt-4 flex flex-wrap items-center gap-3 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-500/30 dark:bg-amber-950/25 dark:text-amber-200">
      <i class="pi pi-info-circle"></i><span>{{ resumenCatalogo }}. Las reglas pendientes no generan remisiones automáticas ni acciones externas.</span>
    </div>

    <div class="mt-5 overflow-x-auto border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
      <table class="data-table min-w-[980px]">
        <thead><tr><th>Paso</th><th>Estado</th><th>Origen</th><th>Resolución Dirección</th><th>Consulta previa</th><th>Participantes / aceptaciones</th><th>Destinatarios</th><th v-if="auth.isAdmin"></th></tr></thead>
        <tbody>
          <tr v-if="!cargando && reglas.length === 0"><td :colspan="auth.isAdmin ? 8 : 7" class="py-8 text-center text-slate-500">No hay reglas registradas.</td></tr>
          <tr v-for="regla in reglas" :key="regla.id_regla">
            <td><p class="font-semibold text-slate-900 dark:text-white">{{ regla.nombre_paso || `Paso ${regla.id_paso}` }}</p><p class="text-xs text-slate-500 dark:text-slate-400">v{{ regla.version }}</p></td>
            <td><span :class="regla.estado_validacion === 'Confirmada' ? 'badge-graduado' : 'badge-observado'">{{ etiquetaEstado(regla) }}</span><p class="mt-1 text-[11px] text-slate-500 dark:text-slate-400">{{ camposRegistrados(regla) }}/6 datos</p></td>
            <td>{{ regla.sistema_origen || 'Pendiente' }}</td>
            <td>{{ booleano(regla.requiere_resolucion_direccion) }}</td>
            <td>{{ booleano(regla.requiere_consulta_previa) }}</td>
            <td>{{ resumen(regla.tipos_participantes) }}<span v-if="regla.cantidad_aceptaciones !== null && regla.cantidad_aceptaciones !== undefined"> · {{ regla.cantidad_aceptaciones }}</span></td>
            <td>{{ resumen(regla.destinatarios_obligatorios) }}</td>
            <td v-if="auth.isAdmin"><button type="button" class="icon-btn" title="Editar regla" aria-label="Editar regla" @click="editar(regla)"><i class="pi pi-pencil"></i></button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="editando" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4" @click.self="editando = null">
      <form class="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl" @submit.prevent="guardar">
        <div class="flex items-start justify-between gap-4"><div><p class="eyebrow">Paso {{ editando.id_paso }}</p><h2 class="text-lg font-bold text-slate-950">{{ editando.nombre_paso }}</h2></div><button type="button" class="icon-btn" title="Cerrar" aria-label="Cerrar" @click="editando = null"><i class="pi pi-times"></i></button></div>
        <div class="mt-5 grid gap-4 sm:grid-cols-2">
          <label class="input-label">Estado<select v-model="form.estado_validacion" class="input-field mt-1"><option value="Pendiente_Validacion">Pendiente de validación</option><option value="Confirmada">Confirmada</option></select></label>
          <label class="input-label">Sistema de origen<input v-model="form.sistema_origen" class="input-field mt-1" placeholder="Pendiente de validación" /></label>
          <label class="input-label">¿Requiere resolución de Dirección?<select v-model="form.requiere_resolucion_direccion" class="input-field mt-1"><option value="">Pendiente</option><option value="true">Sí</option><option value="false">No</option></select></label>
          <label class="input-label">¿Requiere consulta previa?<select v-model="form.requiere_consulta_previa" class="input-field mt-1"><option value="">Pendiente</option><option value="true">Sí</option><option value="false">No</option></select></label>
          <label class="input-label">Tipos de participantes<input v-model="form.tipos_participantes" class="input-field mt-1" placeholder="Separados por coma" /></label>
          <label class="input-label">Cantidad de aceptaciones<input v-model="form.cantidad_aceptaciones" type="number" min="0" class="input-field mt-1" /></label>
          <label class="input-label sm:col-span-2">Destinatarios obligatorios<input v-model="form.destinatarios_obligatorios" class="input-field mt-1" placeholder="Separados por coma" /></label>
          <label class="input-label">Vigencia de resolución (meses)<input v-model="form.vigencia_meses" type="number" min="1" class="input-field mt-1" /></label>
          <label class="input-label">Plazo sugerido de consulta (días)<input v-model="form.plazo_consulta_dias" type="number" min="1" class="input-field mt-1" placeholder="Sin valor por ahora" /></label>
          <label class="input-label sm:col-span-2">Modalidades de respuesta<input v-model="form.modalidades_respuesta" class="input-field mt-1" placeholder="Respuesta, Documento, Constancia" /></label>
          <label class="input-label sm:col-span-2">Nota de validación<textarea v-model="form.nota_validacion" class="input-field mt-1 min-h-20" placeholder="Norma, oficio o acuerdo que sustenta esta regla"></textarea></label>
        </div>
        <p v-if="errorFormulario" class="mt-4 text-sm text-red-700">{{ errorFormulario }}</p>
        <div class="mt-6 flex justify-end gap-3"><button type="button" class="btn-ghost" @click="editando = null">Cancelar</button><button class="btn-primary" :disabled="guardando">{{ guardando ? 'Guardando...' : 'Guardar regla' }}</button></div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../api.js'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()
const reglas = ref([]); const cargando = ref(false); const error = ref('')
const editando = ref(null); const guardando = ref(false); const errorFormulario = ref('')
const form = ref({})
const resumen = (lista) => Array.isArray(lista) && lista.length ? lista.join(', ') : 'Pendiente'
const booleano = (valor) => valor === true ? 'Sí' : valor === false ? 'No' : 'Pendiente'
const etiquetaEstado = (regla) => regla.estado_validacion === 'Confirmada' ? 'Confirmada' : (camposRegistrados(regla) ? 'Parcial' : 'Pendiente')
const listaDesdeTexto = (valor) => valor.trim() ? valor.split(',').map(item => item.trim()).filter(Boolean) : null
const camposRegistrados = (regla) => [regla.sistema_origen, regla.requiere_resolucion_direccion, regla.requiere_consulta_previa, regla.tipos_participantes, regla.cantidad_aceptaciones, regla.destinatarios_obligatorios].filter(valor => valor !== null && valor !== undefined && valor !== '').length
const resumenCatalogo = computed(() => {
  const completos = reglas.value.filter(regla => regla.estado_validacion === 'Confirmada').length
  const parciales = reglas.value.filter(regla => camposRegistrados(regla) > 0 && regla.estado_validacion !== 'Confirmada').length
  return `${completos} reglas confirmadas y ${parciales} con información parcial registrada`
})

async function cargar() { cargando.value = true; error.value = ''; try { reglas.value = (await api.get('/reglas-resolucion')).data.data } catch (e) { error.value = e.response?.data?.detail || 'No se pudo cargar el catálogo.' } finally { cargando.value = false } }
function editar(regla) { editando.value = regla; errorFormulario.value = ''; form.value = { estado_validacion: regla.estado_validacion, sistema_origen: regla.sistema_origen || '', requiere_resolucion_direccion: regla.requiere_resolucion_direccion === null ? '' : String(regla.requiere_resolucion_direccion), requiere_consulta_previa: regla.requiere_consulta_previa === null ? '' : String(regla.requiere_consulta_previa), tipos_participantes: (regla.tipos_participantes || []).join(', '), cantidad_aceptaciones: regla.cantidad_aceptaciones ?? '', destinatarios_obligatorios: (regla.destinatarios_obligatorios || []).join(', '), vigencia_meses: regla.vigencia_meses ?? '', plazo_consulta_dias: regla.plazo_consulta_dias ?? '', modalidades_respuesta: (regla.modalidades_respuesta || []).join(', '), nota_validacion: regla.nota_validacion || '' } }
async function guardar() { guardando.value = true; errorFormulario.value = ''; const normalizarBooleano = valor => valor === '' ? null : valor === 'true'; const numeroOpcional = valor => valor === '' ? null : Number(valor); const datos = { ...form.value, requiere_resolucion_direccion: normalizarBooleano(form.value.requiere_resolucion_direccion), requiere_consulta_previa: normalizarBooleano(form.value.requiere_consulta_previa), tipos_participantes: listaDesdeTexto(form.value.tipos_participantes), destinatarios_obligatorios: listaDesdeTexto(form.value.destinatarios_obligatorios), modalidades_respuesta: listaDesdeTexto(form.value.modalidades_respuesta), cantidad_aceptaciones: numeroOpcional(form.value.cantidad_aceptaciones), vigencia_meses: numeroOpcional(form.value.vigencia_meses), plazo_consulta_dias: numeroOpcional(form.value.plazo_consulta_dias) }; try { await api.put(`/reglas-resolucion/${editando.value.id_paso}`, datos); editando.value = null; await cargar() } catch (e) { errorFormulario.value = e.response?.data?.detail || 'No se pudo guardar la regla.' } finally { guardando.value = false } }
onMounted(cargar)
</script>
