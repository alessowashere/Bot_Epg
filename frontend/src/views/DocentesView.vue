<template>
  <div class="p-6 space-y-5 animate-fade-in">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-bold text-white">Docentes</h2>
        <p class="text-slate-400 text-sm mt-0.5">Carga laboral y asignaciones de tesis</p>
      </div>
      <button @click="abrirForm(null)" class="btn-primary">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg>
        Nuevo Docente
      </button>
    </div>

    <!-- Búsqueda -->
    <div class="relative">
      <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803a7.5 7.5 0 0010.607 10.607z" /></svg>
      <input v-model="busqueda" class="input-field pl-9" placeholder="Buscar docente..." />
    </div>

    <!-- Grilla de docentes -->
    <div v-if="cargando" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="i in 6" :key="i" class="h-32 bg-slate-800/60 rounded-xl animate-pulse"></div>
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div
        v-for="d in docentesFiltrados" :key="d.id_docente"
        class="card hover:border-slate-600 transition-all duration-200"
      >
        <div class="flex items-start gap-3">
          <!-- Avatar -->
          <div :class="['w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold flex-shrink-0',
            d.estado === 'Activo' ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-400']">
            {{ d.nombre_completo.split(' ')[0][0] }}{{ d.nombre_completo.split(' ')[1]?.[0] || '' }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="font-semibold text-white text-sm truncate">{{ d.nombre_completo }}</p>
            <p class="text-xs text-slate-400 truncate">{{ d.especialidad || 'Sin especialidad' }}</p>
            <div class="flex items-center gap-1.5 mt-1">
              <span :class="[
                'badge text-[10px]',
                d.estado === 'Activo' ? 'badge-graduado' :
                d.estado === 'De Licencia' ? 'badge-observado' : 'badge-caduco'
              ]">{{ d.estado }}</span>
              <span class="badge badge-nuevo text-[10px]">{{ d.tipo_contrato }}</span>
            </div>
          </div>
          <button @click="abrirForm(d)" class="btn-ghost btn-sm flex-shrink-0">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" /></svg>
          </button>
        </div>

        <!-- Barra de carga laboral -->
        <div class="mt-4">
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-[10px] text-slate-500">Carga laboral</span>
            <span class="text-xs font-bold" :class="d.carga_actual >= d.max_tesis_permitidas ? 'text-red-400' : 'text-emerald-400'">
              {{ d.carga_actual }} / {{ d.max_tesis_permitidas }}
            </span>
          </div>
          <div class="h-2 bg-slate-700 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :class="d.carga_actual >= d.max_tesis_permitidas ? 'bg-red-500' : d.carga_actual >= d.max_tesis_permitidas * 0.7 ? 'bg-amber-500' : 'bg-emerald-500'"
              :style="{ width: `${Math.min(100, (d.carga_actual / d.max_tesis_permitidas) * 100)}%` }"
            ></div>
          </div>
          <p v-if="!d.disponible" class="text-[10px] text-red-400 mt-1">Sin disponibilidad</p>
          <p v-else class="text-[10px] text-emerald-400 mt-1">Disponible para asignación</p>
        </div>
      </div>

      <div v-if="docentesFiltrados.length === 0" class="col-span-3 text-center py-12 text-slate-500">
        No hay docentes registrados
      </div>
    </div>

    <!-- Modal CRUD docente -->
    <div v-if="modalAbierto" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" @click.self="modalAbierto = false">
      <div class="card w-full max-w-md animate-slide-up">
        <h3 class="text-base font-bold text-white mb-5">{{ form.id_docente ? 'Editar Docente' : 'Nuevo Docente' }}</h3>
        <div class="space-y-4">
          <div>
            <label class="input-label">DNI *</label>
            <input v-model="form.dni" class="input-field font-mono" placeholder="12345678" />
          </div>
          <div>
            <label class="input-label">Nombre Completo *</label>
            <input v-model="form.nombre_completo" class="input-field" placeholder="Apellidos y Nombres" />
          </div>
          <div>
            <label class="input-label">Especialidad</label>
            <input v-model="form.especialidad" class="input-field" placeholder="Ej: Administración, Educación..." />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="input-label">Tipo Contrato *</label>
              <select v-model="form.tipo_contrato" class="input-field">
                <option value="Semestral">Semestral</option>
                <option value="Indeterminado">Indeterminado</option>
                <option value="Tiempo Completo">Tiempo Completo</option>
                <option value="Medio Tiempo">Medio Tiempo</option>
              </select>
            </div>
            <div>
              <label class="input-label">Estado</label>
              <select v-model="form.estado" class="input-field">
                <option value="Activo">Activo</option>
                <option value="Inactivo">Inactivo</option>
                <option value="De Licencia">De Licencia</option>
              </select>
            </div>
          </div>
          <div>
            <label class="input-label">Máx. Tesis Permitidas</label>
            <input v-model.number="form.max_tesis" type="number" min="1" max="20" class="input-field" />
          </div>
        </div>
        <div class="flex gap-3 mt-6">
          <button @click="modalAbierto = false" class="btn-ghost flex-1 justify-center">Cancelar</button>
          <button @click="guardar" :disabled="guardando" class="btn-primary flex-1 justify-center">
            <svg v-if="guardando" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            {{ guardando ? 'Guardando...' : form.id_docente ? 'Actualizar' : 'Crear Docente' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api.js'

const docentes = ref([])
const cargando = ref(true)
const busqueda = ref('')
const modalAbierto = ref(false)
const guardando = ref(false)

const form = ref({ id_docente: null, dni: '', nombre_completo: '', especialidad: '', tipo_contrato: 'Indeterminado', estado: 'Activo', max_tesis: 5 })

const docentesFiltrados = computed(() => {
  if (!busqueda.value.trim()) return docentes.value
  const q = busqueda.value.toLowerCase()
  return docentes.value.filter(d =>
    d.nombre_completo.toLowerCase().includes(q) ||
    (d.especialidad || '').toLowerCase().includes(q) ||
    d.dni.includes(q)
  )
})

function abrirForm(docente) {
  if (docente) {
    form.value = { id_docente: docente.id_docente, dni: docente.dni, nombre_completo: docente.nombre_completo, especialidad: docente.especialidad || '', tipo_contrato: docente.tipo_contrato, estado: docente.estado, max_tesis: docente.max_tesis_permitidas }
  } else {
    form.value = { id_docente: null, dni: '', nombre_completo: '', especialidad: '', tipo_contrato: 'Indeterminado', estado: 'Activo', max_tesis: 5 }
  }
  modalAbierto.value = true
}

async function guardar() {
  guardando.value = true
  try {
    const params = {
      nombre_completo: form.value.nombre_completo,
      especialidad: form.value.especialidad || undefined,
      tipo_contrato: form.value.tipo_contrato,
      estado: form.value.estado,
      max_tesis: form.value.max_tesis
    }
    if (form.value.id_docente) {
      await api.put(`/docentes/${form.value.id_docente}`, null, { params })
    } else {
      await api.post('/docentes', null, { params: { ...params, dni: form.value.dni } })
    }
    modalAbierto.value = false
    await cargar()
  } catch (e) {
    console.error(e)
  } finally {
    guardando.value = false
  }
}

async function cargar() {
  cargando.value = true
  try {
    const res = await api.get('/docentes')
    docentes.value = res.data.data
  } catch (e) {
    console.error(e)
  } finally {
    cargando.value = false
  }
}

onMounted(cargar)
</script>
