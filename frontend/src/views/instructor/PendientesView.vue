<script setup lang="ts">
// src/views/instructor/PendientesView.vue
import { computed, onMounted, ref } from 'vue'
import { Bell, ClipboardCheck, Inbox, ListChecks, TrendingUp } from 'lucide-vue-next'

import { api } from '../../api/client'
import type { AlertaRol, EstadisticasInstructor, Evidencia, Pagina } from '../../api/types'
import vacioBandeja from '../../assets/imagenes/vacio-bandeja.svg'
import AlertaLista from '../../components/AlertaLista.vue'
import Esqueleto from '../../components/Esqueleto.vue'
import EstadoBadge from '../../components/EstadoBadge.vue'
import KpiTarjeta from '../../components/KpiTarjeta.vue'
import PaginacionBar from '../../components/PaginacionBar.vue'
import VacioEstado from '../../components/VacioEstado.vue'

const pagina = ref<Pagina<Evidencia> | null>(null)
const estadisticas = ref<EstadisticasInstructor | null>(null)
const alertas = ref<AlertaRol[]>([])
const paginaActual = ref(1)
const cargando = ref(true)
const error = ref('')

const totalEvaluadas = computed(() =>
  estadisticas.value ? estadisticas.value.aprobadas + estadisticas.value.ajustes_requeridos : 0,
)

async function cargar(): Promise<void> {
  cargando.value = true
  try {
    const [p, e, a] = await Promise.all([
      api<Pagina<Evidencia>>(`/api/v1/instructor/evidencias-pendientes?page=${paginaActual.value}&page_size=10`),
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

function fecha(iso: string | null): string {
  return iso ? iso.slice(0, 10) : '—'
}

onMounted(cargar)
</script>

<template>
  <div>
    <header class="hero">
      <div>
        <div class="migas">Instructor · Bandeja de evaluación</div>
        <h1>Pendientes por evaluar</h1>
        <p class="hero-sub">Gestiona las evidencias asignadas, prioriza revisiones y atiende alertas de vencimiento.</p>
      </div>
      <div class="hero-chip" v-if="estadisticas">
        <TrendingUp :size="14" />
        {{ totalEvaluadas }} evaluadas · {{ estadisticas.pendientes_por_evaluar }} en cola
      </div>
    </header>

    <div v-if="error" class="alerta-error" role="alert">{{ error }}</div>

    <section v-if="estadisticas" class="rejilla rejilla-3">
      <KpiTarjeta etiqueta="Por evaluar" :valor="estadisticas.pendientes_por_evaluar" :icono="Inbox" tono="cian" />
      <KpiTarjeta etiqueta="Aprobadas" :valor="estadisticas.aprobadas" :icono="ClipboardCheck" tono="verde" />
      <KpiTarjeta etiqueta="Ajustes requeridos" :valor="estadisticas.ajustes_requeridos" :icono="ListChecks" tono="ambar" />
    </section>

    <section class="tarjeta mt-4">
      <div class="cabecera-fila separada">
        <div>
          <div class="migas">Cola de trabajo</div>
          <h2 class="m-0">Evidencias por evaluar</h2>
        </div>
        <span v-if="pagina" class="pill-count">{{ pagina.total }} registros</span>
      </div>

      <Esqueleto v-if="cargando" :filas="5" />
      <VacioEstado
        v-else-if="!pagina || pagina.items.length === 0"
        :icono="ClipboardCheck"
        :ilustracion="vacioBandeja"
        titulo="Todo al día"
        texto="No hay evidencias pendientes de evaluación en este momento."
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
                <th>Fecha límite</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in pagina.items" :key="e.id_evidencia">
                <td class="font-medium">{{ e.titulo }}</td>
                <td>{{ e.tipo_formato }}</td>
                <td><EstadoBadge :estado="e.estado" /></td>
                <td class="mono">{{ fecha(e.fecha_carga) }}</td>
                <td class="mono">{{ fecha(e.fecha_deadline) }}</td>
                <td class="der">
                  <router-link
                    class="btn btn-primario"
                    :to="{ name: 'evaluar', params: { id: e.id_evidencia }, state: { evidencia: e } }"
                  >
                    <ClipboardCheck :size="15" />
                    Evaluar
                  </router-link>
                </td>
              </tr>
            </tbody>
          </table>
          <PaginacionBar :pagina="pagina.page" :total-paginas="pagina.total_pages" :pagina-actual="paginaActual" @cambiar="cambiarPagina" />
        </div>
      </template>
    </section>

    <section class="tarjeta mt-4">
      <div class="cabecera-fila separada">
        <div>
          <div class="migas">Seguimiento</div>
          <h2 class="m-0"><Bell :size="16" class="ico-aviso" /> Alertas de vencimiento</h2>
          <p class="texto-suave sin-margen">Aprendices asignados con evidencias próximas a vencer o vencidas.</p>
        </div>
        <span class="pill-count warn">{{ alertas.length }} alertas</span>
      </div>
      <AlertaLista :alertas="alertas" mostrar-aprendiz />
    </section>
  </div>
</template>

<style scoped>
.hero { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; flex-wrap:wrap; margin-bottom:1.25rem; padding-bottom:1rem; border-bottom:1px solid var(--borde); }
.hero h1 { margin:.1rem 0 .2rem; font-size:1.55rem; }
.hero-sub { margin:0; color:var(--texto-suave); font-size:.9rem; max-width:720px; }
.hero-chip { display:inline-flex; align-items:center; gap:.4rem; padding:.4rem .7rem; border-radius:999px; border:1px solid #bfdbfe; background:#eff6ff; color:#1d4ed8; font-size:.78rem; font-weight:700; }
.pill-count { display:inline-flex; align-items:center; padding:.25rem .6rem; border-radius:999px; border:1px solid var(--borde); background:#f8fafc; color:var(--texto-suave); font-size:.75rem; font-weight:700; }
.pill-count.warn { color:#b45309; background:#fffbeb; border-color:#fde68a; }
.font-medium { font-weight: 600; color: var(--texto); }
</style>
