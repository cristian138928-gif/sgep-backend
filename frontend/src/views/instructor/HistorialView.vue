<script setup lang="ts">
// src/views/instructor/HistorialView.vue
import { onMounted, ref } from 'vue'
import { History } from 'lucide-vue-next'

import { api } from '../../api/client'
import type { EstadoEvidencia, Pagina, Retroalimentacion } from '../../api/types'
import EstadoBadge from '../../components/EstadoBadge.vue'
import PaginacionBar from '../../components/PaginacionBar.vue'
import VacioEstado from '../../components/VacioEstado.vue'

const pagina = ref<Pagina<Retroalimentacion> | null>(null)
const paginaActual = ref(1)
const cargando = ref(true)
const error = ref('')

async function cargar(): Promise<void> {
  cargando.value = true
  try {
    pagina.value = await api<Pagina<Retroalimentacion>>(
      `/api/v1/instructor/historial?page=${paginaActual.value}&page_size=10`,
    )
  } catch {
    error.value = 'No se pudo cargar el historial.'
  } finally {
    cargando.value = false
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
    <div class="encabezado">
      <div>
        <div class="migas">Instructor · Seguimiento</div>
        <h1>Historial de evaluaciones</h1>
      </div>
    </div>
    <div v-if="error" class="alerta-error">{{ error }}</div>

    <div class="tarjeta tarjeta-flush">
      <VacioEstado
        v-if="cargando || !pagina || pagina.items.length === 0"
        :icono="History"
        :cargando="cargando"
        :titulo="cargando ? 'Cargando historial…' : 'Sin evaluaciones registradas'"
        :texto="
          cargando
            ? 'Estamos consultando tus evaluaciones.'
            : 'Las evaluaciones que registres aparecerán aquí.'
        "
      />

      <template v-else>
        <div class="tabla-contenedor tabla-plana">
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
                <td class="texto-suave ancho-max">{{ r.observaciones }}</td>
              </tr>
            </tbody>
          </table>
          <PaginacionBar
            :pagina="pagina.page"
            :total-paginas="pagina.total_pages"
            :pagina-actual="paginaActual"
            @cambiar="cambiarPagina"
          />
        </div>
      </template>
    </div>
  </div>
</template>
