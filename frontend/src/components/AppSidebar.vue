<template>
  <aside
    :class="[
      'uac-sidebar fixed inset-y-0 left-0 z-50 flex flex-col border-r border-[#25477d] bg-[#102f63] text-white transition-[transform,width] duration-200 lg:static lg:z-auto lg:translate-x-0',
      compact ? 'w-20 lg:w-20' : 'w-64',
      open ? 'translate-x-0' : '-translate-x-full',
    ]"
  >
    <div :class="['flex min-h-20 items-center gap-3 border-b border-white/15 py-4', compact ? 'justify-center px-2' : 'px-4']">
      <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-md bg-white/10">
        <img
          src="/brand/uac-logo-white.png"
          alt="UAC"
          class="h-8 w-8 object-contain"
        />
      </div>
      <div v-if="!compact" class="min-w-0 flex-1">
        <p class="text-[10px] font-semibold uppercase tracking-wide text-cyan-200">Universidad Andina del Cusco</p>
        <h1 class="truncate text-[15px] font-bold">Escuela de Posgrado</h1>
        <p class="text-xs text-blue-100/70">Seguimiento de tesis</p>
      </div>
      <button
        type="button"
        class="icon-btn border-white/15 text-white hover:bg-white/10 lg:hidden"
        aria-label="Cerrar navegacion"
        title="Cerrar navegacion"
        @click="emit('close')"
      >
        <i class="pi pi-times"></i>
      </button>
    </div>

    <div :class="['border-b border-white/15 py-3', compact ? 'px-2' : 'px-4']">
      <div :class="['flex items-center rounded-md bg-white/10 py-2.5', compact ? 'justify-center px-2' : 'gap-3 px-3']" :title="`${auth.nombre} · ${auth.rol}`">
        <div class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-cyan-400 text-xs font-bold text-[#132e66]">
          {{ iniciales }}
        </div>
        <div v-if="!compact" class="min-w-0">
          <p class="truncate text-xs font-semibold">{{ auth.nombre }}</p>
          <p class="text-[11px] text-cyan-200">{{ auth.rol }}</p>
        </div>
      </div>
    </div>

    <div v-if="!compact" class="relative border-b border-white/15 px-4 py-3">
      <div class="relative">
        <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-xs text-blue-100/60"></i>
        <label for="busqueda-global" class="sr-only">Buscar en el sistema</label>
        <input
          id="busqueda-global"
          v-model="busquedaGlobal"
          class="w-full rounded-md border border-white/20 bg-white/10 py-2 pl-9 pr-9 text-xs text-white placeholder:text-blue-100/50 focus:border-cyan-300 focus:outline-none focus:ring-1 focus:ring-cyan-300"
          placeholder="Buscar ticket, persona, tesis..."
          @keyup.enter="buscarGlobal"
          @keydown.esc="limpiarBusqueda"
        />
        <button
          type="button"
          class="absolute right-1.5 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded text-blue-100 hover:bg-white/10 hover:text-white"
          aria-label="Buscar"
          title="Buscar"
          @click="buscarGlobal"
        >
          <i :class="cargandoBusqueda ? 'pi pi-spin pi-spinner' : 'pi pi-arrow-right'" class="text-xs"></i>
        </button>
      </div>

      <div v-if="resultadosGlobales.length || busquedaSinResultados" class="absolute left-4 right-4 top-[58px] z-50 max-h-72 overflow-y-auto rounded-lg border border-slate-200 bg-white py-1 shadow-xl dark:border-slate-700 dark:bg-slate-900">
        <button
          v-for="resultado in resultadosGlobales"
          :key="`${resultado.tipo}-${resultado.id}`"
          type="button"
          class="flex w-full items-start gap-2 border-b border-slate-100 px-3 py-2.5 text-left last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800"
          @click="abrirResultado(resultado)"
        >
          <i :class="iconoResultado(resultado.tipo)" class="pi mt-0.5 text-sm text-[#0973dc]"></i>
          <span class="min-w-0">
            <span class="block truncate text-xs font-semibold text-slate-900 dark:text-white">{{ resultado.titulo }}</span>
            <span class="block truncate text-[11px] text-slate-500">{{ resultado.subtitulo || resultado.detalle }}</span>
          </span>
        </button>
        <p v-if="busquedaSinResultados" class="px-3 py-4 text-center text-xs text-slate-500">Sin coincidencias</p>
      </div>
    </div>

    <nav :class="['flex-1 overflow-y-auto py-4', compact ? 'px-2' : 'px-3']">
      <p v-if="!compact" class="mb-2 px-3 text-[10px] font-semibold uppercase text-blue-100/55">Operacion</p>
      <router-link
        v-for="item in menuItems"
        :key="item.to"
        :to="item.to"
        v-slot="{ isActive, navigate }"
        custom
      >
        <button
          type="button"
          :title="compact ? item.label : undefined"
          :class="[
            'mb-1 flex w-full items-center rounded-md py-2.5 text-left text-sm font-medium transition-colors',
            compact ? 'justify-center px-2' : 'gap-3 px-3',
            isActive ? 'bg-cyan-300 text-[#132e66]' : 'text-blue-50 hover:bg-white/10 hover:text-white',
          ]"
          @click="navegar(navigate)"
        >
          <i :class="item.icon" class="pi w-5 text-center text-base"></i>
          <span v-if="!compact" class="flex-1">{{ item.label }}</span>
        </button>
      </router-link>

      <template v-if="auth.isAdmin">
        <p v-if="!compact" class="mb-2 mt-5 px-3 text-[10px] font-semibold uppercase text-blue-100/55">Administracion</p>
        <router-link to="/usuarios" v-slot="{ isActive, navigate }" custom>
          <button
            type="button"
            :title="compact ? 'Usuarios' : undefined"
            :class="[
              'mb-1 flex w-full items-center rounded-md py-2.5 text-left text-sm font-medium transition-colors',
              compact ? 'justify-center px-2' : 'gap-3 px-3',
              isActive ? 'bg-cyan-300 text-[#132e66]' : 'text-blue-50 hover:bg-white/10 hover:text-white',
            ]"
            @click="navegar(navigate)"
          >
            <i class="pi pi-users w-5 text-center text-base"></i>
            <span v-if="!compact">Usuarios</span>
          </button>
        </router-link>
        <router-link to="/i11" v-slot="{ isActive, navigate }" custom>
          <button
            type="button"
            title="Conciliación histórica"
            :class="[
              'mb-1 flex w-full items-center rounded-md py-2.5 text-left text-sm font-medium transition-colors',
              compact ? 'justify-center px-2' : 'gap-3 px-3',
              isActive ? 'bg-cyan-300 text-[#132e66]' : 'text-blue-50 hover:bg-white/10 hover:text-white',
            ]"
            @click="navegar(navigate)"
          >
            <i class="pi pi-sitemap w-5 text-center text-base"></i>
            <span v-if="!compact">Conciliar históricos</span>
          </button>
        </router-link>
      </template>
    </nav>

    <div :class="['border-t border-white/15', compact ? 'p-2' : 'p-3']">
      <button type="button" class="sidebar-action" :title="isDark ? 'Usar modo claro' : 'Usar modo oscuro'" @click="toggleTema">
        <i :class="isDark ? 'pi-sun' : 'pi-moon'" class="pi w-5 text-center"></i>
        <span v-if="!compact">{{ isDark ? 'Modo claro' : 'Modo oscuro' }}</span>
      </button>
      <button v-if="!auth.enVistaRol" type="button" class="sidebar-action" title="Cerrar las sesiones abiertas en otros dispositivos" @click="cerrarOtrasSesiones">
        <i class="pi pi-desktop w-5 text-center"></i>
        <span v-if="!compact">Cerrar otras sesiones</span>
      </button>
      <button type="button" class="sidebar-action text-red-100 hover:bg-red-500/20" @click="cerrarSesion">
        <i class="pi pi-sign-out w-5 text-center"></i>
        <span v-if="!compact">Cerrar sesion</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import api from '../api.js'

const props = defineProps({ open: { type: Boolean, default: false }, compact: { type: Boolean, default: false } })
const emit = defineEmits(['close'])
const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const busquedaGlobal = ref('')
const resultadosGlobales = ref([])
const cargandoBusqueda = ref(false)
const busquedaSinResultados = ref(false)
const isDark = ref(localStorage.getItem('epg_tema') === 'dark')

const iniciales = computed(() => {
  if (!auth.nombre) return '?'
  return auth.nombre.split(' ').filter(Boolean).slice(0, 2).map(nombre => nombre[0]).join('').toUpperCase()
})

const menuItems = computed(() => {
  const panel = { to: '/', label: 'Panel operativo', icon: 'pi-chart-bar' }
  const guia = { to: '/i10', label: 'Guía de operación', icon: 'pi-compass' }
  if (auth.isSecretaria) return [
    panel,
    { to: '/secretaria', label: 'Mesa de Secretaría', icon: 'pi-file-edit' },
    { to: '/resoluciones', label: 'Control de resoluciones', icon: 'pi-book' },
    { to: '/docentes', label: 'Docentes', icon: 'pi-id-card' },
    { to: '/expedientes', label: 'Expedientes', icon: 'pi-folder-open' },
    { to: '/estudiantes', label: 'Estudiantes', icon: 'pi-users' },
    { to: '/reglas-resolucion', label: 'Reglas por paso', icon: 'pi-sliders-h' },
    guia,
  ]
  if (auth.isDirectora) return [
    panel,
    { to: '/directora', label: 'Firma y aprobación', icon: 'pi-shield' },
    { to: '/expedientes', label: 'Expedientes', icon: 'pi-folder-open' },
    { to: '/estudiantes', label: 'Estudiantes', icon: 'pi-users' },
    { to: '/resoluciones', label: 'Resoluciones', icon: 'pi-file-check' },
    guia,
  ]
  if (!auth.isAdmin) return [
    panel,
    { to: '/tickets-pendientes', label: 'Mesa de tickets', icon: 'pi-list-check' },
    { to: '/bandeja', label: 'Archivo de tickets', icon: 'pi-inbox' },
    { to: '/expedientes', label: 'Expedientes', icon: 'pi-folder-open' },
    { to: '/estudiantes', label: 'Estudiantes', icon: 'pi-users' },
    guia,
  ]
  return [
    panel,
    { to: '/tickets-pendientes', label: 'Mesa de tickets', icon: 'pi-list-check' },
    { to: '/bandeja', label: 'Archivo de tickets', icon: 'pi-inbox' },
    { to: '/expedientes', label: 'Expedientes', icon: 'pi-folder-open' },
    { to: '/estudiantes', label: 'Estudiantes', icon: 'pi-users' },
    { to: '/secretaria', label: 'Mesa de Secretaría', icon: 'pi-file-edit' },
    { to: '/directora', label: 'Firma y aprobación', icon: 'pi-shield' },
    { to: '/resoluciones', label: 'Control de resoluciones', icon: 'pi-book' },
    { to: '/docentes', label: 'Docentes', icon: 'pi-id-card' },
    { to: '/reglas-resolucion', label: 'Reglas por paso', icon: 'pi-sliders-h' },
    guia,
  ]
})

function toggleTema() {
  isDark.value = !isDark.value
  localStorage.setItem('epg_tema', isDark.value ? 'dark' : 'light')
  document.documentElement.classList.toggle('dark', isDark.value)
}

function limpiarBusqueda() {
  resultadosGlobales.value = []
  busquedaSinResultados.value = false
}

async function buscarGlobal() {
  const q = busquedaGlobal.value.trim()
  if (q.length < 2) {
    limpiarBusqueda()
    return
  }
  cargandoBusqueda.value = true
  busquedaSinResultados.value = false
  try {
    const res = await api.get('/buscar', { params: { q, limite: 5 } })
    resultadosGlobales.value = [
      ...(res.data.tickets || []),
      ...(res.data.expedientes || []),
      ...(res.data.resoluciones || []),
      ...(res.data.docentes || []),
      ...(res.data.adjuntos || []),
    ].slice(0, 15)
    busquedaSinResultados.value = resultadosGlobales.value.length === 0
  } catch (error) {
    resultadosGlobales.value = []
    busquedaSinResultados.value = true
  } finally {
    cargandoBusqueda.value = false
  }
}

function iconoResultado(tipo) {
  return {
    ticket: 'pi-ticket',
    expediente: 'pi-folder',
    resolucion: 'pi-file',
    docente: 'pi-user',
    adjunto: 'pi-paperclip',
  }[tipo] || 'pi-search'
}

function abrirResultado(resultado) {
  limpiarBusqueda()
  busquedaGlobal.value = ''
  router.push(resultado.ruta || '/')
}

function navegar(navigate) {
  navigate()
  emit('close')
}

async function cerrarOtrasSesiones() {
  if (!confirm('Se cerrarán las otras sesiones abiertas de esta cuenta.')) return
  try {
    const respuesta = await api.post('/auth/cerrar-otras-sesiones')
    alert(`${respuesta.data.sesiones_cerradas || 0} sesiones cerradas.`)
  } catch (error) {
    alert(error.response?.data?.detail || 'No se pudieron cerrar las otras sesiones.')
  }
}

async function cerrarSesion() {
  try {
    await api.post('/auth/logout')
  } catch {
    // Si venció o ya fue revocada, se limpia de todos modos el acceso local.
  }
  auth.logout()
  router.push('/login')
}

watch(() => route.fullPath, () => emit('close'))
</script>
