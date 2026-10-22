<script setup lang="ts">
// src/views/coordinador/AprendicesView.vue
// EXPLICACIÓN: avance por aprendiz + reporte RF07 (CSV exportar-avance)
import { onMounted, ref } from 'vue'
import { Download, Search, Users, X } from 'lucide-vue-next'

import { api, descargar, ApiError } from '../../api/client'
import type { AvanceAprendiz } from '../../api/types'
import VacioEstado from '../../components/VacioEstado.vue'

const aprendices = ref<AvanceAprendiz[]>([])
const programa = ref('')
const cargando = ref(true)
const error = ref('')
const exportando = ref(false)

async function cargar(): Promise<void> {
  cargando.value = true
  try {
    const qs = programa.value ? `?programa=${encodeURIComponent(programa.value)}` : ''
    aprendices.value = await api<AvanceAprendiz[]>(`/api/v1/coordinador/aprendices${qs}`)
  } catch {
    error.value = 'No se pudo cargar la lista de aprendices.'
  } finally {
    cargando.value = false
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
    <div class="encabezado">
      <div>
        <div class="migas">Coordinación · Reportes</div>
        <h1>Aprendices y avance</h1>
      </div>
      <div class="acciones">
        <button class="btn btn-suave" type="button" :disabled="exportando" @click="exportarAvance">
          <Download :size="15" />
          {{ exportando ? 'Generando…' : 'Exportar avance (RF07)' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="alerta-error">{{ error }}</div>

    <div class="tarjeta">
      <form class="fila fila-fin" @submit.prevent="cargar">
        <div class="campo">
          <label for="programa">Filtrar por programa</label>
          <input id="programa" v-model.trim="programa" type="text" placeholder="ADSO…" />
        </div>
        <button class="btn btn-primario" type="submit">
          <Search :size="15" />
          Buscar
        </button>
        <button
          v-if="programa"
          class="btn"
          type="button"
          @click="programa = ''; cargar()"
        >
          <X :size="15" />
          Limpiar
        </button>
      </form>
    </div>

    <div class="tarjeta tarjeta-flush mt-1">
      <VacioEstado
        v-if="cargando || aprendices.length === 0"
        :icono="Users"
        :cargando="cargando"
        titulo="Sin aprendices"
        :texto="
          cargando ? 'Consultando el registro…' : 'No hay aprendices registrados o el filtro no coincide.'
        "
      />

      <div v-else class="tabla-contenedor tabla-plana">
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
              <td class="ancho-min">
                <div class="barra-progreso">
                  <div :style="{ width: `${a.porcentaje_avance}%` }" />
                </div>
                <small class="dato">{{ a.porcentaje_avance }} %</small>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
