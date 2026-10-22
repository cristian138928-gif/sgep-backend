<script setup lang="ts">
// src/views/instructor/PendientesView.vue
// EXPLICACIÓN: por-evaluar + estadísticas + alertas asignadas => bandeja única del instructor
import { onMounted, ref } from 'vue'
import { Bell, ClipboardCheck, Inbox, ListChecks } from 'lucide-vue-next'

import { api } from '../../api/client'
import type { AlertaRol, EstadisticasInstructor, Pagina } from '../../api/types'
import AlertaLista from '../../components/AlertaLista.vue'
import EstadoBadge from '../../components/EstadoBadge.vue'
import KpiTarjeta from '../../components/KpiTarjeta.vue'
import PaginacionBar from '../../components/PaginacionBar.vue'
import VacioEstado from '../../components/VacioEstado.vue'
import type { Evidencia } from '../../api/types'

const pagina = ref<Pagina<Evidencia> | null>(null)
const estadisticas = ref<EstadisticasInstructor | null>(null)
const alertas = ref<AlertaRol[]>([])
const paginaActual = ref(1)
const cargando = ref(true)
const error = ref('')

async function cargar(): Promise<void> {
  cargando.value = true
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

onMounted(cargar)
</script>

<template>
  <div>
    <div class="encabezado">
      <div>
        <div class="migas">Instructor · Bandeja</div>
        <h1>Bandeja de pendientes</h1>
      </div>
    </div>
    <div v-if="error" class="alerta-error">{{ error }}</div>

    <div v-if="estadisticas" class="rejilla rejilla-3">
      <KpiTarjeta
        etiqueta="Por evaluar"
        :valor="estadisticas.pendientes_por_evaluar"
        :icono="Inbox"
        tono="cian"
      />
      <KpiTarjeta
        etiqueta="Aprobadas"
        :valor="estadisticas.aprobadas"
        :icono="ClipboardCheck"
        tono="verde"
      />
      <KpiTarjeta
        etiqueta="Ajustes"
        :valor="estadisticas.ajustes_requeridos"
        :icono="ListChecks"
        tono="ambar"
      />
    </div>

    <div class="tarjeta mt-1">
      <div class="cabecera-fila separada">
        <h2 class="m-0">Evidencias por evaluar</h2>
        <span v-if="pagina" class="migas">{{ pagina.total }} en cola</span>
      </div>

      <VacioEstado
        v-if="cargando || !pagina || pagina.items.length === 0"
        :icono="ClipboardCheck"
        :cargando="cargando"
        titulo="Todo al día"
        :texto="
          cargando ? 'Consultando la bandeja…' : 'No hay evidencias pendientes de evaluación.'
        "
      />

      <template v-else>
        <div class="tabla-contenedor tabla-plana">
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
                <td class="der">
                  <router-link
                    class="btn btn-primario"
                    :to="{
                      name: 'evaluar',
                      params: { id: e.id_evidencia },
                      state: { evidencia: e },
                    }"
                  >
                    <ClipboardCheck :size="15" />
                    Evaluar
                  </router-link>
                </td>
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

    <div class="tarjeta mt-1">
      <div class="cabecera-fila separada">
        <h2 class="m-0">
          <Bell :size="16" class="ico-aviso" />
          Alertas de vencimiento
        </h2>
        <span class="migas">Mis aprendices</span>
      </div>
      <AlertaLista :alertas="alertas" mostrar-aprendiz />
    </div>
  </div>
</template>
