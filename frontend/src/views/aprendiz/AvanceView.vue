<script setup lang="ts">
// src/views/aprendiz/AvanceView.vue
import { computed, onMounted, ref } from 'vue'
import { Bell, CheckCircle2, Clock3, FileText, Gauge, Target } from 'lucide-vue-next'

import { api } from '../../api/client'
import type { Alerta, AvanceAprendiz } from '../../api/types'
import AlertaLista from '../../components/AlertaLista.vue'
import KpiTarjeta from '../../components/KpiTarjeta.vue'

const avance = ref<AvanceAprendiz | null>(null)
const alertas = ref<Alerta[]>([])
const ventana = ref(7)
const cargando = ref(true)
const error = ref('')

const R = 64
const CIRC = 2 * Math.PI * R

const porcentaje = computed(() => avance.value?.porcentaje_avance ?? 0)
const anilloOffset = computed(() => CIRC * (1 - porcentaje.value / 100))
const pendientes = computed(() =>
  avance.value ? Math.max(avance.value.total_evidencias - avance.value.aprobadas, 0) : 0,
)

const estadoProgreso = computed(() => {
  const p = porcentaje.value
  if (p >= 80) return { texto: 'Excelente avance', clase: 'ok', detalle: 'Vas muy cerca de completar tu etapa práctica.' }
  if (p >= 50) return { texto: 'Avance estable', clase: 'medio', detalle: 'Buen ritmo, mantén la constancia en tus entregas.' }
  if (avance.value && avance.value.total_evidencias === 0) return { texto: 'Sin evidencias', clase: 'neutro', detalle: 'Aún no has registrado evidencias.' }
  return { texto: 'Requiere impulso', clase: 'alerta', detalle: 'Prioriza cargar y ajustar evidencias pendientes.' }
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
  } finally {
    cargando.value = false
  }
})
</script>

<template>
  <div class="avance-view">
    <header class="hero">
      <div>
        <div class="migas">Aprendiz · Etapa práctica</div>
        <h1>Mi avance</h1>
        <p class="hero-sub">Seguimiento de tus evidencias, aprobación y alertas de vencimiento.</p>
      </div>
      <div class="hero-pill" v-if="avance">
        <Target :size="15" />
        {{ estadoProgreso.texto }}
      </div>
    </header>

    <div v-if="error" class="alerta-error" role="alert">{{ error }}</div>

    <div v-if="cargando" class="rejilla rejilla-2">
      <div class="tarjeta sk"></div>
      <div class="tarjeta sk"></div>
    </div>

    <template v-else-if="avance">
      <section class="rejilla avance-grid">
        <article class="tarjeta progreso-card">
          <div class="cabecera-fila separada">
            <div>
              <div class="migas">Progreso general</div>
              <h2 class="m-0">{{ avance.nombre_completo }}</h2>
              <p class="texto-suave sin-margen">Ficha {{ avance.numero_ficha }} · {{ avance.programa }}</p>
            </div>
            <span class="badge-estado" :class="estadoProgreso.clase">{{ estadoProgreso.texto }}</span>
          </div>

          <div class="progreso-wrap">
            <div class="gauge" role="img" aria-label="Porcentaje de avance">
              <svg viewBox="0 0 160 160" class="gauge-svg">
                <defs>
                  <linearGradient id="gradAvance" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#10b981" />
                    <stop offset="100%" stop-color="#059669" />
                  </linearGradient>
                </defs>
                <circle cx="80" cy="80" :r="R" class="track" />
                <circle cx="80" cy="80" :r="R" class="progress" :stroke-dasharray="CIRC" :stroke-dashoffset="anilloOffset" transform="rotate(-90 80 80)" />
              </svg>
              <div class="gauge-center">
                <div class="gauge-value">{{ porcentaje }}%</div>
                <div class="gauge-label">completado</div>
              </div>
            </div>
            <div class="progreso-meta">
              <p class="detalle">{{ estadoProgreso.detalle }}</p>
              <div class="mini-stats">
                <div class="mini"><FileText :size="15" /><span>Total</span><strong>{{ avance.total_evidencias }}</strong></div>
                <div class="mini ok"><CheckCircle2 :size="15" /><span>Aprobadas</span><strong>{{ avance.aprobadas }}</strong></div>
                <div class="mini warn"><Clock3 :size="15" /><span>Pendientes/ajuste</span><strong>{{ pendientes }}</strong></div>
              </div>
              <div class="barra-progreso"><div :style="{ width: `${porcentaje}%` }" /></div>
            </div>
          </div>
        </article>

        <aside class="tarjeta resumen-card">
          <div class="migas">Resumen</div>
          <h2>Indicadores clave</h2>
          <div class="resumen-list">
            <div class="resumen-row"><span>Tasa de aprobación</span><strong>{{ porcentaje }}%</strong></div>
            <div class="resumen-row"><span>Evidencias aprobadas</span><strong>{{ avance.aprobadas }} / {{ avance.total_evidencias }}</strong></div>
            <div class="resumen-row"><span>En gestión</span><strong>{{ pendientes }}</strong></div>
            <div class="resumen-row"><span>Alertas ({{ ventana }} días)</span><strong>{{ alertas.length }}</strong></div>
          </div>
          <div class="nota"><Gauge :size="14" /> Datos calculados a partir de tus evidencias registradas.</div>
        </aside>
      </section>

      <section class="rejilla rejilla-3 mt-4">
        <KpiTarjeta etiqueta="Evidencias totales" :valor="avance.total_evidencias" :icono="FileText" tono="azul" />
        <KpiTarjeta etiqueta="Aprobadas" :valor="avance.aprobadas" :icono="CheckCircle2" tono="verde" />
        <KpiTarjeta etiqueta="Pendientes / Ajuste" :valor="pendientes" :icono="Clock3" tono="ambar" />
      </section>

      <section class="tarjeta mt-4">
        <div class="cabecera-fila separada">
          <div>
            <div class="migas">Seguimiento</div>
            <h2 class="m-0"><Bell :size="16" class="ico-aviso" /> Alertas de vencimiento</h2>
          </div>
          <label class="filtro-inline">
            <span>Ventana</span>
            <select v-model.number="ventana" class="btn" aria-label="Ventana de alertas" @change="cargarAlertas">
              <option :value="7">7 días</option>
              <option :value="14">14 días</option>
              <option :value="30">30 días</option>
            </select>
          </label>
        </div>
        <AlertaLista :alertas="alertas" />
      </section>
    </template>
  </div>
</template>

<style scoped>
.avance-view { display: grid; gap: 0; }
.hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.25rem; padding-bottom: 1rem; border-bottom: 1px solid var(--borde); }
.hero h1 { margin: .1rem 0 .2rem; font-size: 1.55rem; }
.hero-sub { margin: 0; color: var(--texto-suave); font-size: .9rem; }
.hero-pill { display: inline-flex; align-items: center; gap: .4rem; padding: .4rem .7rem; border-radius: 999px; border: 1px solid #a7f3d0; background: #ecfdf5; color: #047857; font-size: .78rem; font-weight: 700; }
.avance-grid { grid-template-columns: minmax(0,1.5fr) minmax(280px,1fr); gap: 1rem; }
.progreso-wrap { display: grid; grid-template-columns: 180px 1fr; gap: 1rem; align-items: center; }
.gauge { position: relative; width: 180px; height: 180px; margin: 0 auto; }
.gauge-svg { width: 100%; height: 100%; display: block; }
.track { fill: none; stroke: #e2e8f0; stroke-width: 14; }
.progress { fill: none; stroke: url(#gradAvance); stroke-width: 14; stroke-linecap: round; transition: stroke-dashoffset .6s ease; }
.gauge-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.gauge-value { font-family: var(--fuente-mono); font-size: 1.8rem; font-weight: 700; color: #047857; line-height: 1; }
.gauge-label { font-size: .7rem; text-transform: uppercase; letter-spacing: .08em; color: var(--texto-suave); margin-top: 2px; }
.detalle { margin: 0 0 .7rem; color: var(--texto-suave); font-size: .9rem; }
.mini-stats { display: grid; gap: .45rem; margin-bottom: .7rem; }
.mini { display: grid; grid-template-columns: 18px 1fr auto; align-items: center; gap: .45rem; padding: .45rem .55rem; border: 1px solid #e2e8f0; border-radius: 10px; background: #f8fafc; font-size: .84rem; color: var(--texto-suave); }
.mini strong { font-family: var(--fuente-mono); color: var(--texto); }
.mini.ok { color: #047857; }
.mini.warn { color: #b45309; }
.resumen-list { display: grid; gap: .5rem; margin-top: .5rem; }
.resumen-row { display: flex; justify-content: space-between; gap: .8rem; padding: .55rem .65rem; border: 1px solid #e2e8f0; border-radius: 10px; background: #fff; font-size: .86rem; color: var(--texto-suave); }
.resumen-row strong { font-family: var(--fuente-mono); color: var(--texto); }
.nota { margin-top: .8rem; display: inline-flex; align-items: center; gap: .4rem; font-size: .78rem; color: var(--texto-suave); }
.badge-estado { display: inline-flex; padding: .25rem .55rem; border-radius: 999px; font-size: .72rem; font-weight: 700; border: 1px solid; }
.badge-estado.ok { color:#047857; background:#ecfdf5; border-color:#a7f3d0; }
.badge-estado.medio { color:#b45309; background:#fffbeb; border-color:#fde68a; }
.badge-estado.alerta { color:#be123c; background:#fff1f2; border-color:#fecdd3; }
.badge-estado.neutro { color:#475569; background:#f8fafc; border-color:#e2e8f0; }
.filtro-inline { display: inline-flex; align-items: center; gap: .5rem; font-size: .82rem; color: var(--texto-suave); }
.sk { height: 280px; background: linear-gradient(90deg,#f1f5f9,#e2e8f0,#f1f5f9); background-size: 200% 100%; animation: shimmer 1.2s infinite; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
@media (max-width: 900px) { .avance-grid, .progreso-wrap { grid-template-columns: 1fr; } .gauge { width: 170px; height: 170px; } }
</style>
