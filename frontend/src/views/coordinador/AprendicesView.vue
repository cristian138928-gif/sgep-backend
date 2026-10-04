<script setup lang="ts">
// src/views/coordinador/AprendicesView.vue
// EXPLICACIÓN: avance por aprendiz + reporte RF07 (CSV exportar-avance)
import { onMounted, ref } from 'vue'

import { api, descargar, ApiError } from '../../api/client'
import type { AvanceAprendiz } from '../../api/types'

const aprendices = ref<AvanceAprendiz[]>([])
const programa = ref('')
const error = ref('')
const exportando = ref(false)

async function cargar(): Promise<void> {
  try {
    const qs = programa.value ? `?programa=${encodeURIComponent(programa.value)}` : ''
    aprendices.value = await api<AvanceAprendiz[]>(`/api/v1/coordinador/aprendices${qs}`)
  } catch {
    error.value = 'No se pudo cargar la lista de aprendices.'
  }
}

async function exportarAvance(): Promise<void> {
  error.value = ''
  exportando.value = true
  try {
    await descargar('/api/v1/coordinador/exportar-avance', 'avance_aprendices_sgep.csv')
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail : 'No se pudo generar el CSV.'
  } finally {
    exportando.value = false
  }
}

onMounted(cargar)
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center">
      <h1>Aprendices y avance</h1>
      <button class="btn btn-suave" type="button" :disabled="exportando" @click="exportarAvance">
        {{ exportando ? 'Generando…' : 'Exportar avance (RF07)' }}
      </button>
    </div>

    <div v-if="error" class="alerta-error">{{ error }}</div>

    <div class="tarjeta">
      <form style="display: flex; gap: 0.7rem; align-items: flex-end" @submit.prevent="cargar">
        <div class="campo" style="flex: 1; margin-bottom: 0">
          <label for="programa">Filtrar por programa</label>
          <input id="programa" v-model.trim="programa" type="text" placeholder="ADSO…" />
        </div>
        <button class="btn btn-primario" type="submit">Buscar</button>
        <button
          v-if="programa"
          class="btn"
          type="button"
          @click="programa = ''; cargar()"
        >
          Limpiar
        </button>
      </form>
    </div>

    <div class="tarjeta" style="margin-top: 1rem; padding: 0">
      <div v-if="aprendices.length === 0" class="vacio">
        <h3>Sin aprendices</h3>
        <p>No hay aprendices registrados o el filtro no coincide.</p>
      </div>

      <div v-else class="tabla-contenedor" style="border: none; box-shadow: none">
        <table class="tabla">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Ficha</th>
              <th>Programa</th>
              <th>Evidencias</th>
              <th>Aprobadas</th>
              <th>Avance</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in aprendices" :key="a.id_usuario">
              <td>{{ a.nombre_completo }}</td>
              <td>{{ a.numero_ficha }}</td>
              <td>{{ a.programa }}</td>
              <td>{{ a.total_evidencias }}</td>
              <td>{{ a.aprobadas }}</td>
              <td style="min-width: 160px">
                <div class="barra-progreso">
                  <div :style="{ width: `${a.porcentaje_avance}%` }" />
                </div>
                <small>{{ a.porcentaje_avance }} %</small>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
