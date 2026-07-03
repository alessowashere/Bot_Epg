<template>
  <!-- Timeline horizontal de los 7 pasos -->
  <div class="w-full overflow-x-auto py-2">
    <div class="flex items-start min-w-max gap-0">
      <template v-for="(paso, idx) in pasos" :key="paso.id_paso">
        <!-- Nodo del paso -->
        <div class="flex flex-col items-center" style="min-width: 120px;">
          <!-- Círculo del paso -->
          <div class="relative">
            <div :class="[
              'w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all duration-300',
              estado(paso.id_paso) === 'activo'    ? 'bg-indigo-600 border-indigo-400 text-white shadow-lg shadow-indigo-500/40 ring-2 ring-indigo-400 ring-offset-2 ring-offset-slate-800' : '',
              estado(paso.id_paso) === 'completado' ? 'bg-emerald-600 border-emerald-400 text-white' : '',
              estado(paso.id_paso) === 'pendiente'  ? 'bg-slate-800 border-slate-600 text-slate-400' : '',
            ]">
              <!-- Check si completado -->
              <svg v-if="estado(paso.id_paso) === 'completado'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
              </svg>
              <span v-else>{{ paso.id_paso }}</span>
            </div>
            <!-- Punto pulsante si activo -->
            <span v-if="estado(paso.id_paso) === 'activo'"
              class="absolute -top-0.5 -right-0.5 w-3 h-3 bg-indigo-400 rounded-full animate-pulse-dot">
            </span>
          </div>

          <!-- Nombre del paso -->
          <p :class="[
            'text-center text-[10px] font-medium mt-2 leading-tight px-1',
            estado(paso.id_paso) === 'activo'     ? 'text-indigo-300' : '',
            estado(paso.id_paso) === 'completado' ? 'text-emerald-400' : '',
            estado(paso.id_paso) === 'pendiente'  ? 'text-slate-500' : '',
          ]" style="max-width: 100px;">
            {{ paso.nombre_paso }}
          </p>
        </div>

        <!-- Línea conectora entre pasos -->
        <div v-if="idx < pasos.length - 1"
          class="h-px mt-[18px] flex-1"
          :class="pasoActual > idx + 1 ? 'bg-emerald-500' : 'bg-slate-700'"
          style="min-width: 24px; max-width: 48px;">
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  pasoActual: {
    type: Number,
    required: true
  },
  pasos: {
    type: Array,
    default: () => [
      { id_paso: 1, nombre_paso: 'Nombramiento de Asesor' },
      { id_paso: 2, nombre_paso: 'Dictamen de Proyecto' },
      { id_paso: 3, nombre_paso: 'Inscripción de Proyecto' },
      { id_paso: 4, nombre_paso: 'Declarado Apto' },
      { id_paso: 5, nombre_paso: 'Dictamen de Tesis' },
      { id_paso: 6, nombre_paso: 'Sustentación' },
      { id_paso: 7, nombre_paso: 'Trámite Diploma' },
    ]
  }
})

function estado(idPaso) {
  if (idPaso < props.pasoActual) return 'completado'
  if (idPaso === props.pasoActual) return 'activo'
  return 'pendiente'
}
</script>
