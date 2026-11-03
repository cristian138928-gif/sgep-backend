<script setup lang="ts">
// src/views/aprendiz/AvanceView.vue
// EXPLICACIÓN: avance + alertas en UNA vista => menos peticiones y contexto único
import { computed, onMounted, ref } from 'vue'
import { Bell, Gauge, TrendingUp } from 'lucide-vue-next'

import { api } from '../../api/client'
import type { Alerta, AvanceAprendiz } from '../../api/types'
import AlertaLista from '../../components/AlertaLista.vue'
import KpiTarjeta from '../../components/KpiTarjeta.vue'

const avance = ref<AvanceAprendiz | null>(null)
const alertas = ref<Alerta[]>([])
const ventana = ref(7)
const error = ref('')

// EXPLICACIÓN: circunferencia SVG del anillo => porcentaje exacto sin redondeo visual
const CIRC = 2 * Math.PI * 62
const anilloOffset = computed(() => {
  const p = avance.value?.porcentaje_avance ?? 0
  return CIRC * (1 - p / 100)
})

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
    <div class="encabezado">
      <div>
        <div class="migas">Aprendiz · Etapa práctica</div>
        <h1>Mi avance</h1>
      </div>
    </div>
    <div v-if="error" class="alerta-error">{{ error }}</div>

    <template v-if="avance">
      <div class="tarjeta">
        <div class="cabecera-fila">
          <div>
            <h2 class="m-0">{{ avance.nombre_completo }}</h2>
            <p class="texto-suave sin-margen">
              Ficha {{ avance.numero_ficha }} · {{ avance.programa }}
            </p>
          </div>
          <span class="kpi-ico">
            <Gauge :size="18" />
          </span>
        </div>

        <div class="anillo-avance">
          <svg viewBox="0 0 140 140" class="anillo-svg" role="img" aria-label="Progreso general">
            <circle cx="70" cy="70" r="62" class="anillo-fondo" />
            <circle cx="70" cy="70" r="62" class="anillo-cilindro" :stroke-dashoffset="anilloOffset" />
          </svg>
          <div class="anillo-texto">{{ avance.porcentaje_avance }}%</div>
        </div>
        <p class="dato dato-fuerte centrado">
          {{ avance.porcentaje_avance }} % completado
        </p>
      </div>

      <div class="rejilla rejilla-3 mt-1">
        <KpiTarjeta
          etiqueta="Evidencias"
          :valor="avance.total_evidencias"
          :icono="TrendingUp"
          tono="azul"
        />
        <KpiTarjeta
          etiqueta="Aprobadas"
          :valor="avance.aprobadas"
          :icono="TrendingUp"
          tono="verde"
        />
        <KpiTarjeta
          etiqueta="Pendientes"
          :valor="avance.total_evidencias - avance.aprobadas"
          :icono="TrendingUp"
          tono="ambar"
        />
      </div>

      <div class="tarjeta mt-1">
        <div class="cabecera-fila separada">
          <h2 class="m-0">
            <Bell :size="16" class="ico-aviso" />
            Alertas de vencimiento
          </h2>
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
