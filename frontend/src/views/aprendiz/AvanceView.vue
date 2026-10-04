<script setup lang="ts">
// src/views/aprendiz/AvanceView.vue
// EXPLICACIÓN: avance + alertas en UNA vista => menos peticiones y contexto único
import { onMounted, ref } from 'vue'

import { api } from '../../api/client'
import type { Alerta, AvanceAprendiz } from '../../api/types'
import AlertaLista from '../../components/AlertaLista.vue'

const avance = ref<AvanceAprendiz | null>(null)
const alertas = ref<Alerta[]>([])
const ventana = ref(7)
const error = ref('')

async function cargarAlertas(): Promise<void> {
  alertas.value = await api<Alerta[]>(`/api/v1/aprendiz/alertas?dias=${ventana.value}`)
}

onMounted(async () => {
  try {
    const [a] = await Promise.all([api<AvanceAprendiz>('/api/v1/aprendiz/avance'), cargarAlertas()])
    avance.value = a
  } catch {
    error.value = 'No se pudo cargar tu avance.'
  }
})
</script>

<template>
  <div>
    <h1>Mi avance</h1>
    <div v-if="error" class="alerta-error">{{ error }}</div>

    <template v-if="avance">
      <div class="tarjeta">
        <h2>{{ avance.nombre_completo }}</h2>
        <p style="color: var(--texto-suave); margin-top: 0">
          Ficha {{ avance.numero_ficha }} · {{ avance.programa }}
        </p>

        <div class="barra-progreso" style="margin: 1rem 0 0.5rem">
          <div :style="{ width: `${avance.porcentaje_avance}%` }" />
        </div>
        <p style="font-weight: 700; margin: 0">
          {{ avance.porcentaje_avance }} % completado
        </p>
      </div>

      <div class="rejilla rejilla-3" style="margin-top: 1rem">
        <div class="tarjeta metrica">
          <div class="metrica-valor">{{ avance.total_evidencias }}</div>
          <div class="metrica-etiqueta">Evidencias</div>
        </div>
        <div class="tarjeta metrica">
          <div class="metrica-valor">{{ avance.aprobadas }}</div>
          <div class="metrica-etiqueta">Aprobadas</div>
        </div>
        <div class="tarjeta metrica">
          <div class="metrica-valor">{{ avance.total_evidencias - avance.aprobadas }}</div>
          <div class="metrica-etiqueta">Pendientes</div>
        </div>
      </div>

      <div class="tarjeta" style="margin-top: 1rem">
        <div style="display: flex; justify-content: space-between; align-items: center">
          <h2>Alertas de vencimiento</h2>
          <select v-model.number="ventana" class="btn" @change="cargarAlertas">
            <option :value="7">Próximos 7 días</option>
            <option :value="14">Próximos 14 días</option>
            <option :value="30">Próximos 30 días</option>
          </select>
        </div>
        <AlertaLista :alertas="alertas" />
      </div>
    </template>
  </div>
</template>
