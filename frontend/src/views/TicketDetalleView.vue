<template>
  <div class="page-shell animate-fade-in">
    <header class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
      <div class="flex min-w-0 items-start gap-3">
        <button type="button" class="icon-btn mt-0.5" title="Volver" aria-label="Volver" @click="router.back()"><i class="pi pi-arrow-left"></i></button>
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-2">
            <p class="font-mono text-sm font-bold text-sky-700 dark:text-cyan-300">#{{ ticket?.numero_visual || '...' }}</p>
            <span v-if="ticket" :class="badgeSituacion(ticket.situacion_operativa)">{{ textoSituacion(ticket.situacion_operativa) }}</span>
            <span v-if="ticket" :class="badgeEstado(ticket.estado)">{{ textoEstado(ticket.estado) }}</span>
          </div>
          <h2 class="mt-1 max-w-4xl text-xl font-bold text-slate-950 sm:text-2xl dark:text-white">{{ ticket?.asunto || 'Detalle de ticket' }}</h2>
          <p class="mt-1 text-xs text-slate-500">{{ formatFechaHora(ticket?.fecha) }} · {{ ticket?.nombre_estudiante_osticket || 'Estudiante sin identificar' }}</p>
        </div>
      </div>
      <button type="button" class="btn-outline self-start" :disabled="cargando" @click="cargar">
        <i :class="cargando ? 'pi-spin pi-spinner' : 'pi-refresh'" class="pi"></i>Actualizar
      </button>
    </header>

    <div v-if="cargando && !ticket" class="grid grid-cols-1 gap-5 xl:grid-cols-3">
      <div class="h-96 animate-pulse rounded-lg bg-slate-200 xl:col-span-2 dark:bg-slate-800"></div>
      <div class="h-96 animate-pulse rounded-lg bg-slate-200 dark:bg-slate-800"></div>
    </div>

    <div v-else-if="errorCarga" class="rounded-lg border border-red-200 bg-red-50 p-6 text-center dark:border-red-500/30 dark:bg-red-500/10">
      <i class="pi pi-exclamation-circle text-2xl text-red-500"></i>
      <p class="mt-2 text-sm font-semibold text-red-800 dark:text-red-300">{{ errorCarga }}</p>
      <button type="button" class="btn-outline mt-4" @click="router.back()">Volver a la bandeja</button>
    </div>

    <div v-else-if="ticket" class="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1.55fr)_minmax(350px,0.75fr)]">
      <main class="min-w-0 space-y-4">
        <section class="space-y-4">
          <div class="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <div class="flex flex-col gap-3 border-b border-slate-200 px-5 py-4 sm:flex-row sm:items-center sm:justify-between dark:border-slate-800">
              <div>
                <h3 class="section-title">Datos identificados</h3>
                <p class="mt-0.5 text-xs text-slate-500">osTicket, cuerpo y archivos adjuntos.</p>
              </div>
              <button type="button" class="btn-outline btn-sm" :disabled="extrayendo" @click="extraerDatos">
                <i :class="extrayendo ? 'pi-spin pi-spinner' : 'pi-sparkles'" class="pi"></i>
                {{ extrayendo ? 'Procesando' : 'Actualizar extraccion' }}
              </button>
            </div>
            <dl class="grid grid-cols-1 sm:grid-cols-2">
              <div v-for="dato in datosResumen" :key="dato.label" class="min-h-16 border-b border-slate-100 px-5 py-3 sm:border-r dark:border-slate-800">
                <dt class="text-[11px] font-medium text-slate-500">{{ dato.label }}</dt>
                <dd :class="dato.mono ? 'font-mono' : ''" class="mt-1 break-words text-sm font-semibold text-slate-900 dark:text-white">{{ dato.valor || 'No detectado' }}</dd>
              </div>
            </dl>
          </div>

          <div v-if="resumen?.resumen_texto" class="rounded-lg border border-sky-200 bg-sky-50 p-4 text-sm text-sky-900 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-200">
            <p class="text-xs font-semibold uppercase">Resumen automatico</p>
            <p class="mt-1 leading-6">{{ resumen.resumen_texto }}</p>
          </div>

          <div class="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <h3 class="section-title">Archivos procesados</h3>
            <div v-if="detalleArchivos.length" class="mt-3 divide-y divide-slate-100 dark:divide-slate-800">
              <div v-for="archivo in detalleArchivos" :key="archivo.nombre" class="flex items-center gap-3 py-3">
                <i :class="archivo.error ? 'pi-exclamation-triangle text-red-500' : 'pi-check-circle text-emerald-500'" class="pi"></i>
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-medium text-slate-900 dark:text-white">{{ archivo.nombre }}</p>
                  <p class="text-xs text-slate-500">{{ archivo.error || `${archivo.paginas || 0} pagina(s) leidas` }}</p>
                </div>
              </div>
            </div>
            <p v-else class="mt-3 text-sm text-slate-500">Aun no hay detalle de lectura de archivos.</p>
          </div>
        </section>

        <section id="conversacion-ticket" class="rounded-lg border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <div class="mb-4">
            <h3 class="section-title">Conversacion y notas</h3>
            <p class="mt-0.5 text-xs text-slate-500">Las notas internas son locales. Responder al alumno exige confirmacion.</p>
          </div>
          <TicketThread
            :ticket-ref="String(route.params.uuid)"
            :cuerpo-ticket="ticket.cuerpo || ''"
            :mensajes-locales="ticket.datos_extraidos?.mensajes_locales || []"
            @respuesta-enviada="cargar"
          />
        </section>

        <section class="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <h3 class="section-title">Adjuntos del ticket</h3>
            <p class="mt-0.5 text-xs text-slate-500">{{ ticket.adjuntos_count || 0 }} archivo(s) registrados.</p>
          </div>
          <div v-if="ticket.adjuntos.length" class="divide-y divide-slate-100 dark:divide-slate-800">
            <div v-for="adjunto in ticket.adjuntos" :key="adjunto.id_archivo" class="flex items-center gap-3 px-5 py-4">
              <span class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-300"><i class="pi pi-file-pdf"></i></span>
              <div class="min-w-0 flex-1">
                <p class="truncate text-sm font-semibold text-slate-900 dark:text-white">{{ adjunto.nombre }}</p>
                <p class="text-[11px] text-slate-500">Evidencia de osTicket</p>
              </div>
              <button type="button" class="icon-btn" title="Ver archivo" aria-label="Ver archivo" @click="visorModal = adjunto"><i class="pi pi-eye"></i></button>
              <button type="button" class="icon-btn" title="Abrir en otra pestana" aria-label="Abrir en otra pestana" @click="abrirAdjunto(adjunto)"><i class="pi pi-external-link"></i></button>
            </div>
          </div>
          <div v-else class="px-5 py-16 text-center text-sm text-slate-500"><i class="pi pi-paperclip mb-3 block text-3xl text-slate-300"></i>Este ticket no tiene adjuntos registrados.</div>
        </section>

        <section class="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <h3 class="section-title">Historial local</h3>
            <p class="mt-0.5 text-xs text-slate-500">Decisiones, vinculos y notas registradas en este sistema.</p>
          </div>
          <div v-if="ticket.historial_acciones?.length" class="divide-y divide-slate-100 dark:divide-slate-800">
            <div v-for="(evento, index) in ticket.historial_acciones" :key="`${evento.fecha}-${index}`" class="flex gap-3 px-5 py-4">
              <span class="mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300"><i :class="iconoEvento(evento)" class="pi"></i></span>
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <p class="text-sm font-semibold text-slate-900 dark:text-white">{{ tituloEvento(evento) }}</p>
                  <time class="text-[11px] text-slate-500">{{ formatFechaHora(evento.fecha) }}</time>
                </div>
                <p v-if="evento.nota" class="mt-1 whitespace-pre-wrap text-xs leading-5 text-slate-600 dark:text-slate-300">{{ evento.nota }}</p>
                <p class="mt-1 text-[10px] text-slate-500">{{ evento.usuario || 'Sistema' }}</p>
              </div>
            </div>
          </div>
          <p v-else class="px-5 py-12 text-center text-sm text-slate-500">Sin acciones locales registradas.</p>
        </section>
      </main>

      <aside class="space-y-4 xl:sticky xl:top-5 xl:self-start">
        <section class="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <h3 class="section-title">Acciones del ticket</h3>
            <p v-if="ticket.decision_actual?.decision" class="mt-1 text-xs text-slate-500">Actual: {{ textoDecision(ticket.decision_actual.decision) }}</p>
            <p v-else class="mt-1 text-xs text-slate-500">Estas acciones son locales: no modifican osTicket hasta habilitar la integración externa.</p>
          </div>
          <form class="space-y-3 p-5" @submit.prevent="guardarDecision">
            <div class="grid grid-cols-2 gap-2">
              <button type="button" class="btn-outline btn-sm justify-center" @click="irAConversacion"><i class="pi pi-comment"></i>Observar</button>
              <button type="button" class="btn-outline btn-sm justify-center" :class="accionOsticket === 'transferir' ? 'ring-2 ring-sky-400' : ''" @click="seleccionarAccion('transferir')"><i class="pi pi-send"></i>Transferir</button>
              <button type="button" class="btn-outline btn-sm justify-center" :class="accionOsticket === 'no_corresponde' ? 'ring-2 ring-sky-400' : ''" @click="seleccionarAccion('no_corresponde')"><i class="pi pi-ban"></i>No corresponde</button>
              <button type="button" class="btn-outline btn-sm justify-center" :class="accionOsticket === 'cerrar_interno' ? 'ring-2 ring-sky-400' : ''" @click="seleccionarAccion('cerrar_interno')"><i class="pi pi-lock"></i>Cerrar</button>
              <button type="button" class="btn-outline btn-sm col-span-2 justify-center" :class="accionOsticket === 'reabrir' ? 'ring-2 ring-sky-400' : ''" @click="seleccionarAccion('reabrir')"><i class="pi pi-refresh"></i>Reabrir seguimiento</button>
            </div>
            <template v-if="accionOsticket">
              <input v-if="accionOsticket === 'transferir'" v-model="formDecision.destino" class="input-field" placeholder="Área o responsable de destino" required />
              <textarea v-model="formDecision.nota" class="input-field resize-none" rows="3" :placeholder="accionOsticket === 'transferir' ? 'Motivo de la transferencia' : 'Sustento de esta acción'" required></textarea>
            </template>
            <p class="text-[11px] leading-5 text-slate-500">“Observar” abre la conversación para registrar la observación. Crear el expediente es la única acción que deriva internamente a Secretaría Académica.</p>
            <p v-if="errorAccion" class="text-xs text-red-600 dark:text-red-300">{{ errorAccion }}</p>
            <button v-if="accionOsticket" type="submit" class="btn-primary w-full justify-center" :disabled="procesando || !formDecision.nota.trim()">
              <i :class="procesando === 'decision' ? 'pi-spin pi-spinner' : 'pi-check'" class="pi"></i>Confirmar acción
            </button>
          </form>
        </section>

        <section class="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <h3 class="section-title">Expediente oficial</h3>
          </div>
          <div v-if="ticket.expediente" class="p-5">
            <div class="flex items-start gap-3">
              <span class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-blue-50 text-[#132e66] dark:bg-blue-500/15 dark:text-cyan-300"><i class="pi pi-folder-open"></i></span>
              <div class="min-w-0 flex-1">
                <p class="text-sm font-bold text-slate-950 dark:text-white">{{ ticket.expediente.nombre_alumno }}</p>
                <p class="font-mono text-[11px] text-slate-500">{{ ticket.expediente.codigo_alumno }} · Exp. {{ ticket.expediente.id_expediente }}</p>
                <p class="mt-1 text-xs text-slate-500">Paso {{ ticket.expediente.id_paso_actual }}: {{ ticket.expediente.nombre_paso_actual }}</p>
              </div>
            </div>
            <div class="mt-4 flex gap-2">
              <button type="button" class="btn-primary btn-sm flex-1 justify-center" @click="router.push(`/expedientes/${ticket.expediente.uuid}`)">Ver expediente</button>
              <button type="button" class="btn-outline btn-sm" title="Desvincular" @click="desvincular"><i class="pi pi-unlink"></i></button>
            </div>
          </div>
          <div v-else class="space-y-4 p-5">
            <div v-if="ticket.antecedentes_historicos?.length" class="rounded-md border border-violet-200 bg-violet-50 p-3 dark:border-violet-500/30 dark:bg-violet-500/10">
              <p class="text-xs font-semibold text-violet-900 dark:text-violet-200"><i class="pi pi-history mr-1"></i>Antecedentes históricos encontrados</p>
              <p class="mt-1 text-[11px] leading-4 text-violet-800 dark:text-violet-200/80">Coincidencia {{ ticket.antecedentes_historicos[0].criterio === 'codigo_exacto' ? 'exacta por código' : 'exacta por nombre' }}. Es referencia para revisar, no un vínculo automático.</p>
              <div class="mt-2 max-h-44 divide-y divide-violet-200/70 overflow-y-auto dark:divide-violet-500/20">
                <div v-for="item in ticket.antecedentes_historicos" :key="`${item.fuente}-${item.hoja}-${item.fila}`" class="py-2 text-[11px] text-violet-950 dark:text-violet-100">
                  <p class="font-semibold">{{ item.resolucion }} <span v-if="item.paso_sugerido">· P{{ item.paso_sugerido }}</span></p>
                  <p class="mt-0.5 truncate opacity-80">{{ item.tipo || 'Tipo no registrado' }}<span v-if="item.fecha"> · {{ formatFecha(item.fecha) }}</span></p>
                  <p class="mt-0.5 opacity-70">{{ item.fuente }} · {{ item.hoja }} · fila {{ item.fila }}</p>
                </div>
              </div>
            </div>
            <div v-if="ticket.posibles_expedientes?.length">
              <p class="mb-2 text-xs font-semibold text-slate-700 dark:text-slate-200">Coincidencias sugeridas</p>
              <div class="divide-y divide-slate-100 rounded-md border border-slate-200 dark:divide-slate-800 dark:border-slate-700">
                <button v-for="expediente in ticket.posibles_expedientes" :key="expediente.id_expediente" type="button" class="flex w-full items-center gap-2 p-3 text-left hover:bg-sky-50 dark:hover:bg-slate-800" @click="vincular(expediente)">
                  <span class="min-w-0 flex-1">
                    <span class="block truncate text-xs font-semibold text-slate-900 dark:text-white">{{ expediente.nombre_alumno }}</span>
                    <span class="block font-mono text-[10px] text-slate-500">{{ expediente.codigo_alumno }} · {{ expediente.puntaje }}%</span>
                  </span>
                  <i class="pi pi-link text-xs text-sky-700"></i>
                </button>
              </div>
            </div>
            <div>
              <label class="input-label">Buscar expediente</label>
              <div class="flex gap-2">
                <input v-model="busquedaExpediente" class="input-field" placeholder="Nombre, codigo o tesis" @keyup.enter="buscarExpedientes" />
                <button type="button" class="icon-btn" title="Buscar" @click="buscarExpedientes"><i :class="buscandoExpediente ? 'pi-spin pi-spinner' : 'pi-search'" class="pi"></i></button>
              </div>
              <div v-if="resultadosExpediente.length" class="mt-2 divide-y divide-slate-100 rounded-md border border-slate-200 dark:divide-slate-800 dark:border-slate-700">
                <button v-for="expediente in resultadosExpediente" :key="expediente.id" type="button" class="flex w-full items-center gap-2 p-3 text-left hover:bg-sky-50 dark:hover:bg-slate-800" @click="vincularResultado(expediente)">
                  <span class="min-w-0 flex-1"><span class="block truncate text-xs font-semibold text-slate-900 dark:text-white">{{ expediente.titulo }}</span><span class="block truncate font-mono text-[10px] text-slate-500">{{ expediente.subtitulo }}</span></span>
                  <i class="pi pi-link text-xs text-sky-700"></i>
                </button>
              </div>
            </div>
            <p class="text-[11px] leading-5 text-slate-500">Los tickets se vinculan a expedientes existentes o, si es el primer trámite, crean su expediente inicial y se envían a Secretaría en la misma acción.</p>
            <div class="rounded-md border border-sky-200 bg-sky-50 p-3 dark:border-sky-500/30 dark:bg-sky-500/10">
              <p class="text-xs leading-5 text-sky-900 dark:text-sky-200">Si es el primer trámite del estudiante, créalo aquí. El sistema registra la clasificación y lo deriva a Secretaría automáticamente.</p>
              <button type="button" class="btn-primary btn-sm mt-3 w-full justify-center" @click="abrirCrearExpediente"><i class="pi pi-folder-plus"></i>Crear expediente inicial</button>
            </div>
          </div>
        </section>

        <section v-if="ticket.expediente" class="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <div class="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <h3 class="section-title">Resolucion del ticket</h3>
            <p class="mt-0.5 text-xs text-slate-500">Selecciona la resolucion concreta que atendio este ingreso.</p>
          </div>
          <div class="space-y-3 p-5">
            <div v-if="ticket.resolucion_ticket_confirmada" class="rounded-md border border-emerald-200 bg-emerald-50 p-3 dark:border-emerald-500/30 dark:bg-emerald-500/10">
              <p class="text-xs font-semibold text-emerald-800 dark:text-emerald-300"><i class="pi pi-verified mr-1"></i>{{ ticket.resolucion_ticket_confirmada.numero }}</p>
              <p class="mt-1 text-[11px] text-emerald-700 dark:text-emerald-300/80">Confirmada para este ticket por {{ ticket.resolucion_ticket_confirmada.confirmada_por }}</p>
            </div>
            <template v-else>
              <select v-model="resolucionSeleccionada" class="input-field" :disabled="!ticket.resoluciones_relacionadas?.length">
                <option value="">Seleccionar resolucion</option>
                <option v-for="resolucion in ticket.resoluciones_relacionadas" :key="resolucion.ref" :value="resolucion.ref">{{ resolucion.numero }} · P{{ resolucion.paso || '-' }} · {{ resolucion.tipo || 'Resolucion' }}</option>
              </select>
              <button type="button" class="btn-primary w-full justify-center" :disabled="procesando || !resolucionSeleccionada" @click="proponerResolucion">
                <i :class="procesando === 'resolucion' ? 'pi-spin pi-spinner' : 'pi-file-plus'" class="pi"></i>Proponer resolucion
              </button>
            </template>
            <div v-if="ticket.trazabilidad?.resoluciones?.length" class="space-y-2">
              <div v-for="relacion in ticket.trazabilidad.resoluciones" :key="relacion.id_ticket_resolucion" class="rounded-md border border-slate-200 p-2.5 dark:border-slate-700">
                <div class="flex items-center justify-between gap-2">
                  <p class="min-w-0 truncate text-xs font-semibold text-slate-800 dark:text-slate-200">{{ relacion.numero }}</p>
                  <span :class="relacion.estado === 'confirmada' ? 'badge-graduado' : relacion.estado === 'descartada' ? 'badge-caduco' : 'badge-observado'">{{ relacion.estado }}</span>
                </div>
                <p class="mt-1 text-[10px] text-slate-500">Propuesta por {{ relacion.propuesto_por || 'Sistema' }}</p>
                <div v-if="relacion.estado === 'propuesta' && puedeAutorizar" class="mt-2 flex gap-2">
                  <button type="button" class="btn-success btn-sm flex-1 justify-center" :disabled="procesando" @click="confirmarRelacion(relacion)"><i class="pi pi-verified"></i>Confirmar</button>
                  <button type="button" class="btn-outline btn-sm" :disabled="procesando" title="Descartar propuesta" @click="descartarRelacion(relacion)"><i class="pi pi-times"></i></button>
                </div>
              </div>
            </div>
            <div v-if="ticket.resoluciones_relacionadas?.length" class="max-h-44 divide-y divide-slate-100 overflow-y-auto border-t border-slate-100 dark:divide-slate-800 dark:border-slate-800">
              <div v-for="resolucion in ticket.resoluciones_relacionadas" :key="resolucion.ref" class="py-2.5">
                <div class="flex items-start justify-between gap-2">
                  <div class="min-w-0"><p class="truncate text-xs font-semibold text-slate-800 dark:text-slate-200">{{ resolucion.numero }}</p><p class="truncate text-[10px] text-slate-500">{{ resolucion.tipo }} · {{ formatFecha(resolucion.fecha) }}</p></div>
                  <button v-if="resolucion.archivo_url" type="button" class="icon-btn h-7 w-7 text-sky-700 dark:text-cyan-300" title="Abrir archivo" aria-label="Abrir archivo" @click="abrirArchivoResolucion(resolucion)"><i class="pi pi-external-link"></i></button>
                </div>
              </div>
            </div>
            <p v-else class="text-xs text-amber-700 dark:text-amber-300">El expediente aun no tiene resoluciones relacionadas disponibles.</p>
          </div>
        </section>

        <MesaTramiteTicket v-if="ticket.expediente" :ticket-ref="String(route.params.uuid)" :expediente="ticket.expediente" @actualizado="cargar" />
      </aside>
    </div>

    <VisorArchivo v-model="visorModal" />

    <div v-if="mostrarCrearExpediente" class="fixed inset-0 z-[75] flex items-center justify-center bg-slate-950/55 p-4">
      <section class="w-full max-w-lg rounded-lg border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-900" role="dialog" aria-modal="true" aria-labelledby="crear-expediente-titulo">
        <div class="flex items-start justify-between gap-3 border-b border-slate-200 p-5 dark:border-slate-800">
          <div><h3 id="crear-expediente-titulo" class="section-title">Crear y enviar expediente inicial</h3><p class="mt-1 text-xs text-slate-500">Confirma la identidad y el paso; al guardar se remitirá a Secretaría.</p></div>
          <button type="button" class="icon-btn" title="Cerrar" aria-label="Cerrar" @click="cerrarCrearExpediente"><i class="pi pi-times"></i></button>
        </div>
        <form class="space-y-3 p-5" @submit.prevent="crearExpedienteInicial">
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <label><span class="input-label">Nombre completo</span><input v-model="formExpedienteInicial.nombre_alumno" class="input-field" required /></label>
            <label><span class="input-label">Código de alumno</span><input v-model="formExpedienteInicial.codigo_alumno" class="input-field font-mono" required /></label>
            <label><span class="input-label">Paso que solicita este ticket <b class="text-red-600">*</b></span><select v-model.number="formExpedienteInicial.id_paso" class="input-field" required><option v-for="paso in 7" :key="paso" :value="paso">P{{ paso }}</option></select><span class="mt-1 block text-[10px] text-slate-500">No es el historial previo: es el trámite que debe iniciar ahora.</span></label>
            <label><span class="input-label">Tipo de grado <b class="text-red-600">*</b></span><select v-model="formExpedienteInicial.grado_postula" class="input-field" required><option value="Maestro">Maestro</option><option value="Doctor">Doctor</option></select></label>
          </div>
          <label><span class="input-label">Grado académico / programa <span class="font-normal text-slate-500">(detectado; editable)</span></span><input v-model="formExpedienteInicial.programa" class="input-field" placeholder="Ej.: DERECHO CONSTITUCIONAL" /></label>
          <label><span class="input-label">Título de tesis <span class="font-normal text-slate-500">(opcional, confirmar antes de guardar)</span></span><textarea v-model="formExpedienteInicial.titulo_tesis" class="input-field resize-none" rows="3"></textarea></label>
          <label><span class="input-label">Asesor identificado en los documentos <span class="font-normal text-slate-500">(opcional)</span></span><input v-model="formExpedienteInicial.nombre_asesor" class="input-field" placeholder="Sin asesor detectado" /></label>
          <div class="rounded-md border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800/60">
            <p class="text-xs font-semibold text-slate-800 dark:text-slate-100">Documentos presentados</p>
            <ul v-if="ticket.adjuntos?.length" class="mt-2 divide-y divide-slate-200 text-xs dark:divide-slate-700"><li v-for="adjunto in ticket.adjuntos" :key="adjunto.id_archivo" class="flex items-center gap-2 py-2 text-slate-600 dark:text-slate-300"><i class="pi pi-file"></i><span class="min-w-0 flex-1 truncate">{{ adjunto.nombre_archivo || adjunto.nombre }}</span><button type="button" class="icon-btn h-7 w-7" title="Ver documento" @click="visorModal = adjunto"><i class="pi pi-eye"></i></button></li></ul>
            <p v-else class="mt-1 text-xs text-slate-500">No hay adjuntos registrados en este ticket.</p>
          </div>
          <label><span class="input-label">Nota de validación <span class="font-normal text-slate-500">(opcional)</span></span><textarea v-model="formExpedienteInicial.nota" class="input-field resize-none" rows="2" placeholder="Por qué se confirma que es un expediente nuevo"></textarea></label>
          <div class="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300">El sistema buscará primero duplicados por código y nombre. Creará requisitos base, vinculará el ticket y abrirá el trámite en la cola de Secretaría; no genera ni firma una resolución automáticamente.</div>
          <p v-if="errorCrearExpediente" class="text-xs text-red-600 dark:text-red-300">{{ errorCrearExpediente }}</p>
          <div class="flex justify-end gap-2"><button type="button" class="btn-ghost" @click="cerrarCrearExpediente">Cancelar</button><button type="submit" class="btn-primary" :disabled="procesando === 'crear-expediente'"><i :class="procesando === 'crear-expediente' ? 'pi-spin pi-spinner' : 'pi-send'" class="pi"></i>Crear y enviar</button></div>
        </form>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import api from '../api.js'
import MesaTramiteTicket from '../components/MesaTramiteTicket.vue'
import TicketThread from '../components/TicketThread.vue'
import VisorArchivo from '../components/VisorArchivo.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const ticket = ref(null)
const cargando = ref(true)
const errorCarga = ref('')
const errorAccion = ref('')

async function abrirArchivoResolucion(resolucion) {
  if (!resolucion.archivo_historico) {
    window.open(resolucion.archivo_url, '_blank', 'noopener')
    return
  }
  try {
    const respuesta = await api.get(`/resoluciones/${resolucion.id_resolucion}/archivo`, { responseType: 'blob' })
    const url = URL.createObjectURL(respuesta.data)
    window.open(url, '_blank', 'noopener')
    window.setTimeout(() => URL.revokeObjectURL(url), 60000)
  } catch (error) {
    errorAccion.value = error.response?.data?.detail || 'No se pudo abrir la resolución histórica.'
  }
}

async function abrirAdjunto(adjunto) {
  if (!adjunto.api_archivo_url) {
    window.open(adjunto.url_visor || adjunto.ruta_local, '_blank', 'noopener')
    return
  }
  try {
    const respuesta = await api.get(adjunto.api_archivo_url, { responseType: 'blob' })
    const url = URL.createObjectURL(respuesta.data)
    window.open(url, '_blank', 'noopener')
    window.setTimeout(() => URL.revokeObjectURL(url), 60000)
  } catch (error) {
    errorAccion.value = error.response?.data?.detail || 'No se pudo abrir el adjunto.'
  }
}
const extrayendo = ref(false)
const procesando = ref('')
const visorModal = ref(null)
const datosExt = ref({})
const detalleArchivos = ref([])
const resumen = ref(null)
const resolucionSeleccionada = ref('')
const busquedaExpediente = ref('')
const buscandoExpediente = ref(false)
const resultadosExpediente = ref([])
const accionOsticket = ref('')
const formDecision = ref({ nota: '', destino: '' })
const mostrarCrearExpediente = ref(false)
const errorCrearExpediente = ref('')
const formExpedienteInicial = ref({ id_paso: 1, nombre_alumno: '', codigo_alumno: '', grado_postula: 'Maestro', programa: '', titulo_tesis: '', nombre_asesor: '', nota: '' })
const borradorInicialOriginal = ref('')
const puedeAutorizar = computed(() => auth.isAdmin || auth.isDirectora)

const tieneCambiosIniciales = computed(() => JSON.stringify(formExpedienteInicial.value) !== borradorInicialOriginal.value)

const datosResumen = computed(() => [
  { label: 'Nombre en osTicket', valor: ticket.value?.nombre_estudiante_osticket },
  { label: 'Correo', valor: ticket.value?.email_estudiante, mono: true },
  { label: 'Codigo en osTicket', valor: ticket.value?.codigo_alumno_osticket, mono: true },
  { label: 'Paso sugerido', valor: pasoSugeridoTexto.value },
  { label: 'Nombre detectado', valor: datosExt.value.nombre_firma || datosExt.value.nombre_osticket || datosExt.value.caratula?.nombre_alumno },
  { label: 'Codigo detectado', valor: datosExt.value.codigo_alumno, mono: true },
  { label: 'Grado académico', valor: datosExt.value.caratula?.grado_academico || datosExt.value.grado_detectado || resumen.value?.grado_detectado },
  { label: 'Programa detectado', valor: datosExt.value.caratula?.programa },
  { label: 'DNI detectado', valor: datosExt.value.dni, mono: true },
])

const pasoSugeridoTexto = computed(() => {
  const paso = resumen.value?.paso_sugerido || datosExt.value.paso_sugerido || ticket.value?.paso_sugerido
  if (!paso?.id_paso) return ''
  const confianza = paso.confianza ? ` · ${Math.round(paso.confianza * 100)}%` : ''
  return `Paso ${paso.id_paso}: ${paso.nombre_paso || ''}${confianza}`
})

function textoSituacion(valor) {
  return {
    requiere_resolucion: 'Requiere resolucion', falta_resolucion: 'Vinculado pendiente',
    sin_expediente: 'Sin expediente', posible_expediente: 'Posible expediente',
    pendiente_adjuntos: 'Adjuntos pendientes', error_extraccion: 'Error tecnico',
    fuera_proceso: 'Fuera del proceso', pendiente_transferencia: 'Transferir',
    atendido_con_resolucion: 'Resolucion confirmada', atendido: 'Atendido',
  }[valor] || 'Revision humana'
}

function badgeSituacion(valor) {
  if (['atendido', 'atendido_con_resolucion'].includes(valor)) return 'badge-graduado'
  if (valor === 'error_extraccion') return 'badge-error'
  if (['requiere_resolucion', 'falta_resolucion'].includes(valor)) return 'badge-observado'
  if (valor === 'fuera_proceso') return 'badge-caduco'
  return 'badge-nuevo'
}

function textoEstado(valor) {
  return { Pendiente_Descarga: 'Pendiente descarga', Archivos_Descargados: 'Archivos listos', Datos_Extraidos: 'Datos extraidos', Clasificado: 'Vinculado', Notificado: 'Cerrado local', Error: 'Error' }[valor] || valor
}

function badgeEstado(valor) {
  return { Pendiente_Descarga: 'badge-nuevo', Archivos_Descargados: 'badge-proceso', Datos_Extraidos: 'badge-observado', Clasificado: 'badge-proceso', Notificado: 'badge-graduado', Error: 'badge-error' }[valor] || 'badge'
}

function textoDecision(valor) {
  return { requiere_resolucion: 'Requiere resolucion', resolucion_notificada: 'Resolucion notificada', resolucion_cargada: 'Resolución cargada', no_corresponde: 'No corresponde', transferir: 'Transferir', cerrar_interno: 'Cierre interno', reabrir: 'Reabierto' }[valor] || valor
}

function formatFechaHora(fecha) {
  if (!fecha) return 'Sin fecha'
  const normalizada = fecha.includes('T') ? fecha : fecha.replace(' ', 'T')
  return new Date(normalizada).toLocaleString('es-PE', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function formatFecha(fecha) {
  if (!fecha) return 'Sin fecha'
  return new Date(fecha).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric' })
}

function iconoEvento(evento) {
  if (evento.tipo === 'decision') return 'pi-list-check'
  if (evento.tipo === 'mensaje') return 'pi-comment'
  if (evento.accion?.includes('vinculado')) return 'pi-link'
  return 'pi-history'
}

function tituloEvento(evento) {
  if (evento.tipo === 'decision') return `Decision: ${textoDecision(evento.decision)}`
  if (evento.tipo === 'mensaje') return evento.accion === 'nota_interna' ? 'Nota interna local' : 'Respuesta al alumno'
  return (evento.accion || 'Accion local').replaceAll('_', ' ').replace('decision:', 'Decision: ')
}

function sincronizarDatosExtraidos() {
  const datos = ticket.value?.datos_extraidos || {}
  datosExt.value = datos.datos_estructurados || {}
  detalleArchivos.value = datos.detalle_archivos || []
  resumen.value = datos.resumen || null
}

async function cargar() {
  cargando.value = true
  errorCarga.value = ''
  try {
    const res = await api.get(`/tickets/${route.params.uuid}`)
    ticket.value = res.data
    sincronizarDatosExtraidos()
  } catch (err) {
    errorCarga.value = err.response?.data?.detail || 'No se pudo cargar el ticket.'
  } finally {
    cargando.value = false
  }
}

async function extraerDatos() {
  extrayendo.value = true
  errorAccion.value = ''
  try {
    await api.get(`/tickets/${route.params.uuid}/extraer-datos`)
    await cargar()
  } catch (err) {
    errorAccion.value = err.response?.data?.detail || 'No se pudo actualizar la extraccion.'
  } finally {
    extrayendo.value = false
  }
}

async function guardarDecision() {
  if (!accionOsticket.value) return
  if (['no_corresponde', 'cerrar_interno'].includes(accionOsticket.value)) {
    const confirmado = window.confirm('Esta decision sacara el ticket de las colas activas del sistema local. ¿Continuar?')
    if (!confirmado) return
  }
  procesando.value = 'decision'
  errorAccion.value = ''
  try {
    await api.post(`/tickets/${route.params.uuid}/decision`, null, {
      params: {
        decision: accionOsticket.value,
        nota: formDecision.value.nota || undefined,
        destino: formDecision.value.destino || undefined,
      },
    })
    accionOsticket.value = ''
    formDecision.value = { nota: '', destino: '' }
    await cargar()
  } catch (err) {
    errorAccion.value = err.response?.data?.detail || 'No se pudo guardar la decision.'
  } finally {
    procesando.value = ''
  }
}

function seleccionarAccion(accion) {
  accionOsticket.value = accion
  formDecision.value = { nota: '', destino: '' }
  errorAccion.value = ''
}

function irAConversacion() {
  document.getElementById('conversacion-ticket')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function proponerResolucion() {
  if (!resolucionSeleccionada.value) return
  if (!window.confirm('¿Proponer esta resolucion para el ticket especifico? La confirmacion requiere Directora o Administrador.')) return
  procesando.value = 'resolucion'
  errorAccion.value = ''
  try {
    await api.post(`/tickets/${route.params.uuid}/resoluciones/proponer`, null, {
      params: {
        resolucion_ref: resolucionSeleccionada.value,
        nota: formDecision.value.nota || undefined,
      },
    })
    resolucionSeleccionada.value = ''
    await cargar()
  } catch (err) {
    errorAccion.value = err.response?.data?.detail || 'No se pudo proponer la resolucion.'
  } finally {
    procesando.value = ''
  }
}

async function confirmarRelacion(relacion) {
  if (!window.confirm('¿Confirmar esta resolucion para este ticket? Esta accion cierra solo el seguimiento local del ticket.')) return
  procesando.value = 'confirmar-resolucion'
  errorAccion.value = ''
  try {
    await api.post(`/tickets/${route.params.uuid}/resoluciones/${relacion.id_ticket_resolucion}/confirmar`)
    await cargar()
  } catch (err) {
    errorAccion.value = err.response?.data?.detail || 'No se pudo confirmar la resolucion.'
  } finally {
    procesando.value = ''
  }
}

async function descartarRelacion(relacion) {
  if (!window.confirm('¿Descartar esta propuesta de resolucion?')) return
  procesando.value = 'descartar-resolucion'
  errorAccion.value = ''
  try {
    await api.post(`/tickets/${route.params.uuid}/resoluciones/${relacion.id_ticket_resolucion}/descartar`)
    await cargar()
  } catch (err) {
    errorAccion.value = err.response?.data?.detail || 'No se pudo descartar la propuesta.'
  } finally {
    procesando.value = ''
  }
}

async function buscarExpedientes() {
  const q = busquedaExpediente.value.trim()
  if (q.length < 2) return
  buscandoExpediente.value = true
  try {
    const res = await api.get('/buscar', { params: { q, limite: 10 } })
    resultadosExpediente.value = res.data.expedientes || []
  } finally {
    buscandoExpediente.value = false
  }
}

function vincularResultado(resultado) {
  vincular({ uuid: resultado.uuid, id_expediente: resultado.id, nombre_alumno: resultado.titulo })
}

async function vincular(expediente) {
  if (!window.confirm(`¿Vincular este ticket al expediente de ${expediente.nombre_alumno}?`)) return
  procesando.value = 'vincular'
  errorAccion.value = ''
  try {
    await api.post(`/tickets/${route.params.uuid}/vincular-expediente`, null, {
      params: { expediente_ref: expediente.uuid || expediente.id_expediente },
    })
    resultadosExpediente.value = []
    busquedaExpediente.value = ''
    await cargar()
  } catch (err) {
    errorAccion.value = err.response?.data?.detail || 'No se pudo vincular el expediente.'
  } finally {
    procesando.value = ''
  }
}

async function desvincular() {
  if (!window.confirm('¿Desvincular este ticket del expediente? La accion quedara en el historial local.')) return
  procesando.value = 'desvincular'
  errorAccion.value = ''
  try {
    await api.post(`/tickets/${route.params.uuid}/desvincular-expediente`, null, {
      params: { confirmar: true, nota: formDecision.value.nota || undefined },
    })
    await cargar()
  } catch (err) {
    errorAccion.value = err.response?.data?.detail || 'No se pudo desvincular el ticket.'
  } finally {
    procesando.value = ''
  }
}

function abrirCrearExpediente() {
  const paso = resumen.value?.paso_sugerido || datosExt.value.paso_sugerido || ticket.value?.paso_sugerido
  formExpedienteInicial.value = {
    id_paso: Number(paso?.id_paso) || 1,
    nombre_alumno: ticket.value?.nombre_estudiante_osticket || datosExt.value.nombre_firma || datosExt.value.caratula?.nombre_alumno || '',
    codigo_alumno: ticket.value?.codigo_alumno_osticket || datosExt.value.codigo_alumno || '',
    grado_postula: (datosExt.value.grado_detectado || resumen.value?.grado_detectado || 'Maestro') === 'Doctor' ? 'Doctor' : 'Maestro',
    programa: datosExt.value.caratula?.programa || '',
    titulo_tesis: datosExt.value.caratula?.titulo_tesis || resumen.value?.titulo_tesis || '',
    nombre_asesor: datosExt.value.caratula?.nombre_asesor || datosExt.value.nombre_asesor || '',
    nota: '',
  }
  borradorInicialOriginal.value = JSON.stringify(formExpedienteInicial.value)
  errorCrearExpediente.value = ''
  mostrarCrearExpediente.value = true
}

function cerrarCrearExpediente(forzar = false) {
  if (!forzar && tieneCambiosIniciales.value && !window.confirm('Tienes cambios sin guardar. ¿Descartar el expediente inicial?')) return
  mostrarCrearExpediente.value = false
  errorCrearExpediente.value = ''
}

async function crearExpedienteInicial() {
  if (!ticket.value) return
  procesando.value = 'crear-expediente'
  errorCrearExpediente.value = ''
  try {
    await api.post(`/tickets/${route.params.uuid}/crear-expediente-inicial`, formExpedienteInicial.value)
    cerrarCrearExpediente(true)
    await cargar()
  } catch (err) {
    errorCrearExpediente.value = err.response?.data?.detail || 'No se pudo crear el expediente inicial.'
  } finally {
    procesando.value = ''
  }
}

onMounted(cargar)
</script>
