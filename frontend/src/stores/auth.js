import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const usuario = ref(JSON.parse(localStorage.getItem('epg_usuario') || 'null'))

  const isLoggedIn = computed(() => usuario.value !== null)
  const rol = computed(() => usuario.value?.rol || null)
  const nombre = computed(() => usuario.value?.nombre_completo || '')
  const isAdmin = computed(() => rol.value === 'Administrador')
  const isDirectora = computed(() => rol.value === 'Directora')

  function login(usuarioData) {
    usuario.value = usuarioData
    localStorage.setItem('epg_usuario', JSON.stringify(usuarioData))
  }

  function logout() {
    usuario.value = null
    localStorage.removeItem('epg_usuario')
  }

  return { usuario, isLoggedIn, rol, nombre, isAdmin, isDirectora, login, logout }
})
