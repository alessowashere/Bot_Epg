<template>
  <aside class="w-64 flex-shrink-0 bg-slate-900 border-r border-slate-700/50 flex flex-col h-full">
    <!-- Logo / Header -->
    <div class="p-5 border-b border-slate-700/50">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/30 flex-shrink-0">
          <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.966 8.966 0 00-6 2.292m0-14.25v14.25" />
          </svg>
        </div>
        <div>
          <h1 class="text-sm font-bold text-white leading-tight">EPG-UAC</h1>
          <p class="text-xs text-slate-500">Sistema de Posgrado</p>
        </div>
      </div>
    </div>

    <!-- Usuario activo -->
    <div class="px-4 py-3 border-b border-slate-700/50">
      <div class="flex items-center gap-2.5 p-2.5 rounded-lg bg-slate-800/60">
        <div class="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
          {{ iniciales }}
        </div>
        <div class="min-w-0">
          <p class="text-xs font-semibold text-white truncate">{{ auth.nombre }}</p>
          <span class="text-[10px] text-indigo-400 font-medium">{{ auth.rol }}</span>
        </div>
      </div>
    </div>

    <!-- Navegación -->
    <nav class="flex-1 overflow-y-auto py-4 px-3 space-y-1">
      <p class="px-2 text-[10px] text-slate-500 uppercase tracking-widest font-semibold mb-2">Principal</p>

      <router-link v-for="item in menuItems" :key="item.to" :to="item.to" v-slot="{ isActive, navigate }" custom>
        <div
          @click="navigate"
          :class="['nav-item', isActive ? 'active' : '']"
        >
          <span v-html="item.icon" class="w-5 h-5 flex-shrink-0 opacity-80"></span>
          <span>{{ item.label }}</span>
          <span v-if="item.badge" class="ml-auto bg-indigo-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
            {{ item.badge }}
          </span>
        </div>
      </router-link>

      <template v-if="auth.isAdmin">
        <p class="px-2 text-[10px] text-slate-500 uppercase tracking-widest font-semibold mt-4 mb-2">Administración</p>
        <router-link to="/usuarios" v-slot="{ isActive, navigate }" custom>
          <div @click="navigate" :class="['nav-item', isActive ? 'active' : '']">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
            </svg>
            <span>Usuarios</span>
          </div>
        </router-link>
      </template>
    </nav>

    <!-- Footer / Cerrar sesión -->
    <div class="p-3 border-t border-slate-700/50">
      <button @click="cerrarSesion" class="nav-item w-full text-red-400 hover:text-red-300 hover:bg-red-500/10">
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
        </svg>
        <span>Cerrar sesión</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()
const router = useRouter()

const iniciales = computed(() => {
  if (!auth.nombre) return '?'
  return auth.nombre.split(' ').slice(0, 2).map(n => n[0]).join('').toUpperCase()
})

const menuItems = [
  {
    to: '/',
    label: 'Dashboard',
    icon: `<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" /></svg>`
  },
  {
    to: '/bandeja',
    label: 'Bandeja de Tickets',
    icon: `<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 012.012 1.244l.256.512a2.25 2.25 0 002.013 1.244h3.218a2.25 2.25 0 002.013-1.244l.256-.512a2.25 2.25 0 012.013-1.244h3.859m-19.5.338V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 00-2.15-1.588H6.911a2.25 2.25 0 00-2.15 1.588L2.35 13.177a2.25 2.25 0 00-.1.661z" /></svg>`
  },
  {
    to: '/expedientes',
    label: 'Expedientes',
    icon: `<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932H19.05a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776" /></svg>`
  },
  {
    to: '/docentes',
    label: 'Docentes',
    icon: `<svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" /></svg>`
  },
]

function cerrarSesion() {
  auth.logout()
  router.push('/login')
}
</script>
