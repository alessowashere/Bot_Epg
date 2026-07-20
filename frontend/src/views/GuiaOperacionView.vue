<template>
  <div class="page-shell guide-page">
    <section class="guide-heading" aria-labelledby="guia-titulo">
      <div>
        <p class="eyebrow"><i class="pi pi-compass mr-2"></i>Guía de operación</p>
        <h2 id="guia-titulo" class="page-title">Así se mueve un expediente</h2>
        <p class="page-subtitle max-w-3xl">Un mapa para ubicar cada tarea, saber quién actúa y distinguir lo que el sistema registra de lo que sigue siendo una decisión humana.</p>
      </div>
      <nav class="guide-anchor-nav" aria-label="Secciones de la guía">
        <a href="#empezar">Empezar</a>
        <a href="#resolucion">Resolución</a>
        <a href="#pasos">7 pasos</a>
        <a href="#tickets">Tickets</a>
        <a href="#control">Control documental</a>
        <a href="#limites">Límites</a>
      </nav>
    </section>

    <section id="empezar" class="guide-section" aria-labelledby="empezar-titulo">
      <div class="guide-section-heading">
        <div>
          <p class="eyebrow">Tu jornada</p>
          <h3 id="empezar-titulo" class="section-title">{{ rutaRol.titulo }}</h3>
        </div>
        <span class="badge badge-proceso"><i :class="rutaRol.icono" class="pi"></i> {{ etiquetaRol }}</span>
      </div>
      <p class="guide-intro">{{ rutaRol.resumen }}</p>
      <div class="start-grid">
        <article v-for="(paso, indice) in rutaRol.pasos" :key="paso.titulo" class="start-item">
          <span class="start-number">{{ indice + 1 }}</span>
          <div><h4>{{ paso.titulo }}</h4><p>{{ paso.descripcion }}</p></div>
        </article>
      </div>
      <div class="guide-note guide-note-sky"><i class="pi pi-lightbulb"></i><p><strong>Regla simple:</strong> no uses el expediente para adivinar qué hacer con un ingreso. Primero decide el ticket; cuando corresponde, el sistema conserva el ticket como antecedente y lo remite al siguiente rol.</p></div>
    </section>

    <section id="resolucion" class="guide-section" aria-labelledby="flujo-titulo">
      <div class="guide-section-heading">
        <div>
          <p class="eyebrow">Circuito principal</p>
          <h3 id="flujo-titulo" class="section-title">De la solicitud a la resolución registrada</h3>
        </div>
        <span class="badge badge-proceso"><i class="pi pi-lock"></i> Cada avance queda auditado</span>
      </div>

      <ol class="resolution-flow">
        <li v-for="(etapa, index) in etapasResolucion" :key="etapa.nombre" class="flow-stage">
          <div class="flow-connector" aria-hidden="true"><i v-if="index < etapasResolucion.length - 1" class="pi pi-arrow-right"></i></div>
          <div :class="etapa.color" class="flow-icon"><i :class="etapa.icono" class="pi"></i></div>
          <div class="flow-copy">
            <p class="flow-role">{{ etapa.rol }}</p>
            <h4>{{ etapa.nombre }}</h4>
            <p>{{ etapa.descripcion }}</p>
          </div>
        </li>
      </ol>

      <div class="guide-note guide-note-sky">
        <i class="pi pi-info-circle" aria-hidden="true"></i>
        <p><strong>Consulta previa no es designación.</strong> En P1, P2, P5 y P6 solo confirma disponibilidad. La designación formal nace después, dentro de la resolución.</p>
      </div>
    </section>

    <section id="pasos" class="guide-section" aria-labelledby="pasos-titulo">
      <div class="guide-section-heading">
        <div>
          <p class="eyebrow">Expediente académico</p>
          <h3 id="pasos-titulo" class="section-title">Los siete pasos y su regla base</h3>
        </div>
        <router-link to="/i9" class="btn-outline btn-sm"><i class="pi pi-sliders-h"></i> Ver reglas por paso</router-link>
      </div>

      <div class="steps-grid">
        <article v-for="paso in pasos" :key="paso.numero" class="step-guide-item">
          <div class="step-guide-top">
            <span class="step-guide-number">{{ paso.numero }}</span>
            <span :class="paso.consulta ? 'badge-nuevo' : 'badge-caduco'" class="badge">{{ paso.consulta ? 'Consulta previa' : 'Sin consulta' }}</span>
          </div>
          <h4>{{ paso.nombre }}</h4>
          <p>{{ paso.detalle }}</p>
          <div class="step-guide-footer">
            <i :class="paso.origenIcono" class="pi"></i><span>{{ paso.origen }}</span>
          </div>
        </article>
      </div>
    </section>

    <section class="guide-section" aria-labelledby="roles-titulo">
      <div class="guide-section-heading">
        <div>
          <p class="eyebrow">Responsabilidades</p>
          <h3 id="roles-titulo" class="section-title">Quién hace cada parte</h3>
        </div>
      </div>

      <div class="roles-grid">
        <article v-for="rol in roles" :key="rol.nombre" class="role-guide-item">
          <div :class="rol.color" class="role-guide-icon"><i :class="rol.icono" class="pi"></i></div>
          <div>
            <h4>{{ rol.nombre }}</h4>
            <p>{{ rol.resumen }}</p>
            <ul>
              <li v-for="tarea in rol.tareas" :key="tarea"><i class="pi pi-check"></i>{{ tarea }}</li>
            </ul>
          </div>
        </article>
      </div>
    </section>

    <section id="tickets" class="guide-section" aria-labelledby="tickets-titulo">
      <div class="guide-section-heading">
        <div>
          <p class="eyebrow">Mesa operativa y archivo</p>
          <h3 id="tickets-titulo" class="section-title">Del ticket recibido al candidato para resolución</h3>
        </div>
        <router-link to="/i2" class="btn-outline btn-sm"><i class="pi pi-list-check"></i> Abrir Mesa de tickets</router-link>
      </div>

      <div class="guide-note guide-note-sky" aria-label="Flujo de clasificación de tickets">
        <i class="pi pi-sitemap" aria-hidden="true"></i>
        <div>
          <p><strong>Mesa de tickets</strong> es la pantalla de trabajo diario: decidir, vincular o crear el primer expediente y enviar a Secretaría.</p>
          <p class="mt-1"><strong>Archivo de tickets</strong> sirve para buscar cualquier ingreso sincronizado, incluidos históricos, cerrados y asuntos fuera del proceso. No es otra cola de trabajo.</p>
          <p class="mt-2 font-mono text-xs">Ticket → decisión → expediente (si falta) → Secretaría → Dirección → cierre local</p>
        </div>
      </div>

      <div class="ticket-map" role="list" aria-label="Decisiones disponibles para tickets">
        <article v-for="decision in decisionesTicket" :key="decision.nombre" class="ticket-decision" role="listitem">
          <span :class="decision.color" class="ticket-decision-icon"><i :class="decision.icono" class="pi"></i></span>
          <div>
            <h4>{{ decision.nombre }}</h4>
            <p>{{ decision.descripcion }}</p>
          </div>
        </article>
      </div>

      <div class="guide-note guide-note-amber">
        <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
        <p><strong>Vincular no equivale a resolver.</strong> Al elegir “Requiere resolución”, un ticket con expediente se envía a Secretaría; si no tiene expediente, se crea el primero y se envía en la misma acción. No se firma ni se cierra automáticamente.</p>
      </div>
    </section>

    <section id="control" class="guide-section" aria-labelledby="control-titulo">
      <div class="guide-section-heading">
        <div>
          <p class="eyebrow">Secretaría Académica</p>
          <h3 id="control-titulo" class="section-title">Mesa de Secretaría y control de resoluciones</h3>
        </div>
        <router-link to="/i6" class="btn-outline btn-sm"><i class="pi pi-file-edit"></i> Abrir Secretaría</router-link>
      </div>

      <div class="resolution-control-grid">
        <article v-for="item in controlDocumental" :key="item.titulo" class="control-guide-item">
          <span :class="item.color" class="role-guide-icon"><i :class="item.icono" class="pi"></i></span>
          <div><h4>{{ item.titulo }}</h4><p>{{ item.descripcion }}</p></div>
        </article>
      </div>
      <div class="guide-note guide-note-amber">
        <i class="pi pi-wrench" aria-hidden="true"></i>
        <p><strong>Diagnóstico de extracción y Fuera del catálogo no equivalen a trabajo pendiente.</strong> El acervo histórico conserva compilados, actas y oficios para auditoría. Solo “Revisión prioritaria” reúne resoluciones reconocibles que todavía necesitan completar un dato documental.</p>
      </div>
    </section>

    <section id="limites" class="guide-section" aria-labelledby="limites-titulo">
      <div class="guide-section-heading">
        <div>
          <p class="eyebrow">Control institucional</p>
          <h3 id="limites-titulo" class="section-title">Lo que el sistema hace y lo que todavía no ejecuta</h3>
        </div>
      </div>

      <div class="limits-grid">
        <article v-for="limite in limites" :key="limite.titulo" class="limit-item">
          <i :class="limite.icono" class="pi"></i>
          <div><h4>{{ limite.titulo }}</h4><p>{{ limite.descripcion }}</p></div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()
const rutasPorRol = {
  Administrador: {
    titulo: 'Administra sin reemplazar el trabajo operativo', icono: 'pi-cog',
    resumen: 'Usa el panel para supervisar salud técnica, usuarios, reglas y excepciones. Para entender una tarea concreta, puedes entrar en vista de rol de solo lectura.',
    pasos: [
      { titulo: 'Revisa el panel', descripcion: 'Comprueba sincronización, errores y volumen; no clasifiques tickets por rutina.' },
      { titulo: 'Mantén reglas y usuarios', descripcion: 'Configura lo institucional y corrige accesos sin conocer contraseñas ajenas.' },
      { titulo: 'Intervén solo ante excepción', descripcion: 'Los tickets y resoluciones siguen la responsabilidad de cada rol.' },
    ],
  },
  Recepcion: {
    titulo: 'Empieza por los ingresos, no por los expedientes', icono: 'pi-inbox',
    resumen: 'Tu trabajo es decidir el destino del ticket. El sistema se encarga de conservar adjuntos, vincular el contexto y enviar a Secretaría cuando corresponde.',
    pasos: [
      { titulo: 'Abre Mesa de tickets', descripcion: 'Empieza en “Decidir y enviar”; allí ya hay un expediente relacionado.' },
      { titulo: 'Decide una vez', descripcion: 'Marca requiere resolución, no corresponde, transferir o cerrar interno. No hagas una segunda derivación.' },
      { titulo: 'Solo crea cuando sea el primero', descripcion: 'En “Sin expediente”, busca antecedentes. Si no existe, crea y envía el expediente inicial.' },
    ],
  },
  Secretaria_Academica: {
    titulo: 'Trabaja únicamente lo que llegó a tu cola', icono: 'pi-file-edit',
    resumen: 'Tramitación ya decidió el ingreso. Secretaría verifica el expediente, prepara el Word, realiza consultas previas cuando la regla lo exige y remite a Dirección.',
    pasos: [
      { titulo: 'Abre Secretaría Académica', descripcion: 'Cada trámite recibido ya conserva su ticket, expediente y paso de flujo.' },
      { titulo: 'Prepara el documento', descripcion: 'Revisa requisitos, genera o carga el Word y registra número, fecha y referencia ERP cuando aplique.' },
      { titulo: 'Remite a Dirección', descripcion: 'Solo cuando el documento y consultas obligatorias estén completos.' },
    ],
  },
  Directora: {
    titulo: 'Revisa y firma el documento final', icono: 'pi-shield',
    resumen: 'Dirección recibe documentos preparados por Secretaría. Puede observarlos o cargar el PDF firmado para devolverlos al cierre institucional.',
    pasos: [
      { titulo: 'Abre Dirección', descripcion: 'Revisa los trámites listos, no los tickets de ingreso.' },
      { titulo: 'Observa o firma', descripcion: 'Una observación vuelve a Secretaría. El PDF firmado se carga como evidencia final.' },
      { titulo: 'Devuelve al circuito', descripcion: 'Tramitación registra la constancia o notificación exigida por el paso.' },
    ],
  },
  Dictaminante: {
    titulo: 'Responde solo la consulta que recibiste', icono: 'pi-user-edit',
    resumen: 'El enlace temporal permite responder, adjuntar evidencia o dejar constancia sin cuenta institucional.',
    pasos: [
      { titulo: 'Abre el enlace recibido', descripcion: 'El enlace tiene duración limitada y corresponde a una consulta puntual.' },
      { titulo: 'Indica disponibilidad', descripcion: 'Aceptar una consulta no equivale a una designación formal.' },
      { titulo: 'Adjunta evidencia si se solicita', descripcion: 'La respuesta vuelve al trámite de Secretaría para continuar el circuito.' },
    ],
  },
}

const etiquetaRol = computed(() => ({
  Administrador: 'Administración', Recepcion: 'Tramitación', Secretaria_Academica: 'Secretaría Académica', Directora: 'Dirección', Dictaminante: 'Dictaminante',
}[auth.rol] || 'Operación'))
const rutaRol = computed(() => rutasPorRol[auth.rol] || rutasPorRol.Recepcion)

const etapasResolucion = [
  { rol: 'Tramitación', nombre: 'Decide y deriva', descripcion: 'Clasifica el ticket; si corresponde, el sistema crea el trámite y lo deja en Secretaría.', icono: 'pi-send', color: 'bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300' },
  { rol: 'Secretaría Académica', nombre: 'Prepara', descripcion: 'Registra número y fecha, adjunta el Word y realiza consultas si la regla las exige.', icono: 'pi-file-edit', color: 'bg-violet-100 text-violet-700 dark:bg-violet-500/15 dark:text-violet-300' },
  { rol: 'Dirección', nombre: 'Revisa y firma', descripcion: 'Observa o devuelve el PDF firmado con ReFirma al circuito interno.', icono: 'pi-verified', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300' },
  { rol: 'Tramitación', nombre: 'Registra cierre', descripcion: 'Confirma las constancias obligatorias para cada destinatario del paso.', icono: 'pi-check-square', color: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300' },
]

const pasos = [
  { numero: 1, nombre: 'Nombramiento de asesor', detalle: 'Consulta a un asesor antes de la resolución.', consulta: true, origen: 'Mesa de Partes Virtual', origenIcono: 'pi-inbox' },
  { numero: 2, nombre: 'Dictamen de proyecto', detalle: 'Consulta a dos dictaminantes antes de resolver.', consulta: true, origen: 'Mesa de Partes Virtual', origenIcono: 'pi-inbox' },
  { numero: 3, nombre: 'Inscripción del proyecto', detalle: 'Nace con dos dictámenes favorables; no consulta disponibilidad.', consulta: false, origen: 'Expediente EPG', origenIcono: 'pi-folder-open' },
  { numero: 4, nombre: 'Declaratoria de apto', detalle: 'Se origina en ERP y exige la referencia institucional.', consulta: false, origen: 'ERP Universitario', origenIcono: 'pi-database' },
  { numero: 5, nombre: 'Dictamen de tesis', detalle: 'Consulta a dos dictaminantes antes de resolver.', consulta: true, origen: 'Mesa de Partes Virtual', origenIcono: 'pi-inbox' },
  { numero: 6, nombre: 'Sustentación', detalle: 'Consulta a cuatro jurados: dictaminantes y replicantes.', consulta: true, origen: 'Mesa de Partes Virtual', origenIcono: 'pi-inbox' },
  { numero: 7, nombre: 'Trámite del diploma', detalle: 'Concluye al cargar la resolución firmada en el repositorio.', consulta: false, origen: 'ERP Universitario', origenIcono: 'pi-database' },
]

const roles = [
  { nombre: 'Tramitación', resumen: 'Recibe y decide el destino de cada ingreso.', icono: 'pi-send', color: 'bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300', tareas: ['Clasifica tickets', 'Vincula o crea el primer expediente', 'Registra constancias locales'] },
  { nombre: 'Secretaría Académica', resumen: 'Convierte el expediente en un proyecto de resolución verificable.', icono: 'pi-file-edit', color: 'bg-violet-100 text-violet-700 dark:bg-violet-500/15 dark:text-violet-300', tareas: ['Revisa u observa', 'Carga Word y consultas', 'Remite a Dirección'] },
  { nombre: 'Dirección', resumen: 'Controla el documento final antes de devolverlo al circuito.', icono: 'pi-shield', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300', tareas: ['Observa el Word', 'Firma con ReFirma', 'Carga el PDF firmado'] },
]

const decisionesTicket = [
  { nombre: 'Vincular expediente', descripcion: 'Relaciona el ticket con un expediente oficial existente. No lo cierra.', icono: 'pi-link', color: 'bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300' },
  { nombre: 'Requiere resolución', descripcion: 'Con expediente, se envía automáticamente a Secretaría. Sin expediente, permite crear el primero y enviarlo.', icono: 'pi-file-edit', color: 'bg-violet-100 text-violet-700 dark:bg-violet-500/15 dark:text-violet-300' },
  { nombre: 'No corresponde', descripcion: 'Clasifica cursos, convalidaciones u otros asuntos fuera de los siete pasos.', icono: 'pi-directions-alt', color: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300' },
  { nombre: 'Transferir o cerrar interno', descripcion: 'Registra una decisión local; no modifica osTicket automáticamente.', icono: 'pi-arrow-right-arrow-left', color: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200' },
]

const controlDocumental = [
  { titulo: '1. Recibir el trámite', descripcion: 'La Mesa de Secretaría solo muestra lo que Tramitación ya clasificó y derivó internamente.', icono: 'pi-inbox', color: 'bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300' },
  { titulo: '2. Preparar el Word', descripcion: 'Elige el tipo de resolución, reserva o corrige el número, revisa los datos y genera la vista previa desde una plantilla oficial.', icono: 'pi-file-word', color: 'bg-violet-100 text-violet-700 dark:bg-violet-500/15 dark:text-violet-300' },
  { titulo: '3. Consultar cuando aplica', descripcion: 'En P1, P2, P5 y P6 genera enlaces temporales y elige correo institucional, personal o ambos.', icono: 'pi-link', color: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300' },
  { titulo: '4. Controlar el archivo', descripcion: 'El archivo utilizable reúne resoluciones verificadas. Revisión prioritaria, diagnóstico técnico y documentos fuera del catálogo permanecen separados del trabajo diario.', icono: 'pi-book', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300' },
]

const limites = [
  { titulo: 'Sin envíos automáticos', descripcion: 'El sistema prepara enlaces y textos, pero no envía correos.', icono: 'pi-send' },
  { titulo: 'Sin cambios externos', descripcion: 'No ejecuta acciones en ERP, osTicket, ReFirma ni Drive.', icono: 'pi-lock' },
  { titulo: 'Repositorio interno', descripcion: 'Word, PDF y evidencia quedan trazados con versión y hash.', icono: 'pi-folder' },
  { titulo: 'Sesión protegida', descripcion: 'Una cuenta conserva una sesión normal activa y puede cerrar las demás.', icono: 'pi-shield' },
]
</script>

<style scoped>
.guide-page { max-width: 1480px; padding-bottom: 2.5rem; }
.guide-heading { display: flex; align-items: end; justify-content: space-between; gap: 1.75rem; border-bottom: 1px solid rgb(226 232 240); padding: .35rem 0 1.5rem; }
.eyebrow { margin: 0; color: rgb(3 105 161); font-size: .72rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.guide-anchor-nav { display: flex; flex-wrap: wrap; gap: .35rem; }
.guide-anchor-nav a { border: 1px solid rgb(203 213 225); border-radius: .375rem; color: rgb(51 65 85); font-size: .75rem; font-weight: 700; padding: .42rem .65rem; text-decoration: none; }
.guide-anchor-nav a:hover { border-color: rgb(14 165 233); color: rgb(3 105 161); }
.guide-section { border-bottom: 1px solid rgb(226 232 240); padding: 2.15rem 0; scroll-margin-top: 1rem; }
.guide-section-heading { align-items: center; display: flex; gap: 1rem; justify-content: space-between; margin-bottom: 1.35rem; }
.guide-section-heading .section-title { font-size: 1.05rem; margin: .2rem 0 0; }
.guide-intro { color: rgb(71 85 105); font-size: .84rem; line-height: 1.6; margin: 0 0 1.35rem; max-width: 860px; }
.start-grid { display: grid; gap: 1.25rem; grid-template-columns: repeat(3, minmax(0, 1fr)); }
.start-item { align-items: flex-start; border-left: 2px solid rgb(56 189 248); display: flex; gap: .75rem; min-height: 5.4rem; padding: .35rem 0 .35rem .9rem; }
.start-number { align-items: center; background: rgb(19 46 102); border-radius: 50%; color: white; display: inline-flex; flex: 0 0 auto; font-size: .7rem; font-weight: 800; height: 1.45rem; justify-content: center; width: 1.45rem; }
.start-item h4 { color: rgb(15 23 42); font-size: .84rem; margin: 0; }
.start-item p { color: rgb(71 85 105); font-size: .76rem; line-height: 1.55; margin: .32rem 0 0; }
.resolution-flow { display: grid; gap: 1.25rem; grid-template-columns: repeat(4, minmax(0, 1fr)); list-style: none; margin: 0; padding: .15rem 0; }
.flow-stage { min-width: 0; padding-right: .3rem; position: relative; }
.flow-icon, .role-guide-icon, .ticket-decision-icon { align-items: center; border-radius: .375rem; display: inline-flex; height: 2.25rem; justify-content: center; width: 2.25rem; }
.flow-copy { margin-top: .8rem; }
.flow-copy h4, .step-guide-item h4, .role-guide-item h4, .ticket-decision h4, .limit-item h4 { color: rgb(15 23 42); font-size: .9rem; margin: 0; }
.flow-copy p, .step-guide-item p, .role-guide-item p, .ticket-decision p, .limit-item p { color: rgb(71 85 105); font-size: .78rem; line-height: 1.55; margin: .4rem 0 0; }
.flow-role { color: rgb(14 116 144) !important; font-size: .68rem !important; font-weight: 800; letter-spacing: .04em; margin: 0 !important; text-transform: uppercase; }
.flow-connector { align-items: center; color: rgb(14 165 233); display: flex; height: 2.25rem; justify-content: end; pointer-events: none; position: absolute; right: -.55rem; top: 0; z-index: 2; }
.guide-note { align-items: flex-start; border: 1px solid; display: flex; font-size: .8rem; gap: .75rem; margin-top: 1.6rem; padding: 1rem 1.05rem; }
.guide-note p { line-height: 1.6; margin: 0; }
.guide-note-sky { background: rgb(240 249 255); border-color: rgb(186 230 253); color: rgb(12 74 110); }
.guide-note-amber { background: rgb(255 251 235); border-color: rgb(253 230 138); color: rgb(120 53 15); }
.steps-grid { display: grid; gap: 1rem; grid-template-columns: repeat(7, minmax(160px, 1fr)); overflow-x: auto; padding: .2rem 0 .45rem; }
.step-guide-item { border: 1px solid rgb(226 232 240); display: flex; flex-direction: column; min-height: 235px; padding: 1rem; }
.step-guide-top { align-items: center; display: flex; gap: .5rem; justify-content: space-between; margin-bottom: 1rem; }
.step-guide-number { align-items: center; background: rgb(19 46 102); border-radius: 50%; color: white; display: inline-flex; font-size: .72rem; font-weight: 800; height: 1.65rem; justify-content: center; width: 1.65rem; }
.step-guide-item h4 { min-height: 2.5rem; }
.step-guide-footer { align-items: center; color: rgb(100 116 139); display: flex; font-size: .7rem; gap: .35rem; margin-top: auto; padding-top: 1rem; }
.roles-grid, .ticket-map, .limits-grid, .resolution-control-grid { display: grid; gap: 1.25rem; }
.roles-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.role-guide-item { border-left: 2px solid rgb(186 230 253); display: flex; gap: 1rem; min-height: 8rem; padding: .35rem 0 .35rem .85rem; }
.role-guide-item ul { list-style: none; margin: .9rem 0 0; padding: 0; }
.role-guide-item li { align-items: center; color: rgb(51 65 85); display: flex; font-size: .75rem; gap: .45rem; margin-top: .5rem; }
.role-guide-item li i { color: rgb(5 150 105); font-size: .68rem; }
.ticket-map { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.ticket-decision { border-left: 2px solid rgb(203 213 225); display: flex; gap: .8rem; min-height: 6.3rem; padding: .35rem 0 .35rem .85rem; }
.limits-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.resolution-control-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.control-guide-item { align-items: flex-start; border-left: 2px solid rgb(186 230 253); display: flex; gap: .8rem; min-height: 6rem; padding: .35rem 0 .35rem .85rem; }
.control-guide-item h4 { color: rgb(15 23 42); font-size: .85rem; margin: 0; }
.control-guide-item p { color: rgb(71 85 105); font-size: .76rem; line-height: 1.55; margin: .4rem 0 0; }
.limit-item { align-items: flex-start; display: flex; gap: .75rem; min-height: 4.8rem; }
.limit-item > i { color: rgb(14 116 144); font-size: 1.1rem; margin-top: .15rem; }
:global(html.dark .guide-heading), :global(html.dark .guide-section) { border-color: rgb(71 85 105); }
:global(html.dark .guide-page .eyebrow) { color: rgb(103 232 249) !important; }
:global(html.dark .guide-anchor-nav a) { border-color: rgb(100 116 139); color: rgb(226 232 240) !important; }
:global(html.dark .guide-anchor-nav a:hover) { border-color: rgb(56 189 248); color: rgb(224 242 254) !important; }
:global(html.dark .flow-copy h4), :global(html.dark .step-guide-item h4), :global(html.dark .role-guide-item h4), :global(html.dark .ticket-decision h4), :global(html.dark .limit-item h4) { color: rgb(248 250 252) !important; }
:global(html.dark .guide-intro), :global(html.dark .start-item p) { color: rgb(226 232 240) !important; }
:global(html.dark .start-item h4) { color: rgb(248 250 252) !important; }
:global(html.dark .flow-copy p), :global(html.dark .step-guide-item p), :global(html.dark .role-guide-item p), :global(html.dark .ticket-decision p), :global(html.dark .limit-item p), :global(html.dark .role-guide-item li) { color: rgb(226 232 240) !important; }
:global(html.dark .flow-role) { color: rgb(103 232 249) !important; }
:global(html.dark .step-guide-item) { border-color: rgb(71 85 105); }
:global(html.dark .step-guide-footer) { color: rgb(203 213 225) !important; }
:global(html.dark .ticket-decision) { border-color: rgb(100 116 139); }
:global(html.dark .limit-item > i) { color: rgb(103 232 249) !important; }
:global(html.dark .control-guide-item) { border-color: rgb(100 116 139); }
:global(html.dark .control-guide-item h4) { color: rgb(248 250 252) !important; }
:global(html.dark .control-guide-item p) { color: rgb(226 232 240) !important; }
:global(.dark) .guide-note-sky { background: rgb(8 47 73 / .5); border-color: rgb(14 116 144 / .5); color: rgb(186 230 253); }
:global(.dark) .guide-note-amber { background: rgb(69 26 3 / .45); border-color: rgb(180 83 9 / .5); color: rgb(253 230 138); }
@media (max-width: 1100px) { .resolution-flow { grid-template-columns: repeat(2, minmax(0, 1fr)); row-gap: 1.8rem; } .flow-connector { display: none; } .ticket-map, .limits-grid, .resolution-control-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .steps-grid { grid-template-columns: repeat(7, 175px); } }
@media (max-width: 680px) { .guide-heading, .guide-section-heading { align-items: flex-start; flex-direction: column; } .resolution-flow, .roles-grid, .ticket-map, .limits-grid, .resolution-control-grid, .start-grid { grid-template-columns: 1fr; } .flow-stage { border-left: 2px solid rgb(125 211 252); padding-left: .85rem; } .flow-stage:last-child { border-left-color: transparent; } .flow-icon { margin-left: -2rem; } .flow-copy { margin-top: .4rem; } }
</style>
