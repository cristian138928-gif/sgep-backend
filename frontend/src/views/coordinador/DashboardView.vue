<script setup lang="ts">
// src/views/coordinador/DashboardView.vue
// EXPLICACIÓN: KPIs + distribución real de evidencias (SVG) + cumplimiento + alertas + CSV RF07
import { computed, onMounted, ref } from 'vue'
import { CircleCheck, Download, Files, Inbox, TriangleAlert, Users, UserSquare2 } from 'lucide-vue-next'

import { api, descargar, ApiError } from '../../api/client'
import type { AlertaRol, Estadisticas } from '../../api/types'
import AlertaLista from '../../components/AlertaLista.vue'
import KpiTarjeta from '../../components/KpiTarjeta.vue'

const stats = ref<Estadisticas | null>(null)
const alertas = ref<AlertaRol[]>([])
const error = ref('')
const exportando = ref('')

const R = 54
const CIRC = 2 * Math.PI * R

type Segmento = { etiqueta: string; valor: number; color: string }

const segmentos = computed<Segmento[]>(() => {
  if (!stats.value) return []
  return [
    { etiqueta: 'Aprobadas', valor: stats.value.aprobadas, color: '#059669' },
    { etiqueta: 'Pendientes', valor: stats.value.pendientes, color: '#d97706' },
    { etiqueta: 'Ajustes requeridos', valor: stats.value.ajustes_requeridos, color: '#e11d48' },
  ]
})

const totalSeg = computed(() => segmentos.value.reduce((a, s) => a + s.valor, 0))

// EXPLICACIÓN: acumulado de offsets => cada arco SVG inicia donde termina el anterior
const arcos = computed(() => {
  const total = totalSeg.value || 1
  let acc = 0
  return segmentos.value.map((s) => {
    const len = (s.valor / total) * CIRC
    const arc = { ...s, dash: `${len} ${CIRC - len}`, offset: -acc }
    acc += len
    return arc
  })
})

const barras = computed(() => {
  if (!stats.value) return []
  const max = Math.max(
    stats.value.aprobadas,
    stats.value.pendientes,
    stats.value.ajustes_requeridos,
    1,
  )
  return segmentos.value.map((s) => ({ ...s, pct: (s.valor / max) * 100 }))
})

const anilloAprobacion = computed(() => {
  const p = stats.value?.porcentaje_aprobacion ?? 0
  return CIRC * (1 - p / 100)
})

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

    <div v-if="error" class="alerta-error" role="alert">{{ error }}</div>

    <template v-if="stats">
      <div class="rejilla rejilla-3">
        <KpiTarjeta etiqueta="Evidencias totales" :valor="stats.total_evidencias" :icono="Files" tono="azul" />
        <KpiTarjeta etiqueta="Aprobadas" :valor="stats.aprobadas" :icono="CircleCheck" tono="verde" />
        <KpiTarjeta etiqueta="Pendientes" :valor="stats.pendientes" :icono="Inbox" tono="cian" />
        <KpiTarjeta etiqueta="Ajustes requeridos" :valor="stats.ajustes_requeridos" :icono="TriangleAlert" tono="ambar" />
        <KpiTarjeta etiqueta="Aprendices" :valor="stats.total_aprendices" :icono="Users" tono="verde" />
        <KpiTarjeta etiqueta="Instructores" :valor="stats.total_instructores" :icono="UserSquare2" tono="azul" />
      </div>

      <div class="rejilla rejilla-2 mt-4">
        <div class="tarjeta">
          <div class="cabecera-fila separada">
            <div>
              <div class="migas">Distribución</div>
              <h2>Estado de evidencias</h2>
            </div>
            <span class="dato text-slate-500">Total {{ stats.total_evidencias }}</span>
          </div>

          <div class="dist-wrap">
            <div class="donut-wrap" role="img" aria-label="Distribución de evidencias por estado">
              <svg viewBox="0 0 140 140" class="donut-svg">
                <circle cx="70" cy="70" :r="R" class="donut-track" />
                <g transform="rotate(-90 70 70)">
                  <circle
                    v-for="a in arcos"
                    :key="a.etiqueta"
                    cx="70"
                    cy="70"
                    :r="R"
                    fill="none"
                    :stroke="a.color"
                    stroke-width="16"
                    :stroke-dasharray="a.dash"
                    :stroke-dashoffset="a.offset"
                  />
                </g>
              </svg>
              <div class="donut-center">
                <div class="donut-total">{{ stats.total_evidencias }}</div>
                <div class="donut-label">evidencias</div>
              </div>
            </div>

            <ul class="leyenda">
              <li v-for="s in segmentos" :key="s.etiqueta">
                <span class="leyenda-dot" :style="{ background: s.color }" />
                <span class="leyenda-texto">{{ s.etiqueta }}</span>
                <span class="leyenda-valor">{{ s.valor }}</span>
                <span class="leyenda-pct">
                  {{ totalSeg ? ((s.valor / totalSeg) * 100).toFixed(1) : '0.0' }}%
                </span>
              </li>
            </ul>
          </div>

          <div class="barras mt-4">
            <div v-for="b in barras" :key="b.etiqueta" class="barra-fila">
              <span class="barra-nombre">{{ b.etiqueta }}</span>
              <div class="barra-track">
                <div class="barra-fill" :style="{ width: `${b.pct}%`, background: b.color }" />
              </div>
              <span class="barra-num">{{ b.valor }}</span>
            </div>
          </div>
        </div>

        <div class="tarjeta">
          <div class="cabecera-fila separada">
            <div>
              <div class="migas">Cumplimiento global</div>
              <h2>Tasa de aprobación</h2>
            </div>
          </div>

          <div class="aprob-wrap" role="img" aria-label="Porcentaje de aprobación global">
            <svg viewBox="0 0 140 140" class="donut-svg">
              <circle cx="70" cy="70" :r="R" class="donut-track" />
              <circle
                cx="70"
                cy="70"
                :r="R"
                class="anillo-aprob"
                :stroke-dasharray="CIRC"
                :stroke-dashoffset="anilloAprobacion"
                transform="rotate(-90 70 70)"
              />
            </svg>
            <div class="donut-center">
              <div class="donut-total texto-verde">{{ stats.porcentaje_aprobacion }}%</div>
              <div class="donut-label">aprobación</div>
            </div>
          </div>

          <div class="resumen-grid">
            <div class="resumen-item">
              <span class="resumen-dot" style="background:#059669" />
              <span>Aprobadas</span>
              <strong>{{ stats.aprobadas }}</strong>
            </div>
            <div class="resumen-item">
              <span class="resumen-dot" style="background:#d97706" />
              <span>Pendientes</span>
              <strong>{{ stats.pendientes }}</strong>
            </div>
            <div class="resumen-item">
              <span class="resumen-dot" style="background:#e11d48" />
              <span>Ajustes</span>
              <strong>{{ stats.ajustes_requeridos }}</strong>
            </div>
            <div class="resumen-item">
              <span class="resumen-dot" style="background:#2563eb" />
              <span>Total</span>
              <strong>{{ stats.total_evidencias }}</strong>
            </div>
          </div>
        </div>
      </div>

      <div class="tarjeta mt-4">
        <div class="migas">Seguimiento</div>
        <h2>Alertas de vencimiento (todo el centro)</h2>
        <AlertaLista :alertas="alertas" mostrar-aprendiz />
      </div>
    </template>
  </div>
</template>

<style scoped>
.dist-wrap { display: flex; align-items: center; gap: 1.25rem; flex-wrap: wrap; }
.donut-wrap, .aprob-wrap { position: relative; width: 160px; height: 160px; flex: none; }
.aprob-wrap { margin: 0 auto 0.5rem; }
.donut-svg { width: 100%; height: 100%; display: block; }
.donut-track { fill: none; stroke: #e2e8f0; stroke-width: 16; }
.donut-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.donut-total { font-family: var(--fuente-mono); font-size: 1.5rem; font-weight: 700; color: var(--texto); line-height: 1; }
.donut-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--texto-suave); margin-top: 2px; }
.anillo-aprob { fill: none; stroke: #059669; stroke-width: 16; stroke-linecap: round; transition: stroke-dashoffset 0.6s ease; }

.leyenda { list-style: none; margin: 0; padding: 0; flex: 1; min-width: 180px; display: grid; gap: 0.5rem; }
.leyenda li { display: grid; grid-template-columns: 10px 1fr auto auto; align-items: center; gap: 0.5rem; font-size: 0.85rem; }
.leyenda-dot, .resumen-dot { width: 10px; height: 10px; border-radius: 999px; flex: none; display: inline-block; }
.leyenda-texto { color: var(--texto); }
.leyenda-valor { font-family: var(--fuente-mono); font-weight: 700; color: var(--texto); }
.leyenda-pct { font-family: var(--fuente-mono); font-size: 0.75rem; color: var(--texto-suave); min-width: 3.2rem; text-align: right; }

.barras { display: grid; gap: 0.55rem; }
.barra-fila { display: grid; grid-template-columns: 120px 1fr 32px; align-items: center; gap: 0.6rem; font-size: 0.8rem; }
.barra-nombre { color: var(--texto-suave); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.barra-track { height: 10px; background: #f1f5f9; border-radius: 999px; overflow: hidden; border: 1px solid #e2e8f0; }
.barra-fill { height: 100%; border-radius: 999px; transition: width 0.5s ease; }
.barra-num { font-family: var(--fuente-mono); font-weight: 700; text-align: right; color: var(--texto); }

.resumen-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem 1rem; margin-top: 0.5rem; }
.resumen-item { display: grid; grid-template-columns: 10px 1fr auto; align-items: center; gap: 0.45rem; font-size: 0.85rem; color: var(--texto-suave); }
.resumen-item strong { font-family: var(--fuente-mono); color: var(--texto); }
</style>
