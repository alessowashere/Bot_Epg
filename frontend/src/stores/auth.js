import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // Guardamos el usuario completo (incluye token JWT) en localStorage
  const usuario = ref(JSON.parse(localStorage.getItem('epg_usuario') || 'null'))
  const token = ref(localStorage.getItem('epg_token') || null)

  const isLoggedIn = computed(() => usuario.value !== null && token.value !== null)
  const rol = computed(() => usuario.value?.rol || null)
  const nombre = computed(() => usuario.value?.nombre_completo || '')
  const correo = computed(() => usuario.value?.correo || '')
  const isAdmin = computed(() => rol.value === 'Administrador')
  const isDirectora = computed(() => rol.value === 'Directora')
  const isDictaminante = computed(() => rol.value === 'Dictaminante')

  function login(loginResponse) {
    // loginResponse incluye: access_token, id_usuario, nombre_completo, correo, rol
    const { access_token, ...usuarioData } = loginResponse
    usuario.value = usuarioData
    token.value = access_token
    localStorage.setItem('epg_usuario', JSON.stringify(usuarioData))
    localStorage.setItem('epg_token', access_token)
  }

  function logout() {
    usuario.value = null
    token.value = null
    localStorage.removeItem('epg_usuario')
    localStorage.removeItem('epg_token')
  }

  return {
    usuario,
    token,
    isLoggedIn,
    rol,
    nombre,
    correo,
    isAdmin,
    isDirectora,
    isDictaminante,
    login,
    logout,
  }
})
