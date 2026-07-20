<template>
  <div class="page-shell animate-fade-in">
    <div class="flex items-center justify-between">
      <div>
        <p class="eyebrow">Administracion</p>
        <h2 class="page-title">Usuarios y accesos</h2>
        <p class="page-subtitle">Solo accesible para Administradores</p>
      </div>
      <button @click="abrirForm(null)" class="btn-primary">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
        Nuevo Usuario
      </button>
    </div>

    <!-- Tabla de usuarios -->
    <div class="card p-0 overflow-hidden">
      <div v-if="cargando" class="p-4 space-y-3">
        <div v-for="i in 4" :key="i" class="h-14 bg-slate-700/30 rounded-lg animate-pulse"></div>
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Usuario</th>
            <th>Correo</th>
            <th>Rol</th>
            <th>Acceso</th>
            <th>Estado</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="usuarios.length === 0">
            <td colspan="6" class="text-center py-8 text-slate-500">No hay usuarios registrados</td>
          </tr>
          <tr v-for="u in usuarios" :key="u.id_usuario">
            <td>
              <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
                  {{ u.nombre_completo.split(' ').slice(0,2).map(n=>n[0]).join('') }}
                </div>
                <span class="font-medium text-slate-900 dark:text-white">{{ u.nombre_completo }}</span>
              </div>
            </td>
            <td class="text-slate-400 text-sm">{{ u.correo }}</td>
            <td>
              <span :class="rolBadge(u.rol)">{{ u.rol }}</span>
            </td>
            <td>
              <span :class="u.password_configurada ? 'badge-graduado' : 'badge-observado'">
                {{ u.debe_cambiar_password ? 'Cambio obligatorio' : (u.password_configurada ? 'Configurada' : 'Sin contrasena') }}
              </span>
            </td>
            <td>
              <span :class="u.activo ? 'badge-graduado' : 'badge-caduco'">
                {{ u.activo ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td>
              <div class="flex items-center gap-1">
                <button @click="abrirForm(u)" class="btn-ghost btn-sm" title="Editar usuario" aria-label="Editar usuario">
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" /></svg>
                </button>
                <button
                  v-if="u.rol !== 'Administrador'"
                  type="button"
                  class="btn-ghost btn-sm text-sky-600 hover:text-sky-800"
                  title="Abrir vista de solo lectura con este rol"
                  aria-label="Abrir vista de solo lectura con este rol"
                  @click="abrirVistaRol(u)"
                >
                  <i class="pi pi-eye text-xs"></i>
                </button>
                <button @click="desactivar(u)" class="btn-ghost btn-sm text-red-400 hover:text-red-300" title="Desactivar usuario" aria-label="Desactivar usuario">
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <div v-if="modalAbierto" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" @click.self="modalAbierto = false">
      <div class="card w-full max-w-md animate-slide-up">
        <h3 class="text-base font-bold text-slate-900 dark:text-white mb-5">{{ form.id_usuario ? 'Editar Usuario' : 'Nuevo Usuario' }}</h3>
        <div class="space-y-4">
          <div>
            <label class="input-label">Nombre Completo *</label>
            <input v-model="form.nombre_completo" class="input-field" placeholder="Apellidos y Nombres" />
          </div>
          <div>
            <label class="input-label">Correo *</label>
            <input v-model="form.correo" class="input-field" type="email" placeholder="usuario@uandina.edu.pe" />
          </div>
          <div>
            <label class="input-label">Rol *</label>
            <select v-model="form.rol" class="input-field">
              <option value="Administrador">Administrador</option>
              <option value="Recepcion">Recepción</option>
              <option value="Secretaria_Academica">Secretaría Académica</option>
              <option value="Directora">Directora</option>
              <option value="Dictaminante">Dictaminante</option>
            </select>
          </div>
          <div>
            <label for="usuario-password" class="input-label">{{ form.id_usuario ? 'Nueva contrasena' : 'Contrasena' }}</label>
            <input
              id="usuario-password"
              v-model="form.password"
              type="password"
              name="new-password"
              class="input-field"
              minlength="12"
              autocomplete="new-password"
              placeholder="12+ caracteres, mayúscula, minúscula y número"
            />
            <p v-if="form.id_usuario" class="mt-1 text-xs text-slate-500">Dejar vacío conserva la contraseña. Al restablecerla, la persona deberá cambiarla al ingresar.</p>
          </div>
        </div>
        <div class="flex gap-3 mt-6">
          <button @click="modalAbierto = false" class="btn-ghost flex-1 justify-center">Cancelar</button>
          <button @click="guardar" :disabled="guardando" class="btn-primary flex-1 justify-center">
            <svg v-if="guardando" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            {{ form.id_usuario ? 'Actualizar' : 'Crear Usuario' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api.js'
import { useAuthStore } from '../stores/auth.js'

const usuarios = ref([])
const cargando = ref(true)
const modalAbierto = ref(false)
const guardando = ref(false)
const form = ref({ id_usuario: null, nombre_completo: '', correo: '', rol: 'Recepcion', password: '' })

function rolBadge(rol) {
  const map = {
    'Administrador': 'badge bg-red-500/20 text-red-300 border border-red-500/30',
    'Directora': 'badge bg-violet-500/20 text-violet-300 border border-violet-500/30',
    'Recepcion': 'badge-proceso',
    'Secretaria_Academica': 'badge bg-cyan-500/20 text-cyan-300 border border-cyan-500/30',
    'Dictaminante': 'badge bg-emerald-500/20 text-emerald-300 border border-emerald-500/30',
  }
  return map[rol] || 'badge'
}

function abrirForm(u) {
  if (u) {
    form.value = { id_usuario: u.id_usuario, nombre_completo: u.nombre_completo, correo: u.correo, rol: u.rol, password: '' }
  } else {
    form.value = { id_usuario: null, nombre_completo: '', correo: '', rol: 'Recepcion', password: '' }
  }
  modalAbierto.value = true
}

async function guardar() {
  guardando.value = true
  try {
    const params = { nombre_completo: form.value.nombre_completo, correo: form.value.correo, rol: form.value.rol }
    let idUsuario = form.value.id_usuario
    if (idUsuario) {
      await api.put(`/usuarios/${idUsuario}`, null, { params: { ...params, activo: true } })
    } else {
      const respuesta = await api.post('/usuarios', null, { params })
      idUsuario = respuesta.data.id_usuario
    }
    if (form.value.password) {
      await api.put(`/usuarios/${idUsuario}/cambiar-password`, { nueva_password: form.value.password })
    }
    modalAbierto.value = false
    await cargar()
  } catch (e) { console.error(e) } finally { guardando.value = false }
}

async function desactivar(u) {
  if (!confirm(`¿Desactivar a ${u.nombre_completo}?`)) return
  try {
    await api.put(`/usuarios/${u.id_usuario}`, null, { params: { nombre_completo: u.nombre_completo, correo: u.correo, rol: u.rol, activo: false } })
    await cargar()
  } catch (e) { console.error(e) }
}

async function abrirVistaRol(u) {
  if (!confirm(`Abrir vista de solo lectura como ${u.nombre_completo}? No se podrán guardar cambios.`)) return
  try {
    const respuesta = await api.post('/auth/vista-rol', { id_usuario: u.id_usuario })
    useAuthStore().entrarVistaRol(respuesta.data)
    window.location.assign('/')
  } catch (e) {
    console.error(e)
  }
}

async function cargar() {
  cargando.value = true
  try {
    const res = await api.get('/usuarios')
    usuarios.value = res.data
  } catch (e) { console.error(e) } finally { cargando.value = false }
}

onMounted(cargar)
</script>
