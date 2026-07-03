<template>
  <div>
    <h3>Bandeja de Monitoreo</h3>
    <div class="row mt-4">
      <div class="col-12">
        <div class="card shadow-sm">
          <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center">
            <span>Expedientes Sincronizados</span>
            <span class="badge bg-primary rounded-pill">{{ tickets.length }} Tickets</span>
          </div>
          <div class="card-body p-0">
            
            <div v-if="cargando" class="text-center p-5">
              <div class="spinner-border text-primary" role="status"></div>
              <p class="mt-2 text-muted">Consultando a FastAPI...</p>
            </div>

            <table v-else class="table table-hover mb-0">
              <thead class="table-light">
                <tr>
                  <th>Nº Ticket</th>
                  <th>Fecha</th>
                  <th>Asunto</th>
                  <th>Estado Bot</th>
                  <th>Archivos Adjuntos</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="t in tickets" :key="t.ticket_id">
                  <td><strong>{{ t.numero_visual }}</strong></td>
                  <td>{{ t.fecha }}</td>
                  <td>{{ t.asunto }}</td>
                  <td>
                    <span class="badge" 
                          :class="t.estado === 'Adjuntos_Descargados' ? 'bg-success' : 'bg-warning text-dark'">
                      {{ t.estado }}
                    </span>
                  </td>
                  <td>
                    <div class="d-flex flex-column gap-1">
                      <a v-for="adj in t.adjuntos" 
                         :key="adj.id_archivo" 
                         :href="adj.url_visor" 
                         target="_blank" 
                         class="btn btn-sm btn-outline-secondary text-start truncate-text"
                         title="Abrir PDF">
                         📎 {{ adj.nombre }}
                      </a>
                      <span v-if="t.adjuntos.length === 0" class="text-muted small">Sin adjuntos</span>
                    </div>
                  </td>
                  <td>
                    <div class="btn-group">
                      <button @click="actualizarEstado(t.ticket_id, 'Aprobado')" class="btn btn-sm btn-success">✓</button>
                      <button @click="actualizarEstado(t.ticket_id, 'Observado')" class="btn btn-sm btn-danger">✗</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="tickets.length === 0">
                  <td colspan="5" class="text-center py-4 text-muted">No hay expedientes en la base de datos.</td>
                </tr>
                  
              </tbody>
            </table>

          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const tickets = ref([])
const cargando = ref(true)

const cargarTickets = async () => {
  try {
    // Petición al endpoint expuesto por Nginx hacia FastAPI
    const respuesta = await axios.get('https://dataepis.uandina.pe:49267/bot-posgrado/api/tickets')
    tickets.value = respuesta.data.data
  } catch (error) {
    console.error("Error al cargar los expedientes:", error)
  } finally {
    cargando.value = false
  }
}

onMounted(() => {
  cargarTickets()
})
const actualizarEstado = async (id, estado) => {
  try {
    await axios.post(`https://dataepis.uandina.pe:49267/bot-posgrado/api/tickets/${id}/cambiar-estado`, null, {
      params: { nuevo_estado: estado }
    })
    cargarTickets() // Esto refresca la tabla automáticamente
  } catch (error) {
    alert("Error al actualizar el estado: " + error.message)
  }
}
</script>

<style scoped>
.truncate-text {
  max-width: 250px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
