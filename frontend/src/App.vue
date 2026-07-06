<template>
  <PToast position="top-right" />
  <PConfirmDialog />

  <!-- Sin sidebar: Login o Dictaminante (rutas públicas) -->
  <template v-if="!auth.isLoggedIn">
    <router-view />
  </template>

  <!-- Con sidebar: Panel principal -->
  <template v-else>
    <div class="flex h-screen overflow-hidden bg-slate-950">
      <AppSidebar />
      <main class="flex-1 overflow-y-auto">
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
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth.js'
import AppSidebar from './components/AppSidebar.vue'

const auth = useAuthStore()

// Aplicar tema guardado al cargar la app
onMounted(() => {
  const tema = localStorage.getItem('epg_tema')
  // Por defecto: modo oscuro (dark) a menos que se haya guardado 'light'
  if (tema !== 'light') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
})
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
</style>
