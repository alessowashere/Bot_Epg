<template>
  <div class="page-shell animate-fade-in">
    <header class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="eyebrow">Secretaría Académica</p>
        <h2 class="page-title">Resoluciones en preparación</h2>
        <p class="page-subtitle">Revisa el expediente, prepara el Word y remítelo a Dirección.</p>
      </div>
      <button type="button" class="btn-ghost btn-sm" @click="cargar"><i class="pi pi-refresh"></i> Actualizar</button>
    </header>

    <nav class="flex flex-wrap gap-2 border-b border-slate-200 pb-3 dark:border-slate-800" aria-label="Áreas de Secretaría">
      <button type="button" :class="modo === 'trabajo' ? 'btn-primary' : 'btn-outline'" class="btn-sm" @click="modo = 'trabajo'"><i class="pi pi-inbox"></i>Bandeja de trabajo</button>
      <button type="button" :class="modo === 'control' ? 'btn-primary' : 'btn-outline'" class="btn-sm" @click="abrirControl"><i class="pi pi-book"></i>Control de resoluciones</button>
    </nav>

    <div v-if="mensaje" :class="['rounded-md border px-3 py-2 text-xs', error ? 'border-red-500/30 bg-red-950/30 text-red-200' : 'border-emerald-500/30 bg-emerald-950/30 text-emerald-200']">{{ mensaje }}</div>

    <section v-if="modo === 'control'" class="space-y-4">
      <div class="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(0,1fr)_280px]">
        <div class="card">
          <div class="flex flex-wrap items-center justify-between gap-3"><div><p class="eyebrow">Numeración {{ anioControl }}</p><h3 class="section-title">Libro anual de resoluciones</h3></div><select v-model.number="anioControl" class="input-field w-32" @change="cargarControl"><option v-for="anio in aniosControl" :key="anio" :value="anio">{{ anio }}</option></select></div>
          <div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4"><div><p class="text-[10px] text-slate-500">Última firmada</p><p class="mt-1 text-xl font-bold text-slate-900 dark:text-white">{{ controlNumero.ultimo_numero_firmado || '-' }}</p></div><div><p class="text-[10px] text-slate-500">Siguiente por asignar</p><p class="mt-1 text-sm font-bold text-sky-700 dark:text-cyan-300">{{ controlNumero.siguiente_disponible || '-' }}</p></div><div><p class="text-[10px] text-slate-500">Reservas activas</p><p class="mt-1 text-xl font-bold text-slate-900 dark:text-white">{{ controlNumero.reservas_activas?.length || 0 }}</p></div><div><p class="text-[10px] text-slate-500">Colisiones</p><p class="mt-1 text-xl font-bold" :class="controlNumero.colisiones?.length ? 'text-red-600' : 'text-emerald-600'">{{ controlNumero.colisiones?.length || 0 }}</p></div></div>
        </div>
        <div class="card"><p class="eyebrow">Modelos Word</p><h3 class="section-title">7 pasos cubiertos</h3><p class="mt-2 text-xs leading-5 text-slate-500">{{ plantillasTodas.length }} familias canónicas, incluidas variantes CAI, cambios y rectificaciones.</p><button type="button" class="btn-outline btn-sm mt-3" @click="mostrarCatalogo = !mostrarCatalogo"><i class="pi pi-file-word"></i>{{ mostrarCatalogo ? 'Ocultar catálogo' : 'Ver catálogo' }}</button></div>
      </div>
      <div v-if="mostrarCatalogo" class="card">
        <div class="flex items-center justify-between gap-3"><div><p class="eyebrow">Catálogo institucional</p><h3 class="section-title">Modelos detectados en la carpeta de Secretaría</h3></div><span class="badge-proceso">{{ plantillasTodas.length }}</span></div>
        <div class="mt-4 grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3">
          <div v-for="plantilla in plantillasTodas" :key="plantilla.codigo" class="rounded border border-slate-200 px-3 py-2 dark:border-slate-700">
            <div class="flex items-start justify-between gap-2"><p class="text-xs font-semibold text-slate-900 dark:text-white">P{{ plantilla.id_paso }} · {{ etiquetaVariante(plantilla.variante) }}</p><span class="font-mono text-[10px] text-cyan-700 dark:text-cyan-300">{{ plantilla.codigo }}</span></div>
            <p class="mt-1 line-clamp-2 text-[10px] leading-4 text-slate-500">{{ plantilla.paso }}</p>
            <p class="mt-2 text-[10px] text-slate-500">{{ plantilla.copias_clasificadas }} documento(s) comparados · {{ plantilla.formatos_detectados }} formato(s)</p>
          </div>
        </div>
      </div>
      <div class="card p-0 overflow-hidden">
        <div class="flex flex-wrap gap-2 border-b border-slate-200 p-3 dark:border-slate-700"><input v-model="busquedaControl" class="input-field min-w-52 flex-1" placeholder="Número, estudiante, programa o tipo" @keyup.enter="buscarControl" /><select v-model="pasoControl" class="input-field w-36" @change="buscarControl"><option value="">Todos los pasos</option><option v-for="paso in 7" :key="paso" :value="paso">Paso {{ paso }}</option></select><button class="btn-primary btn-sm" @click="buscarControl"><i class="pi pi-search"></i>Buscar</button></div>
        <div class="max-h-[580px] overflow-auto"><table class="data-table"><thead><tr><th>Resolución</th><th>Estudiante</th><th>Tipo</th><th>Fecha</th><th></th></tr></thead><tbody><tr v-for="item in resolucionesControl" :key="item.id_documento"><td class="font-mono font-semibold">{{ item.resolucion_numero }}-{{ item.resolucion_anio }}</td><td><p class="text-xs font-semibold text-slate-900 dark:text-white">{{ item.nombre_alumno || 'Sin estudiante' }}</p><p class="text-[10px] text-slate-500">{{ item.codigo_alumno || '' }}</p></td><td class="text-xs">P{{ item.id_paso_inferido || '-' }} · {{ item.tipo_resolucion || 'Sin tipo' }}</td><td class="text-xs">{{ item.fecha_resolucion || '-' }}</td><td><button class="icon-btn" title="Vista previa del archivo" @click="abrirArchivoControl(item)"><i class="pi pi-eye"></i></button></td></tr><tr v-if="!resolucionesControl.length"><td colspan="5" class="py-10 text-center text-sm text-slate-500">No hay resoluciones para este filtro.</td></tr></tbody></table></div>
        <div class="flex items-center justify-between gap-3 border-t border-slate-200 px-3 py-2 text-xs text-slate-500 dark:border-slate-700"><span>{{ totalControl }} registro(s) · página {{ paginaControl }} de {{ paginasControl }}</span><div class="flex gap-2"><button type="button" class="btn-outline btn-sm" :disabled="paginaControl <= 1" @click="cambiarPaginaControl(-1)"><i class="pi pi-chevron-left"></i>Anterior</button><button type="button" class="btn-outline btn-sm" :disabled="paginaControl >= paginasControl" @click="cambiarPaginaControl(1)">Siguiente<i class="pi pi-chevron-right"></i></button></div></div>
      </div>
    </section>

    <template v-else>
    <section v-if="seleccionLote.length" class="flex flex-wrap items-center gap-3 border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-950 dark:border-sky-500/30 dark:bg-sky-500/10 dark:text-sky-100">
      <span class="font-semibold">{{ seleccionLote.length }} trámite(s) seleccionado(s)</span>
      <select v-model="modeloLoteId" class="input-field min-w-56 !py-1.5 text-xs">
        <option value="">Modelo institucional para lote</option>
        <option v-for="modelo in modelosLote" :key="modelo.id_documento" :value="modelo.id_documento">{{ etiquetaModelo(modelo) }}</option>
      </select>
      <button type="button" class="btn-outline btn-sm" :disabled="procesando || !modeloLoteId || !puedeOperarLote" @click="generarLote"><i class="pi pi-file-word"></i> Generar Word en lote</button>
      <button type="button" class="btn-success btn-sm" :disabled="procesando || !puedeRemitirLote" @click="remitirLote"><i class="pi pi-send"></i> Remitir lote a Dirección</button>
      <button type="button" class="icon-btn ml-auto" title="Limpiar selección" aria-label="Limpiar selección" @click="seleccionLote = []"><i class="pi pi-times"></i></button>
      <p v-if="!puedeOperarLote" class="basis-full text-xs text-sky-800 dark:text-sky-200">Para generar juntos deben ser trámites del mismo paso, en elaboración y con número/fecha ya registrados.</p>
    </section>

    <div class="grid min-h-[560px] grid-cols-1 gap-5 xl:grid-cols-[340px_minmax(0,1fr)]">
      <section class="card p-0 overflow-hidden">
        <div class="border-b border-slate-200 p-3 dark:border-slate-700">
          <label for="buscar-secretaria" class="sr-only">Buscar trámites</label>
          <div class="relative">
            <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-xs text-slate-500"></i>
            <input id="buscar-secretaria" v-model="busqueda" class="input-field pl-9 text-xs" placeholder="Estudiante, código o resolución" @keyup.enter="cargar" />
          </div>
        </div>
        <div v-if="cargando" class="p-5 text-center text-xs text-slate-500"><i class="pi pi-spin pi-spinner mr-2"></i>Cargando</div>
        <div v-else class="max-h-[680px] overflow-y-auto">
          <div v-for="item in tramites" :key="item.uuid" :class="['flex border-b border-slate-200 last:border-0 dark:border-slate-800', seleccionado?.uuid === item.uuid ? 'bg-sky-50 dark:bg-cyan-950/30' : 'hover:bg-slate-50 dark:hover:bg-slate-800/50']">
            <label class="flex w-10 items-center justify-center" :title="item.estado === 'en_elaboracion_secretaria' ? 'Seleccionar para operación por lote' : 'Solo los trámites en elaboración se pueden operar en lote'">
              <input v-model="seleccionLote" :value="item.uuid" :disabled="item.estado !== 'en_elaboracion_secretaria'" type="checkbox" class="h-4 w-4 accent-sky-600 disabled:opacity-35" @change="actualizarModelosLote" />
            </label>
            <button type="button" :class="['min-w-0 flex-1 px-4 py-3 text-left', seleccionado?.uuid === item.uuid ? 'bg-sky-50 dark:bg-cyan-950/30' : '']" @click="seleccionar(item)">
            <div class="flex items-start justify-between gap-2">
              <p class="line-clamp-2 text-xs font-semibold text-slate-900 dark:text-white">{{ item.estudiante }}</p>
              <span class="badge-proceso flex-shrink-0">P{{ item.id_paso }}</span>
            </div>
            <p class="mt-1 truncate text-[11px] text-slate-500 dark:text-slate-400">{{ item.numero_resolucion || 'Sin número' }} · {{ item.tipo_resolucion }}</p>
            <p class="mt-1 text-[10px] text-sky-700 dark:text-cyan-300">{{ etiquetaEstado(item.estado) }}</p>
            </button>
          </div>
          <p v-if="!tramites.length" class="p-8 text-center text-xs text-slate-500">No hay trámites para Secretaría.</p>
        </div>
      </section>

      <section v-if="seleccionado" class="card min-w-0">
        <div class="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 pb-4 dark:border-slate-700">
          <div class="min-w-0">
            <p class="eyebrow">{{ seleccionado.codigo_alumno }} · Paso {{ seleccionado.id_paso }}</p>
            <h3 class="text-lg font-semibold text-slate-900 dark:text-white">{{ seleccionado.estudiante }}</h3>
            <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">{{ seleccionado.tipo_resolucion }}</p>
          </div>
          <div class="flex flex-wrap gap-2"><button v-if="seleccionado.ticket_uuid" type="button" class="btn-outline btn-sm" @click="abrirTicket"><i class="pi pi-ticket"></i> Ticket #{{ seleccionado.ticket_numero }}</button><button type="button" class="btn-outline btn-sm" @click="abrirExpediente"><i class="pi pi-folder-open"></i> Ver expediente</button></div>
        </div>

        <p v-if="seleccionado.titulo_tesis" class="mt-4 text-sm leading-6 text-slate-700 dark:text-slate-300">{{ seleccionado.titulo_tesis }}</p>
        <p v-if="seleccionado.observacion_actual" class="mt-3 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900 dark:border-amber-500/30 dark:bg-amber-950/30 dark:text-amber-200">{{ seleccionado.observacion_actual }}</p>
        <div v-if="seleccionado.regla_paso" class="mt-4 rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-xs text-slate-700 dark:border-cyan-500/25 dark:bg-cyan-950/15 dark:text-slate-300">
          <p class="font-semibold text-sky-900 dark:text-cyan-100">Regla P{{ seleccionado.id_paso }} · {{ seleccionado.regla_paso.estado_validacion === 'Confirmada' ? 'confirmada' : 'parcial' }}</p>
          <p class="mt-1">Origen: {{ seleccionado.regla_paso.sistema_origen || 'por validar' }} · Consulta: {{ textoConsultaRegla }}</p>
          <p v-if="seleccionado.regla_paso.nota_validacion" class="mt-1 text-slate-500 dark:text-slate-400">{{ seleccionado.regla_paso.nota_validacion }}</p>
        </div>

        <div class="mt-4 flex gap-1 rounded-md bg-slate-100 p-1 dark:bg-slate-800" role="tablist">
          <button type="button" :class="subvista === 'documento' ? 'bg-white text-slate-950 shadow-sm dark:bg-slate-700 dark:text-white' : 'text-slate-500'" class="flex-1 rounded px-3 py-2 text-xs font-semibold" @click="subvista = 'documento'"><i class="pi pi-file-word mr-1"></i>Generar resolución</button>
          <button v-if="mostrarConsulta" type="button" :class="subvista === 'consulta' ? 'bg-white text-slate-950 shadow-sm dark:bg-slate-700 dark:text-white' : 'text-slate-500'" class="flex-1 rounded px-3 py-2 text-xs font-semibold" @click="subvista = 'consulta'"><i class="pi pi-users mr-1"></i>Consulta docente</button>
        </div>

        <div v-if="seleccionado.estado === 'derivado_secretaria'" class="mt-5">
          <h4 class="text-sm font-semibold text-slate-900 dark:text-white">Revisión inicial</h4>
          <textarea v-model="notaRevision" class="input-field mt-2 resize-none text-xs" rows="3" placeholder="Observación para el tramitador (obligatoria si devuelve)"></textarea>
          <div class="mt-3 flex flex-wrap gap-2">
            <button type="button" class="btn-success" :disabled="procesando" @click="revisar('Aceptar')"><i class="pi pi-check"></i> Aceptar y preparar</button>
            <button type="button" class="btn-danger" :disabled="procesando || !notaRevision.trim()" @click="revisar('Observar')"><i class="pi pi-undo"></i> Devolver observado</button>
          </div>
        </div>

        <form v-if="subvista === 'documento' && ['en_elaboracion_secretaria', 'observado_por_direccion'].includes(seleccionado.estado)" class="mt-5 border-t border-slate-200 pt-5 dark:border-slate-700" @submit.prevent="guardarBorrador">
          <h4 class="text-sm font-semibold text-slate-900 dark:text-white">Datos y borrador</h4>
          <div class="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
            <div><label for="numero-res" class="input-label">Número de resolución</label><div class="flex gap-2"><input id="numero-res" v-model="preparacion.numero" class="input-field min-w-0" required placeholder="0766-2026/EPG-UAC" @blur="revisarNumeracion" /><button type="button" class="icon-btn" title="Usar siguiente número controlado" @click="usarSiguienteNumero"><i class="pi pi-sort-numeric-up"></i></button></div><p v-if="controlNumero.siguiente_disponible" class="mt-1 text-[10px] text-slate-500">Sugerido: {{ controlNumero.siguiente_disponible }}</p></div>
            <div><label for="fecha-res" class="input-label">Fecha de resolución</label><input id="fecha-res" v-model="preparacion.fecha" type="date" class="input-field" required /></div>
            <div v-if="revisionNumeracion" class="md:col-span-2 rounded-md border px-3 py-3 text-xs" :class="revisionNumeracion.bloquea ? 'border-red-300 bg-red-50 text-red-900 dark:border-red-500/30 dark:bg-red-950/20 dark:text-red-100' : revisionNumeracion.es_hueco ? 'border-amber-300 bg-amber-50 text-amber-950 dark:border-amber-500/30 dark:bg-amber-950/20 dark:text-amber-100' : 'border-emerald-300 bg-emerald-50 text-emerald-950 dark:border-emerald-500/30 dark:bg-emerald-950/20 dark:text-emerald-100'">
              <p class="font-semibold">{{ revisionNumeracion.mensaje }}</p>
              <div v-for="registro in revisionNumeracion.registros || []" :key="`${registro.origen}-${registro.referencia}`" class="mt-2 rounded border border-current/20 px-2 py-2"><p><strong>{{ registro.referencia }}</strong> · {{ registro.estudiante }}</p><p class="mt-1 opacity-80">{{ registro.origen }} · {{ registro.tipo || registro.estado || 'sin detalle' }}</p><button v-if="registro.archivo_url" type="button" class="mt-2 underline" @click="abrirArchivoUrl(registro.archivo_url)">Ver resolución existente</button></div>
              <div v-if="revisionNumeracion.es_hueco" class="mt-3 grid gap-2 md:grid-cols-[220px_minmax(0,1fr)]"><select v-model="preparacion.decision_numeracion" class="input-field text-xs"><option value="">¿Por qué se usa este número?</option><option value="no_emitida">Número no emitido</option><option value="archivo">Reservado para archivo</option><option value="anulada">Resolución anulada</option></select><input v-model="preparacion.nota_numeracion" class="input-field text-xs" placeholder="Explica brevemente la decisión para auditoría" /></div>
            </div>
            <div v-if="[4, 7].includes(seleccionado.id_paso)" class="md:col-span-2"><label for="ref-erp-secretaria" class="input-label">Referencia ERP</label><input id="ref-erp-secretaria" v-model="preparacion.referencia_origen" class="input-field" placeholder="Referencia obligatoria antes de remitir" /></div>
            <div class="md:col-span-2"><label for="word-res" class="input-label">Word para revisión de Dirección</label><input id="word-res" type="file" accept=".doc,.docx,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document" class="input-field text-xs" @change="archivoWord = $event.target.files?.[0] || null" /></div>
            <label class="flex items-center gap-2 text-xs text-slate-300 md:col-span-2"><input v-model="preparacion.requiere_consulta" :disabled="consultaDefinida" type="checkbox" class="h-4 w-4 accent-cyan-500 disabled:opacity-60" /> Requiere consulta previa de disponibilidad antes de designar</label>
          </div>
          <div class="mt-3 flex flex-wrap items-center gap-2">
            <button class="btn-primary" :disabled="procesando"><i class="pi pi-save"></i> Guardar borrador</button>
            <div v-if="seleccionado.borrador_word_url" class="flex flex-wrap gap-2"><button type="button" class="btn-primary btn-sm" :disabled="procesando" @click="abrirEditorWord"><i class="pi pi-pencil"></i> Editar Word en el servidor</button><a :href="seleccionado.borrador_word_url" target="_blank" rel="noopener" class="btn-success btn-sm"><i class="pi pi-download"></i> Descargar Word v{{ seleccionado.borrador_version }}</a></div>
            <button v-if="seleccionado.borrador_word_url || seleccionado.numero_resolucion" type="button" class="btn-danger btn-sm" :disabled="procesando" @click="descartarBorrador"><i class="pi pi-trash"></i>Descartar preparación</button>
          </div>
        </form>

        <section v-if="subvista === 'documento' && ['en_elaboracion_secretaria', 'observado_por_direccion'].includes(seleccionado.estado)" class="mt-5 border-t border-slate-200 pt-5 dark:border-slate-700">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h4 class="text-sm font-semibold text-slate-900 dark:text-white">Plantilla Word oficial</h4>
              <p class="mt-1 text-xs text-slate-500">Usa el formato canónico de Secretaría y conserva encabezados, tablas, estilos y pies.</p>
            </div>
            <span class="badge badge-observado"><i class="pi pi-user-edit"></i> Revisión obligatoria</span>
          </div>
          <div class="mt-3 grid grid-cols-1 gap-2 md:grid-cols-[minmax(0,1fr)_auto_auto]">
            <select v-model="plantillaOficialCodigo" class="input-field text-xs" @change="vistaOficial = null">
              <option value="">Selecciona la plantilla oficial</option>
              <option v-for="plantilla in plantillasOficiales" :key="plantilla.codigo" :value="plantilla.codigo">{{ plantilla.paso }} · {{ etiquetaVariante(plantilla.variante) }}</option>
            </select>
            <button type="button" class="btn-outline btn-sm" :disabled="procesando || !plantillaOficialCodigo || !preparacion.numero || !preparacion.fecha" @click="cargarVistaOficial"><i class="pi pi-eye"></i>Vista previa</button>
            <button type="button" class="btn-primary btn-sm" :disabled="procesando || !plantillaOficialCodigo || !preparacion.numero || !preparacion.fecha" @click="generarOficial"><i class="pi pi-file-word"></i>Generar Word</button>
          </div>
          <div v-if="vistaOficial" class="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_280px]">
            <article class="overflow-hidden rounded border border-slate-200 bg-slate-100 p-2 shadow-inner dark:border-slate-700 dark:bg-slate-950"><iframe v-if="vistaPdfUrl" :src="vistaPdfUrl" title="Vista visual de la resolución" class="h-[680px] w-full bg-white"></iframe><p v-else class="p-8 text-center text-xs text-slate-500">Preparando la maqueta visual del Word.</p></article>
            <aside class="space-y-3"><div class="rounded-md border border-slate-200 p-3 text-xs dark:border-slate-700"><p class="font-semibold text-slate-900 dark:text-white">Cambios aplicados</p><p v-for="(total, campo) in vistaOficial.campos_reemplazados" :key="campo" class="mt-1 flex justify-between text-slate-500"><span>{{ campo }}</span><strong>{{ total }}</strong></p><p class="mt-3 border-t border-slate-200 pt-2 text-[11px] text-slate-500 dark:border-slate-700">Edita número, fecha o referencia arriba y actualiza esta vista. El Word se genera sólo cuando lo confirmes.</p></div><p v-for="aviso in vistaOficial.advertencias" :key="aviso" class="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300">{{ aviso }}</p></aside>
          </div>
          <details class="mt-4 border-t border-slate-200 pt-4 dark:border-slate-700">
            <summary class="cursor-pointer text-xs font-semibold text-slate-500">Usar una resolución histórica como referencia</summary>
          <div class="mt-3 grid grid-cols-1 gap-2 md:grid-cols-[minmax(0,1fr)_auto]">
            <select v-model="modeloSeleccionadoId" class="input-field text-xs" @change="cargarVistaModelo">
              <option value="">Selecciona un modelo del paso {{ seleccionado.id_paso }}</option>
              <option v-for="modelo in modelos" :key="modelo.id_documento" :value="modelo.id_documento">{{ etiquetaModelo(modelo) }}</option>
            </select>
            <button type="button" class="btn-outline btn-sm" :disabled="procesando || !modeloSeleccionadoId" @click="cargarVistaModelo"><i class="pi pi-eye"></i> Vista previa</button>
          </div>
          <div v-if="vistaModelo" class="mt-3">
            <div v-if="vistaModelo.advertencias?.length" class="mb-3 border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900 dark:border-amber-500/30 dark:bg-amber-950/20 dark:text-amber-200">
              <p v-for="advertencia in vistaModelo.advertencias" :key="advertencia" class="mt-1 first:mt-0"><i class="pi pi-exclamation-triangle mr-1"></i>{{ advertencia }}</p>
            </div>
            <label for="contenido-borrador" class="input-label">Texto a generar</label>
            <textarea id="contenido-borrador" v-model="contenidoBorrador" class="input-field min-h-72 resize-y font-mono text-xs leading-5" spellcheck="true"></textarea>
            <div class="mt-3 flex flex-wrap items-center gap-2">
              <button type="button" class="btn-primary" :disabled="procesando || !preparacion.numero || !preparacion.fecha || contenidoBorrador.length < 120" @click="generarBorrador"><i class="pi pi-file-word"></i> Generar Word</button>
              <span class="text-xs text-slate-500">No se remite a Dirección automáticamente.</span>
            </div>
          </div>
          <p v-else-if="!modelos.length" class="mt-3 text-xs text-amber-700 dark:text-amber-300">No hay referencias históricas adicionales para este paso.</p>
          </details>
        </section>

        <div v-if="subvista === 'consulta' && ['en_elaboracion_secretaria', 'consulta_previa'].includes(seleccionado.estado)" class="mt-5 border-t border-slate-200 pt-5 dark:border-slate-700">
          <h4 class="text-sm font-semibold text-slate-900 dark:text-white">Consulta previa de disponibilidad</h4>
          <p class="mt-1 text-xs text-slate-500 dark:text-slate-400">La aceptación confirma disponibilidad; no crea una designación.</p>
          <div class="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
            <div class="sm:col-span-2"><label class="input-label">Mensaje predefinido</label><div class="grid grid-cols-1 gap-2 md:grid-cols-[minmax(0,1fr)_190px_auto]"><select v-model="consulta.id_plantilla" class="input-field text-xs" @change="aplicarPlantillaConsulta"><option value="">Mensaje libre</option><option v-for="plantilla in plantillasConsulta" :key="plantilla.id_plantilla" :value="plantilla.id_plantilla">{{ plantilla.nombre }}</option></select><input v-model="consulta.nombre_plantilla" class="input-field text-xs" placeholder="Nombre para guardar" /><button type="button" class="btn-outline btn-sm" :disabled="!consulta.nombre_plantilla || !consulta.asunto || !consulta.mensaje" @click="guardarPlantillaConsulta"><i class="pi pi-save"></i>Guardar</button></div></div>
            <div><label for="vigencia-consulta" class="input-label">Duración del enlace (días)</label><input id="vigencia-consulta" v-model.number="consulta.vigencia_dias" type="number" min="1" max="365" class="input-field text-xs" placeholder="Definir" /></div>
            <div><label for="modalidad-consulta" class="input-label">Respuesta requerida</label><select id="modalidad-consulta" v-model="consulta.modalidad_respuesta" class="input-field text-xs"><option v-for="modalidad in modalidadesConsulta" :key="modalidad">{{ modalidad }}</option></select></div>
          </div>
          <div class="mt-3 grid grid-cols-1 gap-2 md:grid-cols-[minmax(0,1fr)_170px_150px_auto]">
            <select v-model="consulta.id_docente" class="input-field text-xs"><option value="">Selecciona un docente</option><option v-for="docente in docentes" :key="docente.id_docente" :value="docente.id_docente">{{ docente.nombre_completo }}</option></select>
            <select v-model="consulta.tipo_participacion" class="input-field text-xs"><option v-for="tipo in tiposConsulta" :key="tipo">{{ tipo }}</option></select>
            <select v-model="consulta.canal_correo" class="input-field text-xs"><option value="institucional">Institucional</option><option value="personal">Personal</option><option value="ambos">Ambos correos</option></select>
            <button type="button" class="btn-outline btn-sm justify-center" :disabled="procesando || !consulta.id_docente || !consulta.vigencia_dias" @click="crearConsulta"><i class="pi pi-link"></i> Generar enlace</button>
          </div>
          <div class="mt-3 space-y-2"><input v-model="consulta.asunto" class="input-field text-xs" placeholder="Asunto del correo" /><textarea v-model="consulta.mensaje" class="input-field min-h-28 resize-y text-xs" placeholder="Mensaje. Variables: {docente}, {participacion}, {tipo_resolucion}, {estudiante}, {enlace}"></textarea></div>
          <div v-if="seleccionado.consultas?.length" class="mt-3 space-y-2">
            <div v-for="item in seleccionado.consultas" :key="item.uuid" class="flex flex-wrap items-center justify-between gap-2 rounded-md bg-slate-100 px-3 py-2 dark:bg-slate-800/60">
              <div><p class="text-xs font-medium text-slate-900 dark:text-white">{{ item.docente }} · {{ item.tipo_participacion }}</p><p v-if="item.nota_respuesta" class="text-[11px] text-slate-500 dark:text-slate-400">{{ item.nota_respuesta }}</p></div>
              <span :class="item.estado === 'Aceptado' ? 'badge-graduado' : item.estado === 'Pendiente' ? 'badge-observado' : 'badge-error'">{{ item.estado }}</span>
            </div>
          </div>
          <div v-if="enlacesGenerados.length" class="mt-3 rounded-md border border-sky-200 bg-sky-50 p-3 dark:border-cyan-500/30 dark:bg-cyan-950/20">
            <p class="text-xs font-semibold text-sky-900 dark:text-cyan-200">Enlaces recién generados</p>
            <div v-for="item in enlacesGenerados" :key="item.uuid" class="mt-3 border-t border-sky-200 pt-3 first:border-0 first:pt-0 dark:border-cyan-500/20"><p class="mb-1 text-[11px] text-sky-800 dark:text-cyan-100">{{ item.correo_borrador?.para || 'Docente sin correo registrado' }}</p><div class="flex items-center gap-2"><input :value="item.enlace_respuesta" readonly class="input-field min-w-0 flex-1 text-xs" /><button type="button" class="icon-btn" title="Copiar invitación" aria-label="Copiar invitación" @click="copiar(item.correo_borrador?.mensaje || item.enlace_respuesta)"><i class="pi pi-copy"></i></button></div></div>
          </div>
        </div>

        <div v-if="seleccionado.estado === 'en_elaboracion_secretaria'" class="mt-5 flex justify-end border-t border-slate-200 pt-5 dark:border-slate-700">
          <button type="button" class="btn-success" :disabled="procesando || !seleccionado.borrador_word_url" @click="remitir"><i class="pi pi-send"></i> Remitir a Dirección</button>
        </div>

        <div v-if="seleccionado.eventos?.length" class="mt-6 border-t border-slate-200 pt-5 dark:border-slate-700">
          <h4 class="text-sm font-semibold text-slate-900 dark:text-white">Historial</h4>
          <div class="mt-3 space-y-2"><div v-for="evento in [...seleccionado.eventos].reverse()" :key="evento.id_evento" class="grid grid-cols-[110px_minmax(0,1fr)] gap-3 text-xs"><span class="text-slate-500">{{ fechaCorta(evento.fecha) }}</span><span class="text-slate-700 dark:text-slate-300"><strong class="text-slate-950 dark:text-white">{{ evento.usuario }}</strong> · {{ evento.accion }}<small v-if="evento.nota" class="mt-0.5 block text-slate-500">{{ evento.nota }}</small></span></div></div>
        </div>
      </section>
      <section v-else class="card flex items-center justify-center text-sm text-slate-500">Selecciona un trámite de la bandeja.</section>
    </div>
    </template>

    <div v-if="expedienteVista" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm" @click.self="expedienteVista = null">
      <section class="card max-h-[90vh] w-full max-w-5xl overflow-y-auto">
        <header class="flex items-start justify-between gap-4"><div><p class="eyebrow">Expediente en contexto</p><h3 class="section-title mt-1">{{ expedienteVista.nombre_alumno }}</h3><p class="mt-1 text-xs text-slate-500">{{ expedienteVista.codigo_alumno }} · {{ expedienteVista.grado_postula }} · {{ expedienteVista.programa || 'Programa pendiente' }}</p></div><button type="button" class="icon-btn" title="Cerrar" @click="expedienteVista = null"><i class="pi pi-times"></i></button></header>
        <p v-if="expedienteVista.titulo_tesis" class="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-200">{{ expedienteVista.titulo_tesis }}</p>
        <div class="mt-5 grid gap-4 md:grid-cols-3"><div class="rounded border border-slate-200 p-3 text-xs dark:border-slate-700"><p class="input-label">Paso actual</p><p class="font-semibold text-slate-900 dark:text-white">P{{ expedienteVista.id_paso_actual }} · {{ expedienteVista.nombre_paso_actual }}</p><p class="mt-1 text-slate-500">{{ expedienteVista.estado_expediente }}</p></div><div class="rounded border border-slate-200 p-3 text-xs dark:border-slate-700"><p class="input-label">Documentos y tickets</p><p class="font-semibold text-slate-900 dark:text-white">{{ expedienteVista.resoluciones?.length || 0 }} resoluciones · {{ expedienteVista.tickets?.length || 0 }} tickets</p></div><div class="rounded border border-slate-200 p-3 text-xs dark:border-slate-700"><p class="input-label">Requisitos</p><p class="font-semibold text-slate-900 dark:text-white">{{ expedienteVista.resumen_requisitos?.validados || 0 }} validados · {{ expedienteVista.resumen_requisitos?.pendientes || 0 }} pendientes</p></div></div>
        <div class="mt-5 grid gap-4 lg:grid-cols-2"><section><p class="input-label">Resoluciones registradas</p><div class="mt-2 max-h-52 space-y-2 overflow-y-auto"><p v-for="item in expedienteVista.resoluciones || []" :key="item.id_resolucion" class="rounded border border-slate-200 px-3 py-2 text-xs dark:border-slate-700">P{{ item.id_paso_asociado || '-' }} · {{ item.tipo_documento }}<span class="mt-1 block text-slate-500">{{ item.estado_firma }}</span></p><p v-if="!expedienteVista.resoluciones?.length" class="text-xs text-slate-500">No hay resoluciones firmadas registradas.</p></div></section><section><p class="input-label">Docentes asignados</p><div class="mt-2 max-h-52 space-y-2 overflow-y-auto"><p v-for="item in expedienteVista.asignaciones || []" :key="item.id_asignacion" class="rounded border border-slate-200 px-3 py-2 text-xs dark:border-slate-700"><strong>{{ item.nombre_docente }}</strong><span class="mt-1 block text-slate-500">{{ item.rol_asignado }} · {{ item.estado_asignacion }}</span></p><p v-if="!expedienteVista.asignaciones?.length" class="text-xs text-slate-500">No hay docentes asignados.</p></div></section></div>
      </section>
    </div>

    <div v-if="archivoControlUrl" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm" @click.self="cerrarArchivoControl">
      <section class="card flex h-[90vh] w-full max-w-6xl flex-col"><header class="flex items-center justify-between gap-4"><div><p class="eyebrow">Vista previa</p><h3 class="section-title mt-1">{{ archivoControlNombre }}</h3></div><button type="button" class="icon-btn" title="Cerrar" @click="cerrarArchivoControl"><i class="pi pi-times"></i></button></header><iframe :src="archivoControlUrl" class="mt-4 min-h-0 flex-1 rounded border border-slate-200 bg-white dark:border-slate-700" title="Archivo de resolución"></iframe></section>
    </div>

    <div v-if="ticketVista" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm" @click.self="ticketVista = null">
      <section class="card max-h-[90vh] w-full max-w-5xl overflow-y-auto"><header class="flex items-start justify-between gap-4"><div><p class="eyebrow">Ticket vinculado</p><h3 class="section-title mt-1">#{{ ticketVista.numero_visual }} · {{ ticketVista.asunto }}</h3><p class="mt-1 text-xs text-slate-500">{{ ticketVista.fecha || 'Sin fecha' }} · {{ ticketVista.nombre_estudiante_osticket || 'Estudiante sin identificar' }}</p></div><div class="flex gap-2"><button type="button" class="btn-outline btn-sm" @click="imprimirTicket"><i class="pi pi-print"></i> Imprimir</button><button type="button" class="icon-btn" title="Cerrar" @click="ticketVista = null"><i class="pi pi-times"></i></button></div></header><div class="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1fr)_280px]"><article><p class="input-label">Solicitud recibida</p><p class="mt-2 max-h-[430px] overflow-y-auto whitespace-pre-wrap rounded border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-800 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200">{{ ticketVista.cuerpo || 'Sin cuerpo disponible.' }}</p></article><aside class="space-y-4"><section><p class="input-label">Adjuntos</p><div class="mt-2 space-y-2"><button v-for="archivo in ticketVista.adjuntos || []" :key="archivo.id_archivo" type="button" class="flex w-full items-center gap-2 rounded border border-slate-200 px-3 py-2 text-left text-xs hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800" @click="abrirArchivoUrl(archivo.api_archivo_url)"><i class="pi pi-paperclip"></i><span class="min-w-0 truncate">{{ archivo.nombre }}</span><i class="pi pi-external-link ml-auto"></i></button><p v-if="!ticketVista.adjuntos?.length" class="text-xs text-slate-500">Sin adjuntos.</p></div></section><section><p class="input-label">Notas y trazabilidad local</p><div class="mt-2 max-h-60 space-y-2 overflow-y-auto"><p v-for="(evento, indice) in ticketVista.historial_acciones || []" :key="`${evento.fecha}-${indice}`" class="rounded border border-slate-200 px-3 py-2 text-xs dark:border-slate-700"><strong>{{ evento.accion || evento.decision || evento.tipo }}</strong><span v-if="evento.nota" class="mt-1 block text-slate-500">{{ evento.nota }}</span><span class="mt-1 block text-[10px] text-slate-500">{{ evento.usuario || 'Sistema' }} · {{ evento.fecha || '' }}</span></p></div></section></aside></div></section>
    </div>

    <div v-if="editorWordAbierto" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 p-3 backdrop-blur-sm">
      <section class="card flex h-[94vh] w-full max-w-[1500px] flex-col p-3"><header class="flex items-center justify-between gap-3 border-b border-slate-200 pb-3 dark:border-slate-700"><div><p class="eyebrow">Edición institucional</p><h3 class="section-title">{{ seleccionado?.borrador_word_nombre || 'Borrador Word' }}</h3><p class="mt-1 text-xs text-slate-500">Los guardados se registran como una nueva versión del trámite.</p></div><button type="button" class="btn-outline btn-sm" @click="cerrarEditorWord"><i class="pi pi-times"></i> Cerrar editor</button></header><div id="onlyoffice-editor" class="mt-3 min-h-0 flex-1 overflow-hidden rounded border border-slate-200 bg-white dark:border-slate-700"></div></section>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import api from '../api.js'

const estados = 'derivado_secretaria,en_elaboracion_secretaria,consulta_previa,observado_por_direccion,listo_para_direccion'
const tramites = ref([])
const seleccionado = ref(null)
const docentes = ref([])
const modo = ref('trabajo')
const subvista = ref('documento')
const cargando = ref(true)
const procesando = ref(false)
const busqueda = ref('')
const notaRevision = ref('')
const archivoWord = ref(null)
const enlacesGenerados = ref([])
const modelos = ref([])
const modeloSeleccionadoId = ref('')
const vistaModelo = ref(null)
const contenidoBorrador = ref('')
const seleccionLote = ref([])
const modelosLote = ref([])
const modeloLoteId = ref('')
const plantillasTodas = ref([])
const plantillasOficiales = ref([])
const plantillaOficialCodigo = ref('')
const vistaOficial = ref(null)
const vistaPdfUrl = ref('')
const revisionNumeracion = ref(null)
const expedienteVista = ref(null)
const ticketVista = ref(null)
const editorWordAbierto = ref(false)
let instanciaEditorWord = null
let scriptEditorWord = null
const archivoControlUrl = ref('')
const archivoControlNombre = ref('')
const plantillasConsulta = ref([])
const controlNumero = ref({})
const anioControl = ref(new Date().getFullYear())
const aniosControl = Array.from({ length: 8 }, (_, indice) => new Date().getFullYear() - indice)
const resolucionesControl = ref([])
const paginaControl = ref(1)
const paginasControl = ref(1)
const totalControl = ref(0)
const mostrarCatalogo = ref(false)
const busquedaControl = ref('')
const pasoControl = ref('')
const mensaje = ref('')
const error = ref(false)
const preparacion = reactive({ numero: '', fecha: '', referencia_origen: '', requiere_consulta: false, decision_numeracion: '', nota_numeracion: '' })
const consulta = reactive({ id_docente: '', tipo_participacion: 'Dictaminante', canal_correo: 'institucional', vigencia_dias: '', modalidad_respuesta: 'Respuesta', id_plantilla: '', nombre_plantilla: '', asunto: '', mensaje: '' })
const reglaConfirmada = computed(() => seleccionado.value?.regla_paso?.estado_validacion === 'Confirmada')
const consultaDefinida = computed(() => seleccionado.value?.regla_paso?.requiere_consulta_previa !== null && seleccionado.value?.regla_paso?.requiere_consulta_previa !== undefined)
const tiposConsulta = computed(() => {
  const tipos = seleccionado.value?.regla_paso?.tipos_participantes
  return seleccionado.value?.regla_paso?.requiere_consulta_previa && tipos?.length ? tipos : ['Asesor', 'Dictaminante', 'Jurado', 'Replicante']
})
const modalidadesConsulta = computed(() => seleccionado.value?.regla_paso?.modalidades_respuesta?.length ? seleccionado.value.regla_paso.modalidades_respuesta : ['Respuesta', 'Documento', 'Constancia'])
const textoConsultaRegla = computed(() => {
  const regla = seleccionado.value?.regla_paso
  if (!regla || regla.requiere_consulta_previa === null || regla.requiere_consulta_previa === undefined) return 'por validar'
  if (!regla.requiere_consulta_previa) return 'no requerida'
  const tipos = (regla.tipos_participantes || []).join(', ')
  return `${regla.cantidad_aceptaciones ?? 'las'} aceptación(es)${tipos ? ` de ${tipos}` : ''}`
})
const mostrarConsulta = computed(() => Boolean(seleccionado.value?.requiere_consulta_previa || seleccionado.value?.regla_paso?.requiere_consulta_previa || seleccionado.value?.consultas?.length))
const tramitesLote = computed(() => tramites.value.filter(item => seleccionLote.value.includes(item.uuid)))
const puedeOperarLote = computed(() => {
  const lote = tramitesLote.value
  return lote.length > 0 && lote.every(item => item.estado === 'en_elaboracion_secretaria' && item.numero_resolucion && item.fecha_resolucion) && new Set(lote.map(item => item.id_paso)).size === 1
})
const puedeRemitirLote = computed(() => puedeOperarLote.value && tramitesLote.value.every(item => item.borrador_word_url))

function etiquetaEstado(estado) { return ({ derivado_secretaria: 'Pendiente de revisión', en_elaboracion_secretaria: 'En elaboración', consulta_previa: 'Consulta en curso', observado_por_direccion: 'Devuelto por Dirección', listo_para_direccion: 'Remitido a Dirección' })[estado] || estado }
function etiquetaModelo(modelo) { return `R. ${modelo.numero_resolucion || 'sin número'} · ${modelo.fecha_resolucion || 'sin fecha'} · ${modelo.estudiante_referencia || 'sin estudiante'}` }
function etiquetaVariante(variante) { return ({ regular: 'Base', cai: 'CAI', cambio_asesor: 'Cambio de asesor', cambio_dictaminante: 'Cambio de dictaminante', rectificacion: 'Rectificación', dejar_sin_efecto: 'Dejar sin efecto', ampliacion: 'Ampliación', renuncia: 'Renuncia', consejo_epg: 'Consejo EPG' })[variante] || variante }
function fechaCorta(valor) { return valor ? new Date(valor).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' }) : '' }
function cargarFormulario() { if (!seleccionado.value) return; preparacion.numero = seleccionado.value.numero_resolucion || ''; preparacion.fecha = seleccionado.value.fecha_resolucion || new Date().toISOString().slice(0, 10); preparacion.referencia_origen = seleccionado.value.referencia_origen || ''; preparacion.requiere_consulta = seleccionado.value.requiere_consulta_previa; preparacion.decision_numeracion = ''; preparacion.nota_numeracion = ''; revisionNumeracion.value = null; consulta.vigencia_dias = seleccionado.value.regla_paso?.plazo_consulta_dias || ''; if (!tiposConsulta.value.includes(consulta.tipo_participacion)) consulta.tipo_participacion = tiposConsulta.value[0]; if (!modalidadesConsulta.value.includes(consulta.modalidad_respuesta)) consulta.modalidad_respuesta = modalidadesConsulta.value[0] }

async function cargar() {
  cargando.value = true
  try {
    const [res, docentesRes] = await Promise.all([api.get('/resolucion-tramites', { params: { estado: estados, busqueda: busqueda.value || undefined, per_page: 100 } }), api.get('/docentes', { params: { per_page: 100 } })])
    tramites.value = res.data.data
    docentes.value = docentesRes.data.data
    if (seleccionado.value) {
      const vigente = tramites.value.find(item => item.uuid === seleccionado.value.uuid)
      if (vigente) await seleccionar(vigente)
      else seleccionado.value = null
    }
  } catch (e) { mostrarError(e) } finally { cargando.value = false }
}

async function cargarModelos(idPaso) {
  modelos.value = []
  modeloSeleccionadoId.value = ''
  vistaModelo.value = null
  contenidoBorrador.value = ''
  try {
    const [historicos, oficiales] = await Promise.all([api.get('/resolucion-modelos', { params: { id_paso: idPaso } }), api.get('/plantillas-resolucion', { params: { id_paso: idPaso } })])
    modelos.value = historicos.data.data
    plantillasOficiales.value = oficiales.data.data
    plantillaOficialCodigo.value = plantillasOficiales.value.find(item => item.variante === 'regular')?.codigo || plantillasOficiales.value[0]?.codigo || ''
    vistaOficial.value = null
  } catch (e) { mostrarError(e) }
}
async function seleccionar(item) { const res = await api.get(`/resolucion-tramites/${item.uuid}`); seleccionado.value = res.data; enlacesGenerados.value = []; cargarFormulario(); await cargarModelos(seleccionado.value.id_paso) }
function mostrarError(e) { const detalle = e.response?.data?.detail; error.value = true; mensaje.value = typeof detalle === 'string' ? detalle : detalle?.mensaje || e.response?.data?.mensaje || 'No se pudo completar la acción.' }
async function ejecutar(fn, texto, alCompletar = null) { procesando.value = true; mensaje.value = ''; try { await fn(); error.value = false; mensaje.value = texto; await cargar(); if (alCompletar) alCompletar() } catch (e) { mostrarError(e) } finally { procesando.value = false } }
function revisar(accion) { ejecutar(() => api.post(`/resolucion-tramites/${seleccionado.value.uuid}/revisar`, { accion, nota: notaRevision.value || null }), accion === 'Aceptar' ? 'Trámite aceptado para elaboración.' : 'El trámite volvió al tramitador con la observación.') }
function guardarBorrador() { const form = new FormData(); form.append('numero_resolucion', preparacion.numero); form.append('fecha_resolucion', preparacion.fecha); form.append('requiere_consulta_previa', preparacion.requiere_consulta); if (preparacion.referencia_origen) form.append('referencia_origen', preparacion.referencia_origen); if (preparacion.decision_numeracion) form.append('decision_numeracion', preparacion.decision_numeracion); if (preparacion.nota_numeracion) form.append('nota_numeracion', preparacion.nota_numeracion); if (archivoWord.value) form.append('archivo_word', archivoWord.value); ejecutar(() => api.post(`/resolucion-tramites/${seleccionado.value.uuid}/preparar`, form), 'Borrador y datos guardados.') }
function descartarBorrador() { if (!confirm('Se liberará el número y se retirará el Word de esta preparación. El historial anterior seguirá en auditoría. ¿Continuar?')) return; ejecutar(() => api.post(`/resolucion-tramites/${seleccionado.value.uuid}/descartar-borrador`, { nota: 'Preparación descartada desde la mesa de Secretaría.' }), 'La preparación fue descartada y el número quedó libre.') }
async function cargarVistaModelo() {
  if (!modeloSeleccionadoId.value || !seleccionado.value) return
  procesando.value = true
  try {
    const res = await api.get(`/resolucion-modelos/${modeloSeleccionadoId.value}/vista-previa`, { params: { tramite_ref: seleccionado.value.uuid } })
    vistaModelo.value = res.data
    contenidoBorrador.value = res.data.contenido
    error.value = false
  } catch (e) { mostrarError(e) } finally { procesando.value = false }
}
function generarBorrador() {
  ejecutar(
    () => api.post(`/resolucion-tramites/${seleccionado.value.uuid}/generar-borrador`, {
      id_modelo_documento: Number(modeloSeleccionadoId.value), contenido: contenidoBorrador.value,
      numero_resolucion: preparacion.numero, fecha_resolucion: preparacion.fecha,
      referencia_origen: preparacion.referencia_origen || null,
    }),
    'Word generado desde el modelo. Revísalo antes de remitirlo a Dirección.',
  )
}
async function cargarVistaOficial() {
  if (!plantillaOficialCodigo.value || !seleccionado.value) return
  procesando.value = true
  try {
    if (vistaPdfUrl.value) URL.revokeObjectURL(vistaPdfUrl.value)
    const params = { numero_resolucion: preparacion.numero, fecha_resolucion: preparacion.fecha }
    const [detalle, pdf] = await Promise.all([
      api.get(`/resolucion-tramites/${seleccionado.value.uuid}/plantilla-oficial/${plantillaOficialCodigo.value}/vista-previa`, { params }),
      api.get(`/resolucion-tramites/${seleccionado.value.uuid}/plantilla-oficial/${plantillaOficialCodigo.value}/vista-previa-pdf`, { params, responseType: 'blob' }),
    ])
    vistaOficial.value = detalle.data
    vistaPdfUrl.value = URL.createObjectURL(pdf.data)
    error.value = false
  } catch (e) { mostrarError(e) } finally { procesando.value = false }
}
function generarOficial() {
  ejecutar(
    () => api.post(`/resolucion-tramites/${seleccionado.value.uuid}/generar-borrador-oficial`, { codigo_plantilla: plantillaOficialCodigo.value, numero_resolucion: preparacion.numero, fecha_resolucion: preparacion.fecha, referencia_origen: preparacion.referencia_origen || null, decision_numeracion: preparacion.decision_numeracion || null, nota_numeracion: preparacion.nota_numeracion || null }),
    'Word generado con la plantilla oficial. Revisa la vista final antes de remitirlo.',
  )
}
async function actualizarModelosLote() {
  const lote = tramitesLote.value
  modeloLoteId.value = ''
  modelosLote.value = []
  if (!lote.length || new Set(lote.map(item => item.id_paso)).size !== 1) return
  try { modelosLote.value = (await api.get('/resolucion-modelos', { params: { id_paso: lote[0].id_paso } })).data.data } catch (e) { mostrarError(e) }
}
function generarLote() {
  if (!confirm(`Se generarán ${seleccionLote.value.length} Word usando el modelo seleccionado. Cada borrador seguirá requiriendo revisión. ¿Continuar?`)) return
  ejecutar(
    () => api.post('/resolucion-tramites/generar-borradores-lote', { id_modelo_documento: Number(modeloLoteId.value), tramites: seleccionLote.value }),
    `Se generaron ${seleccionLote.value.length} borradores Word en lote.`,
    () => { seleccionLote.value = []; modelosLote.value = []; modeloLoteId.value = '' },
  )
}
function remitirLote() {
  if (!confirm(`Se remitirán ${seleccionLote.value.length} trámites ya validados a Dirección. Esta acción cambia sus estados locales. ¿Continuar?`)) return
  ejecutar(
    () => api.post('/resolucion-tramites/remitir-direccion-lote', { tramites: seleccionLote.value }),
    `Se remitieron ${seleccionLote.value.length} trámites a Dirección.`,
    () => { seleccionLote.value = []; modelosLote.value = []; modeloLoteId.value = '' },
  )
}
function aplicarPlantillaConsulta() { const plantilla = plantillasConsulta.value.find(item => item.id_plantilla === Number(consulta.id_plantilla)); if (!plantilla) return; consulta.asunto = plantilla.asunto; consulta.mensaje = plantilla.mensaje; consulta.modalidad_respuesta = plantilla.modalidad_respuesta }
async function guardarPlantillaConsulta() { procesando.value = true; try { await api.post('/resolucion-consulta-plantillas', { nombre: consulta.nombre_plantilla, asunto: consulta.asunto, mensaje: consulta.mensaje, modalidad_respuesta: consulta.modalidad_respuesta, activa: true }); consulta.nombre_plantilla = ''; await cargarCatalogos(); mensaje.value = 'Mensaje guardado como plantilla.'; error.value = false } catch (e) { mostrarError(e) } finally { procesando.value = false } }
async function crearConsulta() { procesando.value = true; try { const res = await api.post(`/resolucion-tramites/${seleccionado.value.uuid}/consultas`, { participantes: [{ id_docente: Number(consulta.id_docente), tipo_participacion: consulta.tipo_participacion, canal_correo: consulta.canal_correo }], vigencia_dias: Number(consulta.vigencia_dias), modalidad_respuesta: consulta.modalidad_respuesta, asunto: consulta.asunto || null, mensaje: consulta.mensaje || null }); const nuevosEnlaces = res.data.consultas; await seleccionar(seleccionado.value); enlacesGenerados.value = nuevosEnlaces; error.value = false; mensaje.value = res.data.advertencia } catch (e) { mostrarError(e) } finally { procesando.value = false } }
function remitir() { ejecutar(() => api.post(`/resolucion-tramites/${seleccionado.value.uuid}/remitir-direccion`), 'Resolución remitida a Dirección.') }
async function copiar(texto) { await navigator.clipboard.writeText(texto); mensaje.value = 'Enlace copiado.'; error.value = false }
async function revisarNumeracion() { if (!seleccionado.value || !preparacion.numero.trim()) return; try { revisionNumeracion.value = (await api.get(`/resolucion-tramites/${seleccionado.value.uuid}/numeracion`, { params: { numero_resolucion: preparacion.numero } })).data } catch (e) { mostrarError(e) } }
function usarSiguienteNumero() { if (controlNumero.value.siguiente_disponible) { preparacion.numero = controlNumero.value.siguiente_disponible; revisionNumeracion.value = null; revisarNumeracion() } }
async function abrirExpediente() { if (!seleccionado.value) return; try { expedienteVista.value = (await api.get(`/expedientes/${seleccionado.value.expediente_uuid}`)).data } catch (e) { mostrarError(e) } }
async function abrirTicket() { if (!seleccionado.value?.ticket_uuid) return; try { ticketVista.value = (await api.get(`/tickets/${seleccionado.value.ticket_uuid}`)).data } catch (e) { mostrarError(e) } }
function cargarScriptEditor(url) {
  if (window.DocsAPI?.DocEditor) return Promise.resolve()
  if (scriptEditorWord?.src === url) return new Promise((resolve, reject) => { scriptEditorWord.addEventListener('load', resolve, { once: true }); scriptEditorWord.addEventListener('error', reject, { once: true }) })
  return new Promise((resolve, reject) => {
    scriptEditorWord = document.createElement('script')
    scriptEditorWord.src = url
    scriptEditorWord.async = true
    scriptEditorWord.onload = resolve
    scriptEditorWord.onerror = () => reject(new Error('No se pudo cargar el editor Word institucional.'))
    document.head.appendChild(scriptEditorWord)
  })
}
async function abrirEditorWord() {
  if (!seleccionado.value?.borrador_word_url) return
  procesando.value = true
  try {
    const respuesta = await api.get(`/resolucion-tramites/${seleccionado.value.uuid}/onlyoffice-config`)
    editorWordAbierto.value = true
    await nextTick()
    await cargarScriptEditor(respuesta.data.editor_api_url)
    if (!window.DocsAPI?.DocEditor) throw new Error('El editor Word no se inicializó correctamente.')
    instanciaEditorWord?.destroyEditor?.()
    instanciaEditorWord = new window.DocsAPI.DocEditor('onlyoffice-editor', {
      ...respuesta.data.configuracion,
      events: {
        onError: (evento) => { mensaje.value = `El editor Word informó un problema (${evento?.data?.errorCode || 'sin código'}).`; error.value = true },
        onDocumentStateChange: (evento) => { if (!evento?.data) { mensaje.value = 'La edición fue guardada por el servidor. Actualiza el trámite para ver la nueva versión.'; error.value = false } },
      },
    })
    error.value = false
  } catch (e) {
    editorWordAbierto.value = false
    mostrarError(e)
  } finally { procesando.value = false }
}
async function cerrarEditorWord() {
  instanciaEditorWord?.destroyEditor?.()
  instanciaEditorWord = null
  editorWordAbierto.value = false
  await cargar()
}
function escaparHtml(valor = '') { return String(valor).replace(/[&<>\"']/g, caracter => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[caracter]) }
function imprimirTicket() {
  if (!ticketVista.value) return
  const ticket = ticketVista.value
  const adjuntos = (ticket.adjuntos || []).map(item => `<li>${escaparHtml(item.nombre)}</li>`).join('') || '<li>Sin adjuntos.</li>'
  const eventos = (ticket.historial_acciones || []).map(item => `<li><strong>${escaparHtml(item.accion || item.decision || item.tipo || 'Evento')}</strong>${item.nota ? `<br>${escaparHtml(item.nota)}` : ''}<br><small>${escaparHtml(item.usuario || 'Sistema')} · ${escaparHtml(item.fecha || '')}</small></li>`).join('') || '<li>Sin notas internas registradas.</li>'
  const ventana = window.open('', '_blank')
  if (!ventana) { mensaje.value = 'El navegador bloqueó la ventana de impresión. Permite ventanas emergentes para este sitio.'; error.value = true; return }
  ventana.document.write(`<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Ticket ${escaparHtml(ticket.numero_visual)}</title><style>body{font:13px Arial,sans-serif;color:#111;margin:32px;line-height:1.5}h1{font-size:20px;margin:0 0 4px}h2{font-size:14px;margin-top:26px;border-bottom:1px solid #ccc;padding-bottom:5px}small{color:#555}pre{white-space:pre-wrap;font:13px Arial,sans-serif;border:1px solid #ddd;padding:14px}li{margin:7px 0}</style></head><body><h1>Ticket #${escaparHtml(ticket.numero_visual)}</h1><p>${escaparHtml(ticket.asunto || 'Sin asunto')}<br><small>${escaparHtml(ticket.fecha || '')} · ${escaparHtml(ticket.nombre_estudiante_osticket || 'Estudiante sin identificar')}</small></p><h2>Solicitud recibida</h2><pre>${escaparHtml(ticket.cuerpo || 'Sin cuerpo disponible.')}</pre><h2>Adjuntos</h2><ul>${adjuntos}</ul><h2>Notas y trazabilidad local</h2><ul>${eventos}</ul></body></html>`)
  ventana.document.close()
  ventana.focus()
  ventana.print()
}
async function cargarCatalogos() {
  try {
    const [plantillas, mensajes, numeracion] = await Promise.all([api.get('/plantillas-resolucion'), api.get('/resolucion-consulta-plantillas'), api.get('/resoluciones/control-numeracion', { params: { anio: anioControl.value } })])
    plantillasTodas.value = plantillas.data.data || []
    plantillasConsulta.value = mensajes.data.data || []
    controlNumero.value = numeracion.data || {}
  } catch (e) { mostrarError(e) }
}
async function cargarResolucionesControl() {
  try {
    const respuesta = (await api.get('/resoluciones', { params: { vista: 'oficial', anio: anioControl.value, id_paso: pasoControl.value || undefined, busqueda: busquedaControl.value || undefined, page: paginaControl.value, per_page: 50 } })).data
    resolucionesControl.value = respuesta.data || []
    paginasControl.value = respuesta.total_pages || 1
    totalControl.value = respuesta.total || 0
  } catch (e) { mostrarError(e) }
}
async function cargarControl() { await Promise.all([cargarCatalogos(), cargarResolucionesControl()]) }
async function abrirControl() { modo.value = 'control'; await cargarControl() }
async function buscarControl() { paginaControl.value = 1; await cargarResolucionesControl() }
async function cambiarPaginaControl(direccion) { paginaControl.value += direccion; await cargarResolucionesControl() }
async function abrirArchivoUrl(url) { try { const respuesta = await api.get(url, { responseType: 'blob' }); if (archivoControlUrl.value) URL.revokeObjectURL(archivoControlUrl.value); archivoControlUrl.value = URL.createObjectURL(respuesta.data); archivoControlNombre.value = 'Resolución registrada' } catch (e) { mostrarError(e) } }
async function abrirArchivoControl(item) { await abrirArchivoUrl(item.api_archivo_url); archivoControlNombre.value = `${item.resolucion_numero || 'Resolución'}-${item.resolucion_anio || ''}` }
function cerrarArchivoControl() { if (archivoControlUrl.value) URL.revokeObjectURL(archivoControlUrl.value); archivoControlUrl.value = ''; archivoControlNombre.value = '' }

onMounted(async () => { await Promise.all([cargar(), cargarCatalogos()]) })
onBeforeUnmount(() => { instanciaEditorWord?.destroyEditor?.(); if (vistaPdfUrl.value) URL.revokeObjectURL(vistaPdfUrl.value); cerrarArchivoControl() })
</script>
