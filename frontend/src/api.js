import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'https://dataepis.uandina.pe:49267/bot-posgrado/api',
  timeout: 60000,
})

// ── Interceptor de solicitud: adjuntar Bearer Token JWT ─────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('epg_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ── Interceptor de respuesta: manejar 401 (token expirado) ──────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado o inválido — limpiar sesión y redirigir al login
      localStorage.removeItem('epg_token')
      localStorage.removeItem('epg_usuario')
      // Recargar para que Vue Router redirija al login
      if (window.location.hash !== '#/login') {
        window.location.replace('/#/login')
      }
    }
    return Promise.reject(error)
  }
)

export default api
