<template>
  <PToast position="bottom-right" group="epg-global" />
  <PConfirmDialog />
  <div v-if="auth.enVistaRol" class="fixed inset-x-0 top-0 z-[100] flex min-h-11 items-center justify-between gap-3 bg-amber-300 px-4 text-sm font-semibold text-amber-950 shadow-sm">
    <span class="min-w-0 truncate"><i class="pi pi-eye mr-2"></i>Vista de {{ auth.nombre }} ({{ auth.rol }}): solo lectura</span>
    <button type="button" class="shrink-0 rounded border border-amber-800/40 px-2.5 py-1 text-xs hover:bg-amber-200" @click="volverAdministrador">Volver a Administrador</button>
  </div>

  <!-- Sin sidebar: Login o Dictaminante (rutas públicas) -->
  <template v-if="!auth.isLoggedIn || route.meta.publico || route.meta.cambioPassword">
    <router-view />
  </template>

  <!-- Con sidebar: Panel principal -->
  <template v-else>
    <div :class="['fixed inset-0 flex overflow-hidden bg-slate-50 dark:bg-slate-950', auth.enVistaRol ? 'pt-11' : '']">
      <div
        v-if="sidebarAbierto"
        class="fixed inset-0 z-40 bg-slate-950/50 lg:hidden"
        @click="sidebarAbierto = false"
      ></div>
      <AppSidebar :open="sidebarAbierto" :compact="sidebarCompacta" @close="sidebarAbierto = false" />
      <main class="min-w-0 flex-1 overflow-y-auto">
        <div class="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-slate-200 bg-white/95 px-4 backdrop-blur lg:hidden dark:border-slate-800 dark:bg-slate-950/95">
          <button
            class="icon-btn"
            type="button"
            aria-label="Abrir navegacion"
            title="Abrir navegacion"
            @click="sidebarAbierto = true"
          >
            <i class="pi pi-bars"></i>
          </button>
          <span class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md bg-[#12356b] p-1.5">
            <img src="/brand/uac-logo-white.png" alt="UAC" class="h-full w-full object-contain" />
          </span>
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold text-slate-900 dark:text-white">Escuela de Posgrado UAC</p>
            <p class="text-[11px] text-slate-500">Seguimiento de tesis</p>
          </div>
        </div>
        <header class="app-topbar hidden lg:flex" aria-label="Contexto de la aplicacion">
          <div class="flex min-w-0 items-center gap-2">
            <button class="icon-btn" type="button" :title="sidebarCompacta ? 'Mostrar navegación completa' : 'Usar navegación compacta'" :aria-label="sidebarCompacta ? 'Mostrar navegación completa' : 'Usar navegación compacta'" @click="alternarSidebar">
              <i :class="sidebarCompacta ? 'pi pi-angle-double-right' : 'pi pi-angle-double-left'"></i>
            </button>
            <div class="min-w-0">
            <p class="text-[10px] font-bold uppercase tracking-[0.12em] text-sky-700 dark:text-cyan-300">Sistema interno · EPG UAC</p>
            <p class="mt-0.5 truncate text-sm font-semibold text-slate-900 dark:text-white">{{ tituloRuta }}</p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <div class="hidden items-end text-right sm:flex sm:flex-col">
              <span class="text-[10px] font-medium text-slate-500 dark:text-slate-400">{{ fechaTopbar }}</span>
              <span class="font-mono text-[11px] font-bold text-sky-700 dark:text-cyan-300">{{ horaTopbar }}</span>
            </div>
            <span class="flex h-8 w-8 items-center justify-center rounded-full bg-[#12356b] text-xs font-bold text-white" :title="auth.nombre" aria-label="Sesión activa">{{ iniciales }}</span>
          </div>
        </header>
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </template>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth.js'
import api from './api.js'
import AppSidebar from './components/AppSidebar.vue'
import { useToast } from 'primevue/usetoast'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const sidebarAbierto = ref(false)
const sidebarCompacta = ref(localStorage.getItem('epg_sidebar_compacta') === 'true')
const ahoraTopbar = ref(new Date())
let relojTopbar
const toast = useToast()
const titulosRuta = {
  dashboard: 'Panel de seguimiento',
  bandeja: 'Bandeja de tickets',
  'ticket-detalle': 'Detalle de ticket',
  'tickets-pendientes': 'Revision humana',
  expedientes: 'Expedientes oficiales',
  'expediente-detalle': 'Detalle de expediente',
  resoluciones: 'Resoluciones',
  docentes: 'Docentes',
  directora: 'Mesa de Directora',
  secretaria: 'Secretaría Académica',
  usuarios: 'Usuarios y accesos',
  'reglas-resolucion': 'Reglas institucionales',
  'guia-operacion': 'Guía de operación',
}
const tituloRuta = computed(() => titulosRuta[route.name] || 'Seguimiento de tesis')
const iniciales = computed(() => auth.nombre?.split(' ').filter(Boolean).slice(0, 2).map(item => item[0]).join('').toUpperCase() || '?')
const fechaTopbar = computed(() => ahoraTopbar.value.toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric' }))
const horaTopbar = computed(() => ahoraTopbar.value.toLocaleTimeString('es-PE', { hour: '2-digit', minute: '2-digit', second: '2-digit' }))

function alternarSidebar() {
  sidebarCompacta.value = !sidebarCompacta.value
  localStorage.setItem('epg_sidebar_compacta', String(sidebarCompacta.value))
}

async function volverAdministrador() {
  try {
    await api.post('/auth/logout')
  } catch {
    // La restauración local no debe perderse si la sesión temporal ya venció.
  }
  auth.salirVistaRol()
  router.replace('/')
}

// Aplicar tema guardado al cargar la app
onMounted(() => {
  const tema = localStorage.getItem('epg_tema')
  // La herramienta administrativa inicia en modo claro salvo preferencia guardada.
  if (tema === 'dark') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
  relojTopbar = window.setInterval(() => { ahoraTopbar.value = new Date() }, 1000)
})

function mostrarErrorGlobal(evento) {
  toast.add({
    group: 'epg-global',
    severity: 'error',
    summary: `Error ${evento.detail?.status || ''}`.trim(),
    detail: evento.detail?.mensaje || 'No se pudo completar la operación.',
    life: 5000,
  })
}

onMounted(() => window.addEventListener('epg:api-error', mostrarErrorGlobal))
onBeforeUnmount(() => window.removeEventListener('epg:api-error', mostrarErrorGlobal))
onBeforeUnmount(() => window.clearInterval(relojTopbar))
</script>

<style>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.p-toast {
  z-index: 200 !important;
}
.p-toast-message {
  box-shadow: 0 16px 36px rgb(15 23 42 / .24);
}
</style>
