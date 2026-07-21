import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from './stores/auth.js'

// Conserva los enlaces compartidos antes de migrar desde rutas con #.
if (window.location.hash.startsWith('#/')) {
  window.history.replaceState(null, '', window.location.hash.slice(1))
}

// Lazy imports para mejor rendimiento
const LoginView          = () => import('./views/LoginView.vue')
const DashboardView      = () => import('./views/DashboardView.vue')
const BandejaView        = () => import('./views/BandejaView.vue')
const TicketDetalleView  = () => import('./views/TicketDetalleView.vue')
const ExpedientesView    = () => import('./views/ExpedientesView.vue')
const ExpedienteDetalle  = () => import('./views/ExpedienteDetalleView.vue')
const DocentesView       = () => import('./views/DocentesView.vue')
const UsuariosView       = () => import('./views/UsuariosView.vue')
const DirectoraView      = () => import('./views/DirectoraView.vue')
const SecretariaView     = () => import('./views/SecretariaView.vue')
const ConsultaDisponibilidadView = () => import('./views/ConsultaDisponibilidadView.vue')
const DictaminanteView   = () => import('./views/DictaminanteView.vue')
const ResolucionesView   = () => import('./views/ResolucionesView.vue')
const TicketsPendientesView = () => import('./views/TicketsPendientesView.vue')
const CambiarPasswordView = () => import('./views/CambiarPasswordView.vue')
const ReglasResolucionesView = () => import('./views/ReglasResolucionesView.vue')
const GuiaOperacionView = () => import('./views/GuiaOperacionView.vue')
const ConciliacionIdentidadesView = () => import('./views/ConciliacionIdentidadesView.vue')
const EstudiantesView = () => import('./views/EstudiantesView.vue')
const ActualizacionDocenteView = () => import('./views/ActualizacionDocenteView.vue')

const routes = [
  { path: '/a0', name: 'login', component: LoginView, meta: { publico: true } },
  { path: '/a1', name: 'cambiar-password', component: CambiarPasswordView, meta: { requiereAuth: true, cambioPassword: true } },
  { path: '/i0', name: 'dashboard', component: DashboardView, meta: { requiereAuth: true } },
  { path: '/i1', name: 'bandeja', component: BandejaView, meta: { requiereAuth: true } },
  { path: '/i1/:uuid', name: 'ticket-detalle', component: TicketDetalleView, meta: { requiereAuth: true } },
  { path: '/i2', name: 'tickets-pendientes', component: TicketsPendientesView, meta: { requiereAuth: true } },
  { path: '/i3', name: 'expedientes', component: ExpedientesView, meta: { requiereAuth: true } },
  { path: '/i3/:uuid', name: 'expediente-detalle', component: ExpedienteDetalle, meta: { requiereAuth: true } },
  { path: '/i4', name: 'resoluciones', component: ResolucionesView, meta: { requiereAuth: true } },
  { path: '/i5', name: 'directora', component: DirectoraView, meta: { requiereAuth: true, soloDirectora: true } },
  { path: '/i6', name: 'secretaria', component: SecretariaView, meta: { requiereAuth: true, soloSecretaria: true } },
  { path: '/v/:token', name: 'consulta-resolucion', component: ConsultaDisponibilidadView, meta: { publico: true, admiteSesion: true } },
  { path: '/d/:token', name: 'actualizacion-docente', component: ActualizacionDocenteView, meta: { publico: true, admiteSesion: true } },
  { path: '/q/:uuid_asignacion', name: 'dictaminante', component: DictaminanteView, meta: { publico: true } },
  { path: '/i7', name: 'docentes', component: DocentesView, meta: { requiereAuth: true, soloCoordinacion: true } },
  { path: '/i8', name: 'usuarios', component: UsuariosView, meta: { requiereAuth: true, soloAdmin: true } },
  { path: '/i9', name: 'reglas-resolucion', component: ReglasResolucionesView, meta: { requiereAuth: true, reglasResolucion: true } },
  { path: '/i10', name: 'guia-operacion', component: GuiaOperacionView, meta: { requiereAuth: true } },
  { path: '/i11', name: 'conciliacion-identidades', component: ConciliacionIdentidadesView, meta: { requiereAuth: true, soloAdmin: true } },
  { path: '/i12', name: 'estudiantes', component: EstudiantesView, meta: { requiereAuth: true } },
  { path: '/', redirect: { name: 'dashboard' } },
  // Compatibilidad: las rutas semánticas se redirigen a su identificador interno.
  { path: '/login', redirect: { name: 'login' } },
  { path: '/cambiar-password', redirect: { name: 'cambiar-password' } },
  { path: '/bandeja', redirect: { name: 'bandeja' } },
  { path: '/bandeja/:uuid', redirect: to => ({ name: 'ticket-detalle', params: to.params }) },
  { path: '/tickets-pendientes', redirect: { name: 'tickets-pendientes' } },
  { path: '/expedientes', redirect: { name: 'expedientes' } },
  { path: '/expedientes/:uuid', redirect: to => ({ name: 'expediente-detalle', params: to.params }) },
  { path: '/resoluciones', redirect: { name: 'resoluciones' } },
  { path: '/directora', redirect: { name: 'directora' } },
  { path: '/secretaria', redirect: { name: 'secretaria' } },
  { path: '/consulta-resolucion/:token', redirect: to => ({ name: 'consulta-resolucion', params: to.params }) },
  { path: '/dictaminante/:uuid_asignacion', redirect: to => ({ name: 'dictaminante', params: to.params }) },
  { path: '/docentes', redirect: { name: 'docentes' } },
  { path: '/usuarios', redirect: { name: 'usuarios' } },
  { path: '/reglas-resolucion', redirect: { name: 'reglas-resolucion' } },
  { path: '/guia', redirect: { name: 'guia-operacion' } },
  { path: '/estudiantes', redirect: { name: 'estudiantes' } },
  { path: '/:pathMatch(.*)*', redirect: { name: 'dashboard' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.requiereAuth && !auth.isLoggedIn) {
    return { name: 'login' }
  }
  if (auth.isLoggedIn && auth.requiereCambioPassword && !auth.enVistaRol && !to.meta.cambioPassword && !to.meta.publico) {
    return { name: 'cambiar-password' }
  }
  if (to.name === 'login' && auth.isLoggedIn) {
    return { name: auth.requiereCambioPassword ? 'cambiar-password' : 'dashboard' }
  }
  if (auth.isCoordinacion && to.name === 'dashboard') {
    return { name: 'docentes' }
  }
  if (to.meta.publico && !to.meta.admiteSesion && auth.isLoggedIn) {
    return { name: 'dashboard' }
  }
  if (to.meta.soloAdmin && !auth.isAdmin) {
    return { name: 'dashboard' }
  }
  if (to.meta.soloDirectora && !(auth.isDirectora || auth.isAdmin)) {
    return { name: 'dashboard' }
  }
  if (to.meta.soloSecretaria && !(auth.isSecretaria || auth.isAdmin)) {
    return { name: 'dashboard' }
  }
  if (to.meta.reglasResolucion && !(auth.isSecretaria || auth.isAdmin)) {
    return { name: 'dashboard' }
  }
  if (to.meta.soloCoordinacion && !(auth.isCoordinacion || auth.isAdmin || auth.isSecretaria)) {
    return { name: 'dashboard' }
  }
})

export default router
