import axios from 'axios'

function obtenerDispositivoSesion() {
  let dispositivo = localStorage.getItem('epg_dispositivo_id')
  if (!dispositivo) {
    dispositivo = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`
    localStorage.setItem('epg_dispositivo_id', dispositivo)
  }
  return dispositivo
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/bot-posgrado/api',
  timeout: 60000,
})

// ── Interceptor de solicitud: adjuntar Bearer Token JWT ─────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('epg_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    config.headers['X-EPG-Device-ID'] = obtenerDispositivoSesion()
    return config
  },
  (error) => Promise.reject(error)
)

// ── Interceptor de respuesta: manejar 401 (token expirado) ──────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const detalle = error.response?.data?.detail || error.message || 'No se pudo completar la operación.'
    if (error.response?.status === 403 && error.response?.data?.code === 'cambio_password_requerido') {
      if (window.location.pathname !== '/a1') {
        window.location.replace('/a1')
      }
    }
    if (status === 401) {
      // Token expirado o inválido — limpiar sesión y redirigir al login
      localStorage.removeItem('epg_token')
      localStorage.removeItem('epg_usuario')
      // Recargar para que Vue Router redirija al login
      if (window.location.pathname !== '/a0') {
        window.location.replace('/a0')
      }
    }
    if (status && status !== 401) {
      window.dispatchEvent(new CustomEvent('epg:api-error', {
        detail: { status, mensaje: typeof detalle === 'string' ? detalle : 'No se pudo completar la operación.' },
      }))
    }
    return Promise.reject(error)
  }
)

export default api
