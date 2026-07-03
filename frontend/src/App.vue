<template>
  <div class="dark">
    <PToast position="top-right" />
    <PConfirmDialog />

    <!-- Sin sidebar: Login -->
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
  </div>
</template>

<script setup>
import { useAuthStore } from './stores/auth.js'
import AppSidebar from './components/AppSidebar.vue'

const auth = useAuthStore()
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
