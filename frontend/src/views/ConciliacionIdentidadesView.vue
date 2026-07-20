<template>
  <main class="min-h-full bg-slate-50 px-4 py-5 text-slate-900 dark:bg-[#070d1b] dark:text-slate-100 sm:px-6">
    <section class="mx-auto max-w-[1600px] space-y-4">
      <header class="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p class="text-xs font-bold uppercase tracking-wide text-cyan-700 dark:text-cyan-300">Administración</p>
          <h1 class="mt-1 text-2xl font-bold">Resolución de problemas</h1>
          <p class="mt-1 text-sm text-slate-600 dark:text-slate-400">{{ textoCabecera }}</p>
        </div>
        <button class="icon-btn h-10 w-10 border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-900" title="Actualizar" @click="cargar"><i :class="cargando ? 'pi pi-spin pi-spinner' : 'pi pi-refresh'" class="pi"></i></button>
      </header>

      <div class="flex flex-wrap gap-2 border-b border-slate-200 pb-3 dark:border-slate-800">
        <button v-for="item in tipos" :key="item.id" type="button" class="flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-semibold" :class="tipo === item.id ? 'border-cyan-500 bg-cyan-50 text-cyan-900 dark:bg-cyan-950/40 dark:text-cyan-100' : 'border-slate-300 bg-white text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300'" @click="cambiarTipo(item.id)">
          <i :class="item.icon" class="pi"></i>{{ item.label }} <span v-if="tipo === item.id" class="min-w-6 rounded bg-slate-200 px-1.5 py-0.5 text-center text-xs dark:bg-slate-800">{{ contadorTipo }}</span>
        </button>
      </div>
      <div v-if="tipo === 'ticket'" class="flex gap-1 rounded-md bg-slate-100 p-1 dark:bg-slate-800">
        <button type="button" class="rounded px-3 py-1.5 text-xs font-semibold" :class="modoTicket === 'identidad' ? 'bg-white text-slate-950 shadow-sm dark:bg-slate-950 dark:text-white' : 'text-slate-500'" @click="cambiarModoTicket('identidad')">Conflictos de identidad</button>
        <button type="button" class="rounded px-3 py-1.5 text-xs font-semibold" :class="modoTicket === 'operativo' ? 'bg-white text-slate-950 shadow-sm dark:bg-slate-950 dark:text-white' : 'text-slate-500'" @click="cambiarModoTicket('operativo')">Clasificar destino</button>
      </div>
      <div v-if="tipo === 'ticket' && modoTicket === 'operativo'" class="flex gap-1 rounded-md bg-slate-100 p-1 dark:bg-slate-800">
        <button v-for="cola in colasOperativas" :key="cola.id" type="button" class="rounded px-3 py-1.5 text-xs font-semibold" :class="colaOperativa === cola.id ? 'bg-white text-slate-950 shadow-sm dark:bg-slate-950 dark:text-white' : 'text-slate-500'" @click="cambiarColaOperativa(cola.id)">{{ cola.label }}</button>
      </div>

      <section class="grid min-h-[calc(100vh-225px)] gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
        <aside class="overflow-hidden rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <div class="space-y-3 border-b border-slate-200 p-3 dark:border-slate-800">
            <div v-if="estadosVisibles.length" class="flex gap-1 rounded-md bg-slate-100 p-1 dark:bg-slate-800">
              <button v-for="estado in estadosVisibles" :key="estado.id" type="button" class="flex-1 rounded px-2 py-1.5 text-xs font-semibold" :class="filtroEstado === estado.id ? 'bg-white text-slate-950 shadow-sm dark:bg-slate-950 dark:text-white' : 'text-slate-500'" @click="filtroEstado = estado.id; cargar()">{{ estado.label }}</button>
            </div>
            <label class="relative block"><i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-xs text-slate-400"></i><input v-model="busqueda" class="w-full rounded-md border border-slate-300 bg-white py-2 pl-8 pr-3 text-sm dark:border-slate-700 dark:bg-slate-950" placeholder="Buscar persona o código" @keyup.enter="cargar" /></label>
          </div>
          <div class="max-h-[calc(100vh-390px)] min-h-[480px] overflow-y-auto">
            <button v-for="caso in casos" :key="caso.referencia" type="button" class="w-full border-b border-slate-100 px-3 py-3 text-left hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800" :class="seleccion?.referencia === caso.referencia ? 'border-l-4 border-l-cyan-500 bg-cyan-50 dark:bg-cyan-950/30' : ''" @click="seleccion = caso">
              <p class="truncate text-sm font-bold">{{ tituloCaso(caso) }}</p>
              <p class="mt-1 truncate text-xs text-slate-500 dark:text-slate-400">{{ resumenCaso(caso) }}</p>
              <div class="mt-2 flex gap-1"><span class="rounded px-1.5 py-0.5 text-[10px] font-bold" :class="claseEstadoCaso(caso)">{{ textoEstadoCaso(caso) }}</span><span v-if="caso.trayectorias?.length" class="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300">{{ caso.trayectorias.length }} coincidencia{{ caso.trayectorias.length === 1 ? '' : 's' }}</span></div>
            </button>
            <p v-if="!cargando && !casos.length" class="p-10 text-center text-sm text-slate-500">Sin casos para este filtro.</p>
          </div>
        </aside>

        <section v-if="seleccion" class="space-y-4">
          <article v-if="tipo === 'duplicado'" class="rounded-lg border border-cyan-300 bg-cyan-50 p-4 dark:border-cyan-900 dark:bg-cyan-950/20">
            <div class="flex flex-wrap items-start justify-between gap-3"><div><p class="text-xs font-bold uppercase tracking-wide text-cyan-800 dark:text-cyan-200">Decisión prioritaria</p><h3 class="mt-1 text-base font-bold">¿Cuál será el expediente principal?</h3><p class="mt-1 text-sm text-slate-600 dark:text-slate-300">Los dos usan matrículas distintas. Revisa título, resoluciones y tickets abajo antes de confirmar.</p></div><span class="rounded bg-white px-2 py-1 text-xs font-bold text-cyan-800 shadow-sm dark:bg-slate-900 dark:text-cyan-200">{{ seleccion.duplicados?.length || 0 }} expedientes</span></div>
            <div class="mt-4 grid gap-2 sm:grid-cols-3"><button class="decision-primary" :disabled="!claveSeleccionada || guardando" @click="guardar('preparar_unificacion')">Unificar en el principal elegido</button><button class="decision-secondary" :disabled="guardando" @click="guardar('mantener_separados')">Mantener separados</button><button class="decision-secondary" :disabled="guardando" @click="guardar('pendiente')">Revisar después</button></div>
            <textarea v-model="nota" rows="2" class="mt-3 w-full rounded-md border border-slate-300 bg-white p-2 text-sm dark:border-slate-700 dark:bg-slate-950" placeholder="Motivo o evidencia de la decisión (opcional)"></textarea>
          </article>
          <div class="grid gap-4 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
            <article class="rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
              <p class="text-xs font-bold uppercase tracking-wide text-slate-500">{{ tipo === 'ticket' ? 'Solicitud original' : 'Expediente actual' }}</p>
              <h2 class="mt-2 text-lg font-bold">{{ tituloCaso(seleccion) }}</h2>
              <dl class="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                <template v-for="campo in datosOrigen" :key="campo[0]"><div><dt class="text-[10px] font-bold uppercase tracking-wide text-slate-500">{{ etiqueta(campo[0]) }}</dt><dd class="mt-0.5 break-words font-medium">{{ valorCampo(campo[0], campo[1]) }}</dd></div></template>
              </dl>
              <div class="mt-5 rounded-md border border-sky-200 bg-sky-50 p-3 text-sm leading-5 text-sky-950 dark:border-sky-900 dark:bg-sky-950/25 dark:text-sky-100"><p class="text-[10px] font-bold uppercase tracking-wide text-sky-700 dark:text-sky-300">Por qué aparece aquí</p><p class="mt-1">{{ explicacionCaso }}</p></div>
              <div v-if="seleccion.origen?.resoluciones_vinculadas?.length" class="mt-5 border-t border-slate-200 pt-4 dark:border-slate-800"><p class="text-xs font-bold uppercase tracking-wide text-slate-500">Resoluciones vinculadas al expediente</p><p class="mt-1 text-xs text-slate-500">Historial existente: no implica que todas correspondan a la trayectoria candidata.</p><div class="mt-2 max-h-52 divide-y divide-slate-100 overflow-y-auto dark:divide-slate-800"><div v-for="resolucion in seleccion.origen.resoluciones_vinculadas" :key="resolucion.id_resolucion" class="flex items-center justify-between gap-2 py-2 text-xs"><span class="min-w-0"><strong>P{{ resolucion.paso || '?' }}</strong> · {{ resolucion.tipo }} · {{ resolucion.fecha || 'sin fecha' }}<span class="block truncate text-slate-500">{{ resolucion.archivo }}</span></span><button v-if="resolucion.disponible" type="button" class="icon-btn h-7 w-7 shrink-0 border-slate-300 dark:border-slate-700" title="Abrir archivo histórico" @click="abrirResolucionHistorica(resolucion.id_resolucion)"><i class="pi pi-external-link text-xs"></i></button></div></div></div>
              <div v-if="seleccion.origen?.cuerpo !== undefined" class="mt-5 border-t border-slate-200 pt-4 dark:border-slate-800"><p class="text-xs font-bold uppercase tracking-wide text-slate-500">Mensaje recibido</p><p class="mt-2 max-h-48 overflow-y-auto whitespace-pre-wrap text-sm leading-6 text-slate-700 dark:text-slate-300">{{ seleccion.origen.cuerpo || 'Sin cuerpo disponible' }}</p><div v-if="seleccion.origen.adjuntos?.length" class="mt-3 flex flex-wrap gap-2"><span v-for="adjunto in seleccion.origen.adjuntos" :key="adjunto" class="max-w-full truncate rounded bg-slate-100 px-2 py-1 text-xs dark:bg-slate-800"><i class="pi pi-paperclip mr-1"></i>{{ adjunto }}</span></div></div>
            </article>

            <article class="rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
              <div class="flex items-center justify-between"><div><p class="text-xs font-bold uppercase tracking-wide text-cyan-700 dark:text-cyan-300">{{ tipo === 'duplicado' ? 'Registros coincidentes' : 'Resoluciones encontradas' }}</p><h3 class="mt-1 text-lg font-bold">{{ tipo === 'duplicado' ? 'Expedientes a consolidar' : 'Posibles trayectorias' }}</h3></div><span class="rounded bg-cyan-100 px-2 py-1 text-xs font-bold text-cyan-900 dark:bg-cyan-950 dark:text-cyan-200">{{ tipo === 'duplicado' ? (seleccion.duplicados?.length || 0) : (seleccion.trayectorias?.length || 0) }}</span></div>
              <div v-if="tipo === 'duplicado'" class="mt-4 space-y-3">
                <p class="text-sm text-slate-600 dark:text-slate-300">Compara la evidencia de ambos expedientes y marca el principal. La unificación sigue siendo una operación posterior y auditada.</p>
                <article v-for="expediente in seleccion.duplicados" :key="expediente.id_expediente" class="rounded-md border p-3" :class="claveSeleccionada === `expediente:${expediente.id_expediente}` ? 'border-cyan-500 bg-cyan-50 dark:bg-cyan-950/30' : 'border-slate-200 dark:border-slate-700'">
                  <div class="flex flex-wrap items-start justify-between gap-2">
                    <div><p class="font-bold">Expediente #{{ expediente.id_expediente }}</p><p class="mt-0.5 text-xs text-slate-500">{{ expediente.codigo || 'Sin código de matrícula válido' }} · {{ expediente.estado || 'Sin estado' }} · P{{ expediente.paso || '?' }}</p><p class="mt-1 text-xs font-medium text-slate-700 dark:text-slate-200">{{ expediente.grado || 'Sin grado' }} · {{ expediente.programa || 'Sin programa' }}</p></div>
                    <button type="button" class="decision-secondary !min-h-0 !py-1.5 text-xs" :class="claveSeleccionada === `expediente:${expediente.id_expediente}` ? '!border-cyan-500 !bg-cyan-100 dark:!bg-cyan-950' : ''" @click="claveSeleccionada = `expediente:${expediente.id_expediente}`">{{ claveSeleccionada === `expediente:${expediente.id_expediente}` ? 'Principal elegido' : 'Elegir principal' }}</button>
                  </div>
                  <p v-if="expediente.codigo_invalido" class="mt-2 text-xs font-medium text-amber-700 dark:text-amber-300">Dato descartado: {{ expediente.codigo_invalido }} no tiene formato de código de matrícula.</p>
                  <p class="mt-3 text-xs font-bold uppercase tracking-wide text-slate-500">Título de tesis</p><p class="mt-1 text-sm leading-5">{{ expediente.titulo || 'Sin título registrado' }}</p>
                  <div class="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-600 dark:text-slate-300"><span>Inicio: <strong>{{ expediente.fecha_inicio || 'sin fecha' }}</strong></span><span>Último movimiento: <strong>{{ expediente.fecha_ultimo_movimiento || 'sin fecha' }}</strong></span></div>
                  <div class="mt-3 grid grid-cols-3 gap-2 border-y border-slate-200 py-2 text-xs dark:border-slate-700"><span><strong>{{ expediente.resoluciones }}</strong><br>resoluciones</span><span><strong>{{ expediente.tickets }}</strong><br>tickets</span><span><strong>{{ expediente.requisitos }}</strong><br>requisitos</span></div>
                  <p v-if="Object.keys(expediente.requisitos_estado || {}).length" class="mt-2 text-xs text-slate-500">Requisitos: <span v-for="(cantidad, estado) in expediente.requisitos_estado" :key="estado" class="mr-2"><strong>{{ cantidad }}</strong> {{ estado }}</span></p>
                  <div v-if="expediente.resoluciones_detalle?.length" class="mt-3"><p class="text-xs font-bold uppercase tracking-wide text-slate-500">Resoluciones del expediente</p><div class="mt-1 max-h-40 divide-y divide-slate-200 overflow-y-auto dark:divide-slate-700"><div v-for="resolucion in expediente.resoluciones_detalle" :key="resolucion.id_resolucion" class="flex items-center justify-between gap-2 py-1.5 text-xs"><span class="min-w-0"><strong>P{{ resolucion.paso || '?' }}</strong> · {{ resolucion.fecha || 'sin fecha' }}<span class="block truncate text-slate-500">{{ resolucion.archivo }}</span></span><button v-if="resolucion.disponible" type="button" class="icon-btn h-7 w-7 shrink-0 border-slate-300 dark:border-slate-700" title="Abrir resolución" @click="abrirResolucionHistorica(resolucion.id_resolucion)"><i class="pi pi-external-link text-xs"></i></button></div></div></div>
                  <div v-if="expediente.tickets_detalle?.length" class="mt-3"><p class="text-xs font-bold uppercase tracking-wide text-slate-500">Tickets vinculados</p><div class="mt-1 max-h-24 divide-y divide-slate-200 overflow-y-auto dark:divide-slate-700"><div v-for="ticket in expediente.tickets_detalle" :key="ticket.ticket_id" class="py-1.5 text-xs"><strong>#{{ ticket.numero_visual }}</strong> · {{ ticket.estado }}<span class="block truncate text-slate-500">{{ ticket.asunto }}</span></div></div></div>
                </article>
              </div>
              <div v-else-if="seleccion.trayectorias?.length" class="mt-4 space-y-3">
                <p v-if="trayectoriasConGradoDistinto" class="rounded-md border border-amber-300 bg-amber-50 p-3 text-xs leading-5 text-amber-950 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100">Estas trayectorias no se unifican: corresponden a grados académicos distintos (por ejemplo, Maestría y Doctorado), aunque la persona y el programa coincidan.</p>
                <button v-for="trayectoria in seleccion.trayectorias" :key="trayectoria.clave" type="button" class="w-full rounded-md border p-3 text-left" :class="claveSeleccionada === trayectoria.clave ? 'border-cyan-500 bg-cyan-50 dark:bg-cyan-950/30' : 'border-slate-200 dark:border-slate-700'" @click="claveSeleccionada = trayectoria.clave">
                  <p class="text-sm font-bold">{{ nombreTrayectoria(trayectoria.clave) }}</p><p class="mt-1 text-xs text-slate-500">{{ descripcionTrayectoria(trayectoria.clave) }}</p>
                  <div class="mt-3 space-y-2"><div v-for="(documento, indice) in trayectoria.documentos.slice(0, 4)" :key="documento.id_documento" class="flex items-center justify-between gap-2 border-t border-slate-100 pt-2 text-xs dark:border-slate-800"><span class="min-w-0"><span v-if="indice === 0" class="mr-1 rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-bold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200">Más reciente</span><strong>{{ documento.resolucion }}</strong> · P{{ documento.paso || '?' }} · {{ documento.fecha || 'sin fecha' }}<span class="block truncate text-slate-500">{{ documento.archivo }}</span></span><button type="button" class="icon-btn h-7 w-7 shrink-0 border-slate-300 dark:border-slate-700" title="Abrir PDF" @click.stop="abrirPdf(documento.id_documento)"><i class="pi pi-external-link text-xs"></i></button></div><p v-if="trayectoria.documentos.length > 4" class="pt-1 text-xs text-slate-500">{{ trayectoria.documentos.length - 4 }} resoluciones anteriores conservadas en este mismo hilo.</p></div>
                </button>
              </div>
              <p v-else class="mt-6 text-sm text-slate-500">No hay una trayectoria compatible con el programa y grado actuales.</p>
            </article>
          </div>

          <article v-if="tipo === 'ticket' && modoTicket === 'operativo'" class="rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <div><p class="text-xs font-bold uppercase tracking-wide text-slate-500">Destino operativo</p><h3 class="mt-1 text-base font-bold">¿Qué debe pasar con este ticket?</h3></div>
            <div class="mt-4 grid gap-2 sm:grid-cols-3"><button class="decision-primary" :disabled="guardando" @click="guardar('mantener_activo')">Seguir activo</button><button class="decision-secondary" :disabled="guardando" @click="guardar('archivar_historico')">Archivar histórico</button><button class="decision-secondary" :disabled="guardando" @click="guardar('fuera_proceso')">Fuera del proceso</button></div>
            <textarea v-model="nota" rows="2" class="mt-3 w-full rounded-md border border-slate-300 bg-white p-2 text-sm dark:border-slate-700 dark:bg-slate-950" placeholder="Motivo o evidencia de la decisión (opcional)"></textarea>
          </article>
          <article v-else-if="tipo === 'legado'" class="rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <div><p class="text-xs font-bold uppercase tracking-wide text-slate-500">Histórico conservado</p><h3 class="mt-1 text-base font-bold">No requiere una decisión ahora</h3><p class="mt-1 text-sm text-slate-500">Puede tener resoluciones, pero no existe prueba documental única para vincularlo a una trayectoria canónica. Se conserva en su paso actual: no crea un expediente nuevo, no se fusiona y no afecta tu cola diaria.</p></div>
          </article>
          <article v-else-if="tipo === 'ticket' && seleccion.requiere_decision && seleccion.datos.conflicto_academico === 'si'" class="rounded-lg border border-amber-200 bg-amber-50 p-5 dark:border-amber-900 dark:bg-amber-950/20">
            <div><p class="text-xs font-bold uppercase tracking-wide text-amber-800 dark:text-amber-200">Vínculo bloqueado</p><h3 class="mt-1 text-base font-bold">El ticket no corresponde al expediente anterior</h3><p class="mt-1 text-sm text-slate-600 dark:text-slate-300">Confirma que debe conservarse sin vínculo. Después aparecerá en Clasificar destino para decidir si sigue activo, se archiva con sustento o queda fuera del proceso.</p></div>
            <div class="mt-4 grid gap-2 sm:grid-cols-2"><button class="decision-primary" :disabled="guardando" @click="guardar('mantener_sin_vinculo')">Conservar sin vínculo</button><button class="decision-secondary" :disabled="guardando" @click="irAClasificarDestino">Ir a clasificar destino</button></div>
            <textarea v-model="nota" rows="2" class="mt-3 w-full rounded-md border border-slate-300 bg-white p-2 text-sm dark:border-slate-700 dark:bg-slate-950" placeholder="Motivo o evidencia adicional (opcional)"></textarea>
          </article>
          <article v-else-if="seleccion.requiere_decision && seleccion.trayectorias?.length" class="rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <div class="flex flex-wrap items-center justify-between gap-3"><div><p class="text-xs font-bold uppercase tracking-wide text-slate-500">Decisión</p><h3 class="mt-1 text-base font-bold">¿Qué representa este registro?</h3></div><span v-if="seleccion.decision" class="text-sm text-emerald-700 dark:text-emerald-300">Registrado: {{ seleccion.decision.accion }}</span></div>
            <div v-if="tipo === 'ticket' && seleccion.datos.candidato_archivo_historico === 'si'" class="mt-4 grid gap-2 sm:grid-cols-3"><button class="decision-primary" :disabled="guardando" @click="guardar('archivar_historico')">Archivar internamente</button><button class="decision-secondary" :disabled="guardando" @click="guardar('reactivar')">Mantener activo</button><button class="decision-secondary" :disabled="guardando" @click="guardar('pendiente')">Decidir después</button></div>
            <div v-else class="mt-4 grid gap-2 sm:grid-cols-4"><button class="decision-primary" :disabled="!claveSeleccionada || guardando" @click="guardar('confirmar_trayectoria')">Corresponde a esta trayectoria</button><button class="decision-secondary" :disabled="guardando" @click="guardar('separar')">Son trámites distintos</button><button class="decision-secondary" :disabled="guardando" @click="guardar('mantener_legacy')">Conservar como está</button><button class="decision-secondary" :disabled="guardando" @click="guardar('pendiente')">Decidir después</button></div>
            <textarea v-model="nota" rows="2" class="mt-3 w-full rounded-md border border-slate-300 bg-white p-2 text-sm dark:border-slate-700 dark:bg-slate-950" placeholder="Nota de la decisión (opcional)"></textarea>
          </article>
          <article v-else-if="seleccion.identificado_automaticamente" class="rounded-lg border border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-950 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100">
            <p class="font-bold">Identificado automáticamente</p>
            <p class="mt-1">Hay una sola trayectoria compatible con el estudiante, programa y grado. Se conserva como evidencia y no requiere una decisión humana.</p>
          </article>
        </section>
        <section v-else class="flex min-h-[500px] items-center justify-center rounded-lg border border-dashed border-slate-300 text-sm text-slate-500 dark:border-slate-700">Selecciona un caso de la lista.</section>
      </section>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import api from '../api.js'
const tipos = [{ id: 'expediente', label: 'Conflictos documentales', icon: 'pi-exclamation-triangle' }, { id: 'duplicado', label: 'Duplicados reales', icon: 'pi-clone' }, { id: 'legado', label: 'Históricos conservados', icon: 'pi-file' }, { id: 'ticket', label: 'Tickets por decidir', icon: 'pi-inbox' }]
const estados = [{ id: 'pendiente', label: 'Conflictos' }, { id: 'identificado', label: 'Vínculos únicos' }, { id: 'todos', label: 'Todos' }]
const tipo = ref('duplicado'), modoTicket = ref('identidad'), filtroEstado = ref('pendiente'), colaOperativa = ref('revision'), busqueda = ref(''), casos = ref([]), resumen = ref({}), seleccion = ref(null), cargando = ref(false), guardando = ref(false), claveSeleccionada = ref(''), nota = ref('')
const colasOperativas = [{ id: 'revision', label: 'Revisión histórica' }, { id: 'activos', label: 'Activos recientes' }, { id: 'todos', label: 'Ambas colas' }]
const estadosVisibles = computed(() => {
  if (tipo.value === 'ticket' && modoTicket.value === 'operativo') return []
  if (tipo.value === 'duplicado') return [{ id: 'pendiente', label: 'Por decidir' }, { id: 'decididos', label: 'Preparados' }, { id: 'todos', label: 'Todos' }]
  if (tipo.value === 'legado') return []
  return estados
})
const trayectoriasConGradoDistinto = computed(() => new Set((seleccion.value?.trayectorias || []).map(item => item.documentos?.[0]?.grado).filter(Boolean)).size > 1)
const contadorTipo = computed(() => {
  if (tipo.value === 'legado' || tipo.value === 'expediente') return resumen.value.total ?? '…'
  return resumen.value.pendientes ?? '…'
})
const textoCabecera = computed(() => ({ expediente: 'Hay más de una trayectoria posible o evidencia que no coincide. Revisa el PDF y decide la trayectoria correcta.', duplicado: 'Sólo aparecen matrículas distintas; los duplicados evidentes ya fueron consolidados automáticamente.', legado: 'Consulta expedientes históricos que se conservan en su paso actual. No forman parte de una cola pendiente.', ticket: modoTicket.value === 'operativo' ? 'Decide el destino local con el mensaje, adjuntos y evidencia histórica en una sola ficha.' : 'Cruces documentales ambiguos: no es la Bandeja diaria ni crea vínculos automáticos.' }[tipo.value]))
const datosOrigen = computed(() => !seleccion.value ? [] : Object.entries(seleccion.value.datos).filter(([k, v]) => v && !['claves_candidatas', 'titulo_actual', 'titulo_tesis', 'fuente_resolucion'].includes(k)).slice(0, 10))
const etiquetas = { id_expediente_actual: 'Expediente', codigo_actual: 'Código registrado', grado_actual: 'Grado', programa_actual: 'Programa', estado_actual: 'Estado', firmas_historicas: 'Resoluciones históricas', estado_migracion: 'Situación', origen_evidencia: 'Evidencia disponible', trayectorias_candidatas: 'Coincidencias documentales', estado_propuesta: 'Resultado del cruce', canal_tramite: 'Canal institucional', paso_sugerido: 'Paso identificado', conflicto_academico: 'Contradicción académica', motivo_conflicto: 'Motivo del conflicto', grado_detectado_ticket: 'Grado declarado en ticket', programa_detectado_ticket: 'Programa declarado en ticket', lectura_operativa: 'Lectura operativa' }
function etiqueta(valor) { return etiquetas[valor] || valor.replaceAll('_', ' ') }
function valorCampo(campo, valor) { if (campo !== 'estado_migracion') return valor; return ({ sin_coincidencia_fuerte: 'No se pudo vincular automáticamente', separar_o_revisar: 'Hay más de una trayectoria posible', migrable_unico: 'Vínculo documental único', confirmado_humano: 'Vínculo confirmado', consolidado_historico: 'Histórico consolidado' }[valor] || valor.replaceAll('_', ' ')) }
const explicacionCaso = computed(() => { if (!seleccion.value) return ''; const d = seleccion.value.datos || {}; if (tipo.value === 'legado') return 'Este expediente puede tener una o varias resoluciones, pero sus rutas, nombre, código, programa o grado no aportaron una prueba única para reconstruir el hilo completo. Se conserva exactamente en su paso actual para que una futura resolución o ticket lo complete; no debes fusionarlo ni crear otro.'; if (tipo.value === 'expediente') return 'Este expediente sí tiene evidencia documental, pero el sistema encontró más de una posibilidad compatible o una contradicción entre datos. La resolución existente puede ser de otra matrícula, programa, grado o trámite de la misma persona; por eso requiere decisión humana.'; if (tipo.value === 'duplicado') return 'Son dos expedientes que el sistema asocia a una misma trayectoria, pero sus matrículas son distintas. Confirma si representan el mismo trámite o un cambio de modalidad/reingreso antes de unirlos.'; if (d.conflicto_academico === 'si') return 'El ticket declara una matrícula, grado o programa incompatible con el expediente asociado previamente por nombre. Se retiró o se bloqueará ese vínculo automático: decide el destino sin archivarlo como histórico.'; return d.candidato_archivo_historico === 'si' ? 'El ticket parece histórico, pero debes comprobar si ya fue atendido o si corresponde archivarlo.' : 'El sistema necesita una decisión porque la identidad o el destino del ticket no se puede concluir automáticamente.' })
function tituloCaso(caso) { const d = caso.datos; return d.estudiante || d.nombre_alumno || d.numero_visual || d.nombre_normalizado || caso.referencia }
function resumenCaso(caso) { const d = caso.datos; return d.candidato_archivo_historico === 'si' ? 'Cierre histórico por verificar' : d.programa_actual || d.canal_tramite || d.codigo_actual || d.codigo_validado || d.estado_migracion || d.estado_propuesta || '' }
function textoEstadoCaso(caso) { if (caso.tipo === 'legado') return 'Conservado'; if (caso.datos?.conflicto_academico === 'si') return 'Identidad contradictoria'; if (caso.decision) return 'Decidido'; if (caso.requiere_decision) return 'Por decidir'; if (caso.identificado_automaticamente) return 'Identificado'; return 'Sin coincidencia suficiente' }
function claseEstadoCaso(caso) { if (caso.decision || caso.identificado_automaticamente) return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-200'; if (caso.requiere_decision) return 'bg-amber-100 text-amber-800'; return 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300' }
function nombreTrayectoria(clave) { const trayectoria = seleccion.value?.trayectorias?.find(item => item.clave === clave); return trayectoria?.documentos?.[0]?.estudiante || 'Trayectoria documental' }
function descripcionTrayectoria(clave) { const trayectoria = seleccion.value?.trayectorias?.find(item => item.clave === clave); const doc = trayectoria?.documentos?.[0]; return doc ? `${doc.grado || 'Sin grado'} · ${doc.programa || 'Sin programa'}${doc.modalidad && doc.modalidad !== 'SIN_MODALIDAD' ? ` · ${doc.modalidad}` : ''}` : 'Sin programa identificado' }
async function cargar() { cargando.value = true; try { const endpoint = tipo.value === 'ticket' && modoTicket.value === 'operativo' ? '/admin/conciliacion-operativa-tickets' : tipo.value === 'duplicado' ? '/admin/conciliacion-duplicados' : '/admin/conciliacion-identidades'; const params = { q: busqueda.value, limite: 200 }; if (endpoint.endsWith('identidades') || endpoint.endsWith('duplicados')) params.estado = filtroEstado.value; if (endpoint.endsWith('identidades')) params.tipo = tipo.value; if (endpoint.endsWith('tickets')) params.cola = colaOperativa.value; const { data } = await api.get(endpoint, { params }); casos.value = data.casos; resumen.value = data.resumen; seleccion.value = casos.value[0] || null } finally { cargando.value = false } }
function cambiarTipo(nuevo) { tipo.value = nuevo; modoTicket.value = 'identidad'; filtroEstado.value = nuevo === 'legado' ? 'todos' : 'pendiente'; resumen.value = {}; casos.value = []; seleccion.value = null; cargar() }
function cambiarModoTicket(nuevo) { modoTicket.value = nuevo; filtroEstado.value = 'pendiente'; resumen.value = {}; casos.value = []; seleccion.value = null; cargar() }
function cambiarColaOperativa(nuevo) { colaOperativa.value = nuevo; resumen.value = {}; casos.value = []; seleccion.value = null; cargar() }
function irAClasificarDestino() { modoTicket.value = 'operativo'; colaOperativa.value = 'revision'; resumen.value = {}; casos.value = []; seleccion.value = null; cargar() }
async function guardar(accion) { if (!seleccion.value) return; guardando.value = true; try { await api.post(`/admin/conciliacion-identidades/${tipo.value}/${seleccion.value.referencia}`, { accion, clave_identidad: claveSeleccionada.value || null, nota: nota.value || null }); await cargar() } finally { guardando.value = false } }
async function abrirPdf(id) { try { const { data } = await api.get(`/resoluciones/documentos/${id}/archivo`, { responseType: 'blob' }); window.open(URL.createObjectURL(data), '_blank', 'noopener') } catch { window.dispatchEvent(new CustomEvent('epg:api-error', { detail: { mensaje: 'El PDF de esta resolución no está disponible localmente.' } })) } }
async function abrirResolucionHistorica(id) { try { const { data } = await api.get(`/resoluciones/${id}/archivo`, { responseType: 'blob' }); window.open(URL.createObjectURL(data), '_blank', 'noopener') } catch { window.dispatchEvent(new CustomEvent('epg:api-error', { detail: { mensaje: 'El archivo histórico no está disponible localmente.' } })) } }
watch(seleccion, caso => { claveSeleccionada.value = caso?.decision?.clave_identidad || caso?.trayectorias?.[0]?.clave || ''; nota.value = caso?.decision?.nota || '' })
onMounted(cargar)
</script>

<style scoped>
.decision-primary,.decision-secondary{min-height:2.6rem;border-radius:.375rem;padding:.55rem .75rem;font-size:.82rem;font-weight:700}.decision-primary{background:#123b78;color:#fff}.decision-primary:disabled{opacity:.45}.decision-secondary{border:1px solid #cbd5e1}.decision-secondary:hover{background:#f8fafc}.dark .decision-secondary{border-color:#334155}.dark .decision-secondary:hover{background:#172033}
</style>
