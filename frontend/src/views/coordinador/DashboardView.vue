<script setup lang="ts">
// src/views/coordinador/DashboardView.vue
// EXPLICACIÓN: Dashboard ejecutivo con métricas reales (stats/alertas) y visualización SVG dinámica
import { computed, onMounted, ref } from 'vue'
import {
  Activity,
  AlertTriangle,
  CircleCheck,
  Download,
  Files,
  Inbox,
  ShieldCheck,
  Target,
  TrendingUp,
  TriangleAlert,
  Users,
  UserSquare2,
} from 'lucide-vue-next'

import { api, descargar, ApiError } from '../../api/client'
import type { AlertaRol, Estadisticas } from '../../api/types'
import AlertaLista from '../../components/AlertaLista.vue'
import KpiTarjeta from '../../components/KpiTarjeta.vue'

const stats = ref<Estadisticas | null>(null)
const alertas = ref<AlertaRol[]>([])
const cargando = ref(true)
const error = ref('')
const exportando = ref('')

const R = 54
const CIRC = 2 * Math.PI * R

type Segmento = { clave: string; etiqueta: string; valor: number; color: string; tono: string }

const segmentos = computed<Segmento[]>(() => {
  if (!stats.value) return []
  return [
    { clave: 'aprobadas', etiqueta: 'Aprobadas', valor: stats.value.aprobadas, color: '#059669', tono: 'rgba(5,150,105,0.12)' },
    { clave: 'pendientes', etiqueta: 'Pendientes', valor: stats.value.pendientes, color: '#d97706', tono: 'rgba(217,119,6,0.12)' },
    { clave: 'ajustes', etiqueta: 'Ajustes requeridos', valor: stats.value.ajustes_requeridos, color: '#e11d48', tono: 'rgba(225,29,72,0.12)' },
  ]
})

const total = computed(() => stats.value?.total_evidencias ?? 0)
const enProceso = computed(() => (stats.value ? stats.value.pendientes + stats.value.ajustes_requeridos : 0))

function pct(valor: number): number {
  return total.value ? (valor / total.value) * 100 : 0
}
function fmtPct(valor: number): string {
  return `${pct(valor).toFixed(1)}%`
}

const arcos = computed(() => {
  const t = total.value || 1
  let acc = 0
  return segmentos.value.map((s) => {
    const len = (s.valor / t) * CIRC
    const arc = { ...s, dash: `${len} ${CIRC - len}`, offset: -acc, porcentaje: pct(s.valor) }
    acc += len
    return arc
  })
})

const barras = computed(() => {
  const max = Math.max(...segmentos.value.map((s) => s.valor), 1)
  return segmentos.value.map((s) => ({ ...s, ancho: (s.valor / max) * 100, porcentaje: pct(s.valor) }))
})

const stack = computed(() => segmentos.value.map((s) => ({ ...s, ancho: pct(s.valor) })))

const anilloAprobacion = computed(() => CIRC * (1 - (stats.value?.porcentaje_aprobacion ?? 0) / 100))

const promedioPorAprendiz = computed(() => {
  if (!stats.value || stats.value.total_aprendices === 0) return '0.0'
  return (stats.value.total_evidencias / stats.value.total_aprendices).toFixed(1)
})

const alertasVencidas = computed(() => alertas.value.filter((a) => a.estado_alerta === 'Vencida').length)
const alertasPorVencer = computed(() => alertas.value.filter((a) => a.estado_alerta !== 'Vencida').length)

const salud = computed(() => {
  const p = stats.value?.porcentaje_aprobacion ?? 0
  if (p >= 80) return { titulo: 'Salud óptima', texto: 'La mayoría de evidencias están aprobadas y el flujo avanza correctamente.', clase: 'ok' }
  if (p >= 50) return { titulo: 'Salud estable', texto: 'Hay avance, pero conviene reducir pendientes y ajustes para mejorar la tasa.', clase: 'medio' }
  if (total.value === 0) return { titulo: 'Sin datos', texto: 'Aún no hay evidencias registradas para calcular indicadores.', clase: 'neutro' }
  return { titulo: 'Atención requerida', texto: 'La proporción de pendientes/ajustes es alta; prioriza revisión y seguimiento.', clase: 'critico' }
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
  } finally {
    cargando.value = false
  }
})
</script>

<template>
  <div class="dashboard">
    <header class="hero">
      <div>
        <div class="migas">Coordinaci\u00f3n \u00b7 Panel ejecutivo</div>
        <h1 class="flex items-center gap-2"><span class="inline-block h-2.5 w-2.5 rounded-full bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.15)]"></span> Dashboard general</h1>
        <p class="hero-sub">Seguimiento en tiempo real del estado de evidencias, cumplimiento y alertas del centro.</p>
      </div>
      <div class="acciones hero-actions">
        <button class="btn" type="button" :disabled="exportando !== '' || cargando" @click="exportar('/api/v1/coordinador/exportar-evidencias', 'evidencias_sgep.csv', 'evidencias')">
          <Download :size="15" />
          {{ exportando === 'evidencias' ? 'Generando…' : 'Exportar evidencias' }}
        </button>
        <button class="btn btn-suave" type="button" :disabled="exportando !== '' || cargando" @click="exportar('/api/v1/coordinador/exportar-avance', 'avance_aprendices_sgep.csv', 'avance')">
          <Download :size="15" />
          {{ exportando === 'avance' ? 'Generando…' : 'Reporte de avance (RF07)' }}
        </button>
      </div>
    </header>

    <div v-if="error" class="alerta-error" role="alert">{{ error }}</div>

    <template v-if="cargando">
      <div class="rejilla rejilla-3">
        <div v-for="n in 6" :key="n" class="tarjeta skeleton-card"></div>
      </div>
      <div class="rejilla rejilla-2 mt-4">
        <div class="tarjeta skeleton-panel"></div>
        <div class="tarjeta skeleton-panel"></div>
      </div>
    </template>

    <template v-else-if="stats">
      <section class="rejilla rejilla-3">
        <KpiTarjeta etiqueta="Evidencias totales" :valor="stats.total_evidencias" :icono="Files" tono="azul" />
        <KpiTarjeta etiqueta="Aprobadas" :valor="stats.aprobadas" :icono="CircleCheck" tono="verde" />
        <KpiTarjeta etiqueta="Pendientes" :valor="stats.pendientes" :icono="Inbox" tono="cian" />
        <KpiTarjeta etiqueta="Ajustes requeridos" :valor="stats.ajustes_requeridos" :icono="TriangleAlert" tono="ambar" />
        <KpiTarjeta etiqueta="Aprendices activos" :valor="stats.total_aprendices" :icono="Users" tono="verde" />
        <KpiTarjeta etiqueta="Instructores" :valor="stats.total_instructores" :icono="UserSquare2" tono="azul" />
      </section>

      <section class="panel-grid mt-4">
        <article class="tarjeta panel-principal">
          <div class="panel-head">
            <div>
              <div class="migas">Análisis de evidencias</div>
              <h2>Distribución y composición por estado</h2>
              <p class="panel-desc">Visualización basada en registros reales del sistema.</p>
            </div>
            <div class="chip-total"><span>Total</span><strong>{{ total }}</strong></div>
          </div>

          <div class="stack-wrap" aria-label="Composición porcentual por estado">
            <div class="stack-bar">
              <div v-for="s in stack" :key="s.clave" class="stack-seg" :style="{ width: `${s.ancho}%`, background: s.color }" :title="`${s.etiqueta}: ${s.valor}`"></div>
            </div>
            <div class="stack-legend">
              <span v-for="s in segmentos" :key="s.clave"><i :style="{ background: s.color }"></i>{{ s.etiqueta }} · {{ fmtPct(s.valor) }}</span>
            </div>
          </div>

          <div class="viz-grid">
            <div class="donut-card">
              <div class="donut-wrap" role="img" aria-label="Distribución de evidencias por estado">
                <svg viewBox="0 0 140 140" class="donut-svg">
                  <circle cx="70" cy="70" :r="R" class="donut-track" />
                  <g transform="rotate(-90 70 70)">
                    <circle v-for="a in arcos" :key="a.clave" cx="70" cy="70" :r="R" fill="none" :stroke="a.color" stroke-width="14" stroke-linecap="butt" :stroke-dasharray="a.dash" :stroke-dashoffset="a.offset" />
                  </g>
                </svg>
                <div class="donut-center">
                  <div class="donut-total">{{ total }}</div>
                  <div class="donut-label">evidencias</div>
                </div>
              </div>
              <ul class="leyenda">
                <li v-for="s in segmentos" :key="s.clave">
                  <span class="dot" :style="{ background: s.color }"></span>
                  <span class="leyenda-name">{{ s.etiqueta }}</span>
                  <span class="leyenda-val">{{ s.valor }}</span>
                  <span class="leyenda-pct">{{ fmtPct(s.valor) }}</span>
                </li>
              </ul>
            </div>

            <div class="bars-card">
              <div class="subhead"><Activity :size="15" /> Comparativo por estado</div>
              <div class="barras">
                <div v-for="b in barras" :key="b.clave" class="barra-fila">
                  <div class="barra-meta"><span>{{ b.etiqueta }}</span><strong>{{ b.valor }}</strong></div>
                  <div class="barra-track"><div class="barra-fill" :style="{ width: `${b.ancho}%`, background: b.color }"></div></div>
                  <div class="barra-foot">{{ fmtPct(b.valor) }} del total</div>
                </div>
              </div>
            </div>
          </div>
        </article>

        <aside class="side-col">
          <article class="tarjeta">
            <div class="panel-head compact">
              <div>
                <div class="migas">Cumplimiento</div>
                <h2>Tasa de aprobación</h2>
              </div>
              <span class="badge-salud" :class="salud.clase">{{ salud.titulo }}</span>
            </div>
            <div class="gauge-wrap">
              <div class="gauge" role="img" aria-label="Porcentaje de aprobación global">
                <svg viewBox="0 0 140 140" class="donut-svg">
                  <circle cx="70" cy="70" :r="R" class="donut-track" />
                  <circle cx="70" cy="70" :r="R" class="gauge-ring" :stroke-dasharray="CIRC" :stroke-dashoffset="anilloAprobacion" transform="rotate(-90 70 70)" />
                </svg>
                <div class="donut-center">
                  <div class="gauge-value">{{ stats.porcentaje_aprobacion }}%</div>
                  <div class="donut-label">aprobadas / total</div>
                </div>
              </div>
              <div class="gauge-meta">
                <p>{{ salud.texto }}</p>
                <div class="metric-list">
                  <div><span><Target :size="14" /> En proceso</span><strong>{{ enProceso }} ({{ fmtPct(enProceso) }})</strong></div>
                  <div><span><TrendingUp :size="14" /> Prom. evidencias/aprendiz</span><strong>{{ promedioPorAprendiz }}</strong></div>
                  <div><span><Users :size="14" /> Cobertura instructores</span><strong>{{ stats.total_instructores }}</strong></div>
                </div>
              </div>
            </div>
          </article>

          <article class="tarjeta">
            <div class="panel-head compact">
              <div>
                <div class="migas">Indicadores operativos</div>
                <h2>Resumen de gestión</h2>
              </div>
            </div>
            <div class="insights">
              <div class="insight">
                <div class="insight-icon ok"><ShieldCheck :size="16" /></div>
                <div><div class="insight-label">Aprobación</div><div class="insight-value">{{ stats.porcentaje_aprobacion }}%</div><div class="insight-sub">{{ stats.aprobadas }} de {{ total }} evidencias</div></div>
              </div>
              <div class="insight">
                <div class="insight-icon warn"><Inbox :size="16" /></div>
                <div><div class="insight-label">En revisión</div><div class="insight-value">{{ fmtPct(enProceso) }}</div><div class="insight-sub">{{ enProceso }} pendientes o con ajuste</div></div>
              </div>
              <div class="insight">
                <div class="insight-icon alert"><AlertTriangle :size="16" /></div>
                <div><div class="insight-label">Alertas activas</div><div class="insight-value">{{ alertas.length }}</div><div class="insight-sub">{{ alertasVencidas }} vencidas · {{ alertasPorVencer }} por vencer</div></div>
              </div>
            </div>
          </article>
        </aside>
      </section>

      <section class="tarjeta mt-4">
        <div class="cabecera-fila separada">
          <div>
            <div class="migas">Seguimiento</div>
            <h2>Alertas de vencimiento</h2>
            <p class="panel-desc">Evidencias próximas a vencer o vencidas en todo el centro.</p>
          </div>
          <div class="alert-stats">
            <span class="pill danger">{{ alertasVencidas }} vencidas</span>
            <span class="pill warn">{{ alertasPorVencer }} por vencer</span>
          </div>
        </div>
        <AlertaLista :alertas="alertas" mostrar-aprendiz />
      </section>
    </template>
  </div>
</template>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 0; }
.hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.25rem; padding-bottom: 1rem; border-bottom: 1px solid var(--borde); }
.hero h1 { margin: 0.1rem 0 0.2rem; font-size: 1.6rem; }
.hero-sub { margin: 0; color: var(--texto-suave); font-size: 0.9rem; max-width: 720px; }
.hero-actions { justify-content: flex-end; }

.panel-grid { display: grid; grid-template-columns: minmax(0, 1.65fr) minmax(320px, 1fr); gap: 1rem; align-items: start; }
.side-col { display: grid; gap: 1rem; }
.panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; margin-bottom: 1rem; }
.panel-head.compact { margin-bottom: 0.75rem; }
.panel-head h2 { margin: 0.1rem 0 0.15rem; }
.panel-desc { margin: 0; color: var(--texto-suave); font-size: 0.85rem; }
.chip-total { display: inline-flex; flex-direction: column; align-items: flex-end; padding: 0.45rem 0.7rem; border: 1px solid var(--borde); border-radius: 10px; background: #f8fafc; min-width: 90px; }
.chip-total span { font-size: 0.68rem; text-transform: uppercase; letter-spacing: .08em; color: var(--texto-suave); }
.chip-total strong { font-family: var(--fuente-mono); font-size: 1.1rem; color: var(--texto); }

.stack-wrap { margin-bottom: 1rem; }
.stack-bar { height: 14px; width: 100%; display: flex; overflow: hidden; border-radius: 999px; background: #e2e8f0; border: 1px solid #e2e8f0; }
.stack-seg { height: 100%; min-width: 0; transition: width .5s ease; }
.stack-seg:not(:last-child) { box-shadow: inset -1px 0 0 rgba(255,255,255,.7); }
.stack-legend { display: flex; flex-wrap: wrap; gap: .9rem; margin-top: .5rem; color: var(--texto-suave); font-size: .78rem; }
.stack-legend span { display: inline-flex; align-items: center; gap: .35rem; }
.stack-legend i { width: 8px; height: 8px; border-radius: 999px; display: inline-block; }

.viz-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.donut-card, .bars-card { border: 1px solid #e2e8f0; border-radius: 12px; padding: .9rem; background: linear-gradient(180deg,#fff,#fbfcfe); }
.donut-wrap { position: relative; width: 170px; height: 170px; margin: 0 auto .5rem; }
.donut-svg { width: 100%; height: 100%; display: block; }
.donut-track { fill: none; stroke: #e2e8f0; stroke-width: 14; }
.donut-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.donut-total { font-family: var(--fuente-mono); font-size: 1.55rem; font-weight: 700; color: var(--texto); line-height: 1; }
.donut-label { font-size: .68rem; text-transform: uppercase; letter-spacing: .08em; color: var(--texto-suave); margin-top: 2px; }

.leyenda { list-style: none; margin: 0; padding: 0; display: grid; gap: .45rem; }
.leyenda li { display: grid; grid-template-columns: 10px 1fr auto auto; align-items: center; gap: .5rem; font-size: .84rem; }
.dot { width: 10px; height: 10px; border-radius: 999px; }
.leyenda-name { color: var(--texto); }
.leyenda-val { font-family: var(--fuente-mono); font-weight: 700; color: var(--texto); }
.leyenda-pct { font-family: var(--fuente-mono); font-size: .75rem; color: var(--texto-suave); min-width: 3.2rem; text-align: right; }

.subhead { display: inline-flex; align-items: center; gap: .4rem; font-size: .78rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; color: var(--texto-suave); margin-bottom: .7rem; }
.barras { display: grid; gap: .8rem; }
.barra-fila { display: grid; gap: .25rem; }
.barra-meta { display: flex; justify-content: space-between; gap: .5rem; font-size: .84rem; color: var(--texto); }
.barra-meta strong { font-family: var(--fuente-mono); }
.barra-track { height: 10px; background: #f1f5f9; border-radius: 999px; overflow: hidden; border: 1px solid #e2e8f0; }
.barra-fill { height: 100%; border-radius: 999px; transition: width .5s ease; }
.barra-foot { font-size: .72rem; color: var(--texto-suave); }

.gauge-wrap { display: grid; grid-template-columns: 170px 1fr; gap: .8rem; align-items: center; }
.gauge { position: relative; width: 170px; height: 170px; }
.gauge-ring { fill: none; stroke: #059669; stroke-width: 14; stroke-linecap: round; transition: stroke-dashoffset .6s ease; }
.gauge-value { font-family: var(--fuente-mono); font-size: 1.7rem; font-weight: 700; color: #047857; line-height: 1; }
.gauge-meta p { margin: 0 0 .6rem; font-size: .86rem; color: var(--texto-suave); }
.metric-list { display: grid; gap: .45rem; }
.metric-list div { display: flex; align-items: center; justify-content: space-between; gap: .6rem; padding: .45rem .55rem; border: 1px solid #e2e8f0; border-radius: 10px; background: #f8fafc; font-size: .8rem; }
.metric-list span { display: inline-flex; align-items: center; gap: .35rem; color: var(--texto-suave); }
.metric-list strong { font-family: var(--fuente-mono); color: var(--texto); font-size: .82rem; }

.badge-salud { display: inline-flex; align-items: center; padding: .25rem .55rem; border-radius: 999px; font-size: .72rem; font-weight: 700; border: 1px solid; white-space: nowrap; }
.badge-salud.ok { color:#047857; background:#ecfdf5; border-color:#a7f3d0; }
.badge-salud.medio { color:#b45309; background:#fffbeb; border-color:#fde68a; }
.badge-salud.critico { color:#be123c; background:#fff1f2; border-color:#fecdd3; }
.badge-salud.neutro { color:#475569; background:#f8fafc; border-color:#e2e8f0; }

.insights { display: grid; gap: .6rem; }
.insight { display: grid; grid-template-columns: 34px 1fr; gap: .6rem; align-items: start; padding: .55rem; border: 1px solid #e2e8f0; border-radius: 12px; background: #fff; }
.insight-icon { width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center; border: 1px solid; }
.insight-icon.ok { color:#059669; background:#ecfdf5; border-color:#a7f3d0; }
.insight-icon.warn { color:#d97706; background:#fffbeb; border-color:#fde68a; }
.insight-icon.alert { color:#e11d48; background:#fff1f2; border-color:#fecdd3; }
.insight-label { font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; color: var(--texto-suave); }
.insight-value { font-family: var(--fuente-mono); font-size: 1.05rem; font-weight: 700; color: var(--texto); line-height: 1.2; }
.insight-sub { font-size: .78rem; color: var(--texto-suave); }

.alert-stats { display: flex; gap: .4rem; flex-wrap: wrap; }
.pill { display: inline-flex; align-items: center; padding: .22rem .55rem; border-radius: 999px; font-size: .72rem; font-weight: 700; border: 1px solid; }
.pill.warn { color:#b45309; background:#fffbeb; border-color:#fde68a; }
.pill.danger { color:#be123c; background:#fff1f2; border-color:#fecdd3; }

.skeleton-card { height: 110px; background: linear-gradient(90deg,#f1f5f9,#e2e8f0,#f1f5f9); background-size: 200% 100%; animation: shimmer 1.2s infinite; }
.skeleton-panel { height: 360px; background: linear-gradient(90deg,#f1f5f9,#e2e8f0,#f1f5f9); background-size: 200% 100%; animation: shimmer 1.2s infinite; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

@media (max-width: 1100px) {
  .panel-grid { grid-template-columns: 1fr; }
}
@media (max-width: 860px) {
  .viz-grid, .gauge-wrap { grid-template-columns: 1fr; }
  .gauge { margin: 0 auto; }
  .hero-actions { justify-content: flex-start; }
}
</style>
