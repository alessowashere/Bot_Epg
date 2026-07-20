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
  const isSecretaria = computed(() => rol.value === 'Secretaria_Academica')
  const isDictaminante = computed(() => rol.value === 'Dictaminante')
  const isCoordinacion = computed(() => rol.value === 'Coordinacion_EPG')
  const requiereCambioPassword = computed(() => Boolean(usuario.value?.debe_cambiar_password))
  const enVistaRol = computed(() => Boolean(usuario.value?.modo_vista_rol))

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
    sessionStorage.removeItem('epg_sesion_admin_original')
    localStorage.removeItem('epg_token')
  }

  function actualizarPerfil(cambios) {
    if (!usuario.value) return
    usuario.value = { ...usuario.value, ...cambios }
    localStorage.setItem('epg_usuario', JSON.stringify(usuario.value))
  }

  function entrarVistaRol(respuesta) {
    if (!enVistaRol.value) {
      sessionStorage.setItem('epg_sesion_admin_original', JSON.stringify({
        token: token.value,
        usuario: usuario.value,
      }))
    }
    login(respuesta)
  }

  function salirVistaRol() {
    const original = sessionStorage.getItem('epg_sesion_admin_original')
    if (!original) return logout()
    const sesion = JSON.parse(original)
    usuario.value = sesion.usuario
    token.value = sesion.token
    localStorage.setItem('epg_usuario', JSON.stringify(sesion.usuario))
    localStorage.setItem('epg_token', sesion.token)
    sessionStorage.removeItem('epg_sesion_admin_original')
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
    isSecretaria,
    isDictaminante,
    isCoordinacion,
    requiereCambioPassword,
    enVistaRol,
    login,
    logout,
    actualizarPerfil,
    entrarVistaRol,
    salirVistaRol,
  }
})
