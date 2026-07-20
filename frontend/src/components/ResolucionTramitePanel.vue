<template>
  <section class="card">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <p class="eyebrow">Circuito institucional</p>
        <h3 class="text-base font-semibold text-white">Trámite de resolución</h3>
        <p class="mt-1 text-xs text-slate-400">Tramitación valida requisitos y deriva; Secretaría prepara el Word; Dirección firma; Tramitación registra la constancia final.</p>
      </div>
      <router-link v-if="auth.isSecretaria || auth.isAdmin" to="/secretaria" class="btn-outline btn-sm">
        <i class="pi pi-file-edit"></i> Abrir Secretaría
      </router-link>
      <router-link v-else-if="auth.isDirectora" to="/directora" class="btn-outline btn-sm">
        <i class="pi pi-shield"></i> Abrir Dirección
      </router-link>
    </div>

    <div v-if="mensaje" :class="['mt-4 rounded-md border px-3 py-2 text-xs', error ? 'border-red-500/30 bg-red-950/30 text-red-200' : 'border-emerald-500/30 bg-emerald-950/30 text-emerald-200']">
      {{ mensaje }}
    </div>

    <form v-if="puedeDerivar" class="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2" @submit.prevent="derivar">
      <div>
        <label for="tipo-resolucion" class="input-label">Tipo de resolución</label>
        <input id="tipo-resolucion" v-model="derivacion.tipo_resolucion" class="input-field" required placeholder="Ej. Inscripción de proyecto de tesis" />
      </div>
      <div>
        <label for="ticket-resolucion" class="input-label">Ticket que origina el trámite</label>
        <select id="ticket-resolucion" v-model="derivacion.ticket_id" class="input-field">
          <option value="">Sin ticket específico</option>
          <option v-for="ticket in expediente.tickets" :key="ticket.ticket_id" :value="ticket.ticket_id">#{{ ticket.numero_visual }} · {{ ticket.asunto }}</option>
        </select>
      </div>
      <div v-if="expediente.id_paso_actual === 4" class="md:col-span-2">
        <label for="referencia-erp" class="input-label">Referencia ERP</label>
        <input id="referencia-erp" v-model="derivacion.referencia_origen" class="input-field" placeholder="Código o referencia del registro ERP" />
        <p class="mt-1 text-[11px] text-slate-500">El paso 4 se origina en ERP, pero la resolución igualmente pasa por Dirección.</p>
      </div>
      <div class="md:col-span-2 flex justify-end">
        <button class="btn-primary" :disabled="procesando || !derivacion.tipo_resolucion.trim()">
          <i :class="procesando ? 'pi pi-spin pi-spinner' : 'pi pi-send'"></i>
          {{ tramiteActivo?.estado === 'observado_tramitador' ? 'Subsanar y devolver a Secretaría' : 'Derivar a Secretaría' }}
        </button>
      </div>
    </form>

    <div v-if="tramites.length" class="mt-5 space-y-3">
      <article v-for="tramite in tramites" :key="tramite.uuid" class="rounded-md border border-slate-700 bg-slate-900/40 p-4">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="font-semibold text-white">{{ tramite.numero_resolucion || 'Sin número asignado' }}</p>
            <p class="mt-0.5 text-xs text-slate-300">{{ tramite.tipo_resolucion }} · Paso {{ tramite.id_paso }}</p>
            <p class="mt-1 text-[11px] text-slate-500">{{ tramite.sistema_origen }}<span v-if="tramite.referencia_origen"> · {{ tramite.referencia_origen }}</span></p>
          </div>
          <span :class="badgeEstado(tramite.estado)">{{ etiquetaEstado(tramite) }}</span>
        </div>
        <p v-if="tramite.observacion_actual" class="mt-3 rounded-md border border-amber-500/30 bg-amber-950/30 px-3 py-2 text-xs text-amber-200">{{ tramite.observacion_actual }}</p>
        <div class="mt-3 flex flex-wrap gap-2 text-xs">
          <a v-if="tramite.borrador_word_url" :href="tramite.borrador_word_url" target="_blank" rel="noopener" class="btn-ghost btn-sm"><i class="pi pi-file-word"></i> Word v{{ tramite.borrador_version }}</a>
          <a v-if="tramite.pdf_firmado_url" :href="tramite.pdf_firmado_url" target="_blank" rel="noopener" class="btn-ghost btn-sm"><i class="pi pi-file-pdf"></i> PDF firmado</a>
          <span v-if="tramite.requiere_consulta_previa" class="badge-proceso">Consulta: {{ tramite.consultas_resumen.aceptadas }} aceptada(s), {{ tramite.consultas_resumen.pendientes }} pendiente(s)</span>
        </div>

        <div v-if="puedeNotificar(tramite)" class="mt-4 border-t border-slate-700 pt-4">
          <p class="text-xs font-semibold text-white">Destinatarios de esta resolución</p>
          <p v-if="tramite.notificaciones_resumen?.tipos_faltantes?.length" class="mt-1 text-xs text-amber-300">Falta confirmar: {{ tramite.notificaciones_resumen.tipos_faltantes.join(', ') }}</p>
          <div class="mt-2 grid grid-cols-1 gap-2 md:grid-cols-4">
            <select v-model="notificacion.destinatario_tipo" class="input-field text-xs">
              <option>Estudiante</option><option>Asesor</option><option>Dictaminante</option><option>Replicante</option><option>Otro</option>
            </select>
            <input v-model="notificacion.destinatario_nombre" class="input-field text-xs md:col-span-2" placeholder="Nombre del destinatario" />
            <select v-model="notificacion.canal" class="input-field text-xs"><option>osTicket</option><option>Correo</option><option>Presencial</option><option>Otro</option></select>
            <input v-model="notificacion.destinatario_referencia" class="input-field text-xs md:col-span-3" placeholder="Correo, ticket u otra referencia" />
            <button type="button" class="btn-outline btn-sm justify-center" :disabled="procesando || !notificacion.destinatario_nombre.trim()" @click="agregarDestinatario(tramite)"><i class="pi pi-plus"></i> Agregar</button>
          </div>
          <div v-if="tramite.notificaciones?.length" class="mt-3 space-y-2">
            <div v-for="item in tramite.notificaciones" :key="item.id_notificacion" class="grid grid-cols-1 items-center gap-2 rounded-md bg-slate-800/60 p-2.5 md:grid-cols-[minmax(0,1fr)_minmax(180px,1fr)_auto]">
              <div class="min-w-0">
                <p class="truncate text-xs font-medium text-white">{{ item.destinatario_tipo }} · {{ item.destinatario_nombre }}</p>
                <p class="text-[11px] text-slate-500">{{ item.canal }}<span v-if="item.destinatario_referencia"> · {{ item.destinatario_referencia }}</span></p>
              </div>
              <input v-if="item.estado !== 'Confirmada'" v-model="evidencias[item.id_notificacion]" class="input-field text-xs" placeholder="Constancia o evidencia" />
              <span v-else class="text-xs text-emerald-300">Confirmada · {{ item.evidencia }}</span>
              <button v-if="item.estado !== 'Confirmada'" type="button" class="btn-success btn-sm" :disabled="procesando || !(evidencias[item.id_notificacion] || '').trim()" @click="confirmarNotificacion(tramite, item)"><i class="pi pi-check"></i> Confirmar</button>
              <span v-else class="badge-graduado">Notificado</span>
            </div>
          </div>
          <p class="mt-2 text-[11px] text-slate-500">Registrar aquí no envía mensajes automáticamente. Confirma solo después de efectuar la notificación por el canal indicado.</p>
        </div>
      </article>
    </div>
    <p v-else class="mt-4 text-xs text-slate-500">Todavía no hay un trámite de resolución para este expediente.</p>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import api from '../api.js'

const props = defineProps({ expediente: { type: Object, required: true } })
const emit = defineEmits(['actualizado'])
const auth = useAuthStore()
const route = useRoute()
const procesando = ref(false)
const mensaje = ref('')
const error = ref(false)
const evidencias = reactive({})
const derivacion = reactive({ tipo_resolucion: '', ticket_id: '', referencia_origen: '' })
const notificacion = reactive({ destinatario_tipo: 'Estudiante', destinatario_nombre: '', destinatario_referencia: '', canal: 'osTicket' })

const tramites = computed(() => props.expediente.tramites_resolucion || [])
const tramiteActivo = computed(() => tramites.value.find(item => item.estado !== 'notificado_confirmado'))
const puedeDerivar = computed(() => (auth.rol === 'Recepcion' || auth.isAdmin) && (!tramiteActivo.value || tramiteActivo.value.estado === 'observado_tramitador'))

watch(() => [props.expediente?.uuid, route.query.ticket], () => {
  if (!derivacion.tipo_resolucion && props.expediente?.nombre_paso_actual) {
    derivacion.tipo_resolucion = props.expediente.nombre_paso_actual
  }
  if (!derivacion.ticket_id && route.query.ticket) {
    const ticket = props.expediente?.tickets?.find(item => String(item.ticket_id) === String(route.query.ticket))
    if (ticket) derivacion.ticket_id = ticket.ticket_id
  }
}, { immediate: true })

function etiquetaEstado(tramite) {
  const estado = tramite.estado
  if (tramite.id_paso === 7 && estado === 'notificado_confirmado') return 'Concluido'
  return ({
    derivado_secretaria: 'En revisión de Secretaría', observado_tramitador: 'Requiere subsanación', en_elaboracion_secretaria: 'En elaboración',
    consulta_previa: 'Consultando disponibilidad', listo_para_direccion: 'Pendiente de Dirección', observado_por_direccion: 'Observado por Dirección',
    devuelto_tramitador: 'Firmado, por notificar', pendiente_notificacion: 'Notificación en curso', notificado_confirmado: 'Notificado',
  })[estado] || estado
}

function badgeEstado(estado) {
  if (estado === 'notificado_confirmado') return 'badge-graduado'
  if (estado.includes('observado')) return 'badge-error'
  if (estado === 'devuelto_tramitador' || estado === 'pendiente_notificacion') return 'badge-observado'
  return 'badge-proceso'
}

function puedeNotificar(tramite) {
  return (auth.rol === 'Recepcion' || auth.isAdmin) && ['devuelto_tramitador', 'pendiente_notificacion'].includes(tramite.estado)
}

async function ejecutar(accion, exito) {
  procesando.value = true
  mensaje.value = ''
  try {
    await accion()
    error.value = false
    mensaje.value = exito
    emit('actualizado')
  } catch (e) {
    error.value = true
    mensaje.value = e.response?.data?.detail || 'No se pudo completar la acción.'
  } finally {
    procesando.value = false
  }
}

function derivar() {
  ejecutar(() => api.post(`/expedientes/${props.expediente.uuid}/resolucion-tramites`, {
    tipo_resolucion: derivacion.tipo_resolucion,
    ticket_id: derivacion.ticket_id || null,
    referencia_origen: derivacion.referencia_origen || null,
  }), 'El trámite quedó en la bandeja de Secretaría Académica.')
}

function agregarDestinatario(tramite) {
  ejecutar(() => api.post(`/resolucion-tramites/${tramite.uuid}/notificaciones`, { ...notificacion }), 'Destinatario agregado; queda pendiente confirmar la notificación.')
}

function confirmarNotificacion(tramite, item) {
  ejecutar(() => api.post(`/resolucion-tramites/${tramite.uuid}/notificaciones/${item.id_notificacion}/confirmar`, {
    evidencia: evidencias[item.id_notificacion],
  }), 'Constancia registrada correctamente.')
}
</script>
