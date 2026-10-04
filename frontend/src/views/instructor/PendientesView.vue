<script setup lang="ts">
// src/views/instructor/PendientesView.vue
// EXPLICACIÓN: por-evaluar + estadísticas + alertas asignadas => bandeja única del instructor
import { onMounted, ref } from 'vue'

import { api } from '../../api/client'
import type { AlertaRol, EstadisticasInstructor, Pagina } from '../../api/types'
import AlertaLista from '../../components/AlertaLista.vue'
import EstadoBadge from '../../components/EstadoBadge.vue'
import type { Evidencia } from '../../api/types'

const pagina = ref<Pagina<Evidencia> | null>(null)
const estadisticas = ref<EstadisticasInstructor | null>(null)
const alertas = ref<AlertaRol[]>([])
const paginaActual = ref(1)
const error = ref('')

async function cargar(): Promise<void> {
  try {
    const [p, e, a] = await Promise.all([
      api<Pagina<Evidencia>>(
        `/api/v1/instructor/evidencias-pendientes?page=${paginaActual.value}&page_size=10`,
      ),
      api<EstadisticasInstructor>('/api/v1/instructor/estadisticas'),
      api<AlertaRol[]>('/api/v1/instructor/alertas?dias=7'),
    ])
    pagina.value = p
    estadisticas.value = e
    alertas.value = a
  } catch {
    error.value = 'No se pudo cargar la bandeja de pendientes.'
  }
}

function cambiarPagina(delta: number): void {
  const total = pagina.value?.total_pages ?? 1
  const destino = paginaActual.value + delta
  if (destino >= 1 && destino <= total) {
    paginaActual.value = destino
    void cargar()
  }
}

onMounted(cargar)
</script>

<template>
  <div>
    <h1>Bandeja de pendientes</h1>
    <div v-if="error" class="alerta-error">{{ error }}</div>

    <div v-if="estadisticas" class="rejilla rejilla-3">
      <div class="tarjeta metrica">
        <div class="metrica-valor">{{ estadisticas.pendientes_por_evaluar }}</div>
        <div class="metrica-etiqueta">Por evaluar</div>
      </div>
      <div class="tarjeta metrica">
        <div class="metrica-valor">{{ estadisticas.aprobadas }}</div>
        <div class="metrica-etiqueta">Aprobadas</div>
      </div>
      <div class="tarjeta metrica">
        <div class="metrica-valor">{{ estadisticas.ajustes_requeridos }}</div>
        <div class="metrica-etiqueta">Ajustes</div>
      </div>
    </div>

    <div class="tarjeta" style="margin-top: 1rem">
      <h2>Evidencias por evaluar</h2>
      <div v-if="!pagina || pagina.items.length === 0" class="vacio">
        <h3>Todo al día</h3>
        <p>No hay evidencias pendientes de evaluación.</p>
      </div>

      <template v-else>
        <div class="tabla-contenedor" style="box-shadow: none">
          <table class="tabla">
            <thead>
              <tr>
                <th>Título</th>
                <th>Tipo</th>
                <th>Estado</th>
                <th>Cargada</th>
                <th>Límite</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in pagina.items" :key="e.id_evidencia">
                <td>{{ e.titulo }}</td>
                <td>{{ e.tipo_formato }}</td>
                <td><EstadoBadge :estado="e.estado" /></td>
                <td>{{ e.fecha_carga.slice(0, 10) }}</td>
                <td>{{ e.fecha_deadline ? e.fecha_deadline.slice(0, 10) : '—' }}</td>
                <td style="text-align: right">
                  <router-link
                    class="btn btn-primario"
                    :to="{
                      name: 'evaluar',
                      params: { id: e.id_evidencia },
                      state: { evidencia: e },
                    }"
                  >
                    Evaluar
                  </router-link>
                </td>
              </tr>
            </tbody>
          </table>
          <div class="paginacion">
            <button class="btn" type="button" :disabled="paginaActual === 1" @click="cambiarPagina(-1)">
              Anterior
            </button>
            <span>Página {{ pagina.page }} de {{ pagina.total_pages }}</span>
            <button
              class="btn"
              type="button"
              :disabled="paginaActual === pagina.total_pages"
              @click="cambiarPagina(1)"
            >
              Siguiente
            </button>
          </div>
        </div>
      </template>
    </div>

    <div class="tarjeta" style="margin-top: 1rem">
      <h2>Alertas de vencimiento (mis aprendices)</h2>
      <AlertaLista :alertas="alertas" mostrar-aprendiz />
    </div>
  </div>
</template>
