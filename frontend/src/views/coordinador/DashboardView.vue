<script setup lang="ts">
// src/views/coordinador/DashboardView.vue
// EXPLICACIÓN: KPIs globales + alertas + salida CSV del RF07 en una sola pantalla
import { onMounted, ref } from 'vue'

import { api, descargar, ApiError } from '../../api/client'
import type { AlertaRol, Estadisticas } from '../../api/types'
import AlertaLista from '../../components/AlertaLista.vue'

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
    <div style="display: flex; justify-content: space-between; align-items: center">
      <h1>Dashboard</h1>
      <div style="display: flex; gap: 0.6rem">
        <button
          class="btn"
          type="button"
          :disabled="exportando !== ''"
          @click="exportar('/api/v1/coordinador/exportar-evidencias', 'evidencias_sgep.csv', 'evidencias')"
        >
          {{ exportando === 'evidencias' ? 'Generando…' : 'CSV evidencias' }}
        </button>
        <button
          class="btn btn-suave"
          type="button"
          :disabled="exportando !== ''"
          @click="exportar('/api/v1/coordinador/exportar-avance', 'avance_aprendices_sgep.csv', 'avance')"
        >
          {{ exportando === 'avance' ? 'Generando…' : 'CSV avance (RF07)' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="alerta-error">{{ error }}</div>

    <template v-if="stats">
      <div class="rejilla rejilla-3">
        <div class="tarjeta metrica">
          <div class="metrica-valor">{{ stats.total_evidencias }}</div>
          <div class="metrica-etiqueta">Evidencias totales</div>
        </div>
        <div class="tarjeta metrica">
          <div class="metrica-valor">{{ stats.aprobadas }}</div>
          <div class="metrica-etiqueta">Aprobadas</div>
        </div>
        <div class="tarjeta metrica">
          <div class="metrica-valor">{{ stats.pendientes }}</div>
          <div class="metrica-etiqueta">Pendientes</div>
        </div>
        <div class="tarjeta metrica">
          <div class="metrica-valor">{{ stats.ajustes_requeridos }}</div>
          <div class="metrica-etiqueta">Ajustes requeridos</div>
        </div>
        <div class="tarjeta metrica">
          <div class="metrica-valor">{{ stats.total_aprendices }}</div>
          <div class="metrica-etiqueta">Aprendices</div>
        </div>
        <div class="tarjeta metrica">
          <div class="metrica-valor">{{ stats.total_instructores }}</div>
          <div class="metrica-etiqueta">Instructores</div>
        </div>
      </div>

      <div class="tarjeta" style="margin-top: 1rem">
        <h2>Aprobación global: {{ stats.porcentaje_aprobacion }} %</h2>
        <div class="barra-progreso">
          <div :style="{ width: `${stats.porcentaje_aprobacion}%` }" />
        </div>
      </div>
    </template>

    <div class="tarjeta" style="margin-top: 1rem">
      <h2>Alertas de vencimiento (todo el centro)</h2>
      <AlertaLista :alertas="alertas" mostrar-aprendiz />
    </div>
  </div>
</template>
