<script setup lang="ts">
// src/views/instructor/HistorialView.vue
import { onMounted, ref } from 'vue'

import { api } from '../../api/client'
import type { EstadoEvidencia, Pagina, Retroalimentacion } from '../../api/types'
import EstadoBadge from '../../components/EstadoBadge.vue'

const pagina = ref<Pagina<Retroalimentacion> | null>(null)
const paginaActual = ref(1)
const error = ref('')

async function cargar(): Promise<void> {
  try {
    pagina.value = await api<Pagina<Retroalimentacion>>(
      `/api/v1/instructor/historial?page=${paginaActual.value}&page_size=10`,
    )
  } catch {
    error.value = 'No se pudo cargar el historial.'
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

function fechaCorta(iso: string): string {
  return new Date(iso).toLocaleDateString('es-CO', { dateStyle: 'medium' })
}

onMounted(cargar)
</script>

<template>
  <div>
    <h1>Historial de evaluaciones</h1>
    <div v-if="error" class="alerta-error">{{ error }}</div>

    <div class="tarjeta" style="padding: 0">
      <div v-if="!pagina || pagina.items.length === 0" class="vacio">
        <h3>Sin evaluaciones registradas</h3>
        <p>Las evaluaciones que registres aparecerán aquí.</p>
      </div>

      <template v-else>
        <div class="tabla-contenedor" style="border: none; box-shadow: none">
          <table class="tabla">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Evidencia</th>
                <th>Resultado</th>
                <th>Observaciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in pagina.items" :key="r.id_retroalimentacion">
                <td>{{ fechaCorta(r.fecha_revision) }}</td>
                <td>#{{ r.id_evidencia }}</td>
                <td>
                  <EstadoBadge :estado="r.estado_evaluacion as EstadoEvidencia" />
                </td>
                <td style="max-width: 420px">{{ r.observaciones }}</td>
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
  </div>
</template>
