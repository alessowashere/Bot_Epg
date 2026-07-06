import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from './stores/auth.js'

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
const DictaminanteView   = () => import('./views/DictaminanteView.vue')

const routes = [
  { path: '/login',  name: 'login',  component: LoginView, meta: { publico: true } },
  { path: '/',       name: 'dashboard',  component: DashboardView,     meta: { requiereAuth: true } },
  { path: '/bandeja',  name: 'bandeja',  component: BandejaView,       meta: { requiereAuth: true } },
  { path: '/bandeja/:uuid', name: 'ticket-detalle', component: TicketDetalleView, meta: { requiereAuth: true } },
  { path: '/expedientes',     name: 'expedientes',    component: ExpedientesView,   meta: { requiereAuth: true } },
  { path: '/expedientes/:uuid', name: 'expediente-detalle', component: ExpedienteDetalle, meta: { requiereAuth: true } },
  { path: '/directora', name: 'directora', component: DirectoraView, meta: { requiereAuth: true, soloDirectora: true } },
  { path: '/dictaminante/:uuid_asignacion', name: 'dictaminante', component: DictaminanteView, meta: { publico: true } },
  { path: '/docentes',  name: 'docentes',  component: DocentesView,  meta: { requiereAuth: true } },
  { path: '/usuarios',  name: 'usuarios',  component: UsuariosView,  meta: { requiereAuth: true, soloAdmin: true } },
  // Fallback
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.requiereAuth && !auth.isLoggedIn) {
    return { name: 'login' }
  }
  if (to.meta.publico && auth.isLoggedIn) {
    return { name: 'dashboard' }
  }
  if (to.meta.soloAdmin && !auth.isAdmin) {
    return { name: 'dashboard' }
  }
  if (to.meta.soloDirectora && !(auth.isDirectora || auth.isAdmin)) {
    return { name: 'dashboard' }
  }
})

export default router
