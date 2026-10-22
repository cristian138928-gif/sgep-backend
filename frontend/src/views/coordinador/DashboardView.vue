<script setup lang="ts">
// src/views/coordinador/DashboardView.vue
// EXPLICACIÓN: KPIs globales + alertas + salida CSV del RF07 en una sola pantalla
import { onMounted, ref } from 'vue'
import { CircleCheck, Download, Files, Inbox, TriangleAlert, Users, UserSquare2 } from 'lucide-vue-next'

import { api, descargar, ApiError } from '../../api/client'
import type { AlertaRol, Estadisticas } from '../../api/types'
import AlertaLista from '../../components/AlertaLista.vue'
import KpiTarjeta from '../../components/KpiTarjeta.vue'

const stats = ref<Estadisticas | null>(null)
const alertas = ref<AlertaRol[]>([])
const error = ref('')
const exportando = ref('')

async function exportar(ruta: string, archivo: string, clave: string): Promise<void> {
  error.value = ''
  exportando.value = clave
  try {
    await descargar(ruta, archivo)
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail : 'No se pudo generar el CSV.'
  } finally {
    exportando.value = ''
  }
}

onMounted(async () => {
  try {
    const [s, a] = await Promise.all([
      api<Estadisticas>('/api/v1/coordinador/estadisticas'),
      api<AlertaRol[]>('/api/v1/coordinador/alertas?dias=7'),
    ])
    stats.value = s
    alertas.value = a
  } catch {
    error.value = 'No se pudo cargar el dashboard.'
  }
})
</script>

<template>
  <div>
    <div class="encabezado">
      <div>
        <div class="migas">Coordinación · Panel general</div>
        <h1>Dashboard</h1>
      </div>
      <div class="acciones">
        <button
          class="btn"
          type="button"
          :disabled="exportando !== ''"
          @click="exportar('/api/v1/coordinador/exportar-evidencias', 'evidencias_sgep.csv', 'evidencias')"
        >
          <Download :size="15" />
          {{ exportando === 'evidencias' ? 'Generando…' : 'CSV evidencias' }}
        </button>
        <button
          class="btn btn-suave"
          type="button"
          :disabled="exportando !== ''"
          @click="exportar('/api/v1/coordinador/exportar-avance', 'avance_aprendices_sgep.csv', 'avance')"
        >
          <Download :size="15" />
          {{ exportando === 'avance' ? 'Generando…' : 'CSV avance (RF07)' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="alerta-error">{{ error }}</div>

    <template v-if="stats">
      <div class="rejilla rejilla-3">
        <KpiTarjeta
          etiqueta="Evidencias totales"
          :valor="stats.total_evidencias"
          :icono="Files"
          tono="azul"
        />
        <KpiTarjeta
          etiqueta="Aprobadas"
          :valor="stats.aprobadas"
          :icono="CircleCheck"
          tono="verde"
        />
        <KpiTarjeta
          etiqueta="Pendientes"
          :valor="stats.pendientes"
          :icono="Inbox"
          tono="cian"
        />
        <KpiTarjeta
          etiqueta="Ajustes requeridos"
          :valor="stats.ajustes_requeridos"
          :icono="TriangleAlert"
          tono="ambar"
        />
        <KpiTarjeta
          etiqueta="Aprendices"
          :valor="stats.total_aprendices"
          :icono="Users"
          tono="verde"
        />
        <KpiTarjeta
          etiqueta="Instructores"
          :valor="stats.total_instructores"
          :icono="UserSquare2"
          tono="azul"
        />
      </div>

      <div class="tarjeta mt-1">
        <div class="cabecera-fila separada">
          <div>
            <div class="migas">Cumplimiento global</div>
            <h2>Aprobación del centro</h2>
          </div>
          <span class="kpi-valor texto-verde">
            {{ stats.porcentaje_aprobacion }}%
          </span>
        </div>
        <div class="barra-progreso">
          <div :style="{ width: `${stats.porcentaje_aprobacion}%` }" />
        </div>
      </div>

      <div class="tarjeta mt-1">
        <div class="migas">Seguimiento</div>
        <h2>Alertas de vencimiento (todo el centro)</h2>
        <AlertaLista :alertas="alertas" mostrar-aprendiz />
      </div>
    </template>
  </div>
</template>
