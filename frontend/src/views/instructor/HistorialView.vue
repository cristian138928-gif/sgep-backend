<script setup lang="ts">
// src/views/instructor/HistorialView.vue
import { onMounted, ref } from 'vue'
import { CalendarDays, History } from 'lucide-vue-next'

import { api } from '../../api/client'
import type { EstadoEvidencia, Pagina, Retroalimentacion } from '../../api/types'
import vacioBandeja from '../../assets/imagenes/vacio-bandeja.svg'
import Esqueleto from '../../components/Esqueleto.vue'
import EstadoBadge from '../../components/EstadoBadge.vue'
import PaginacionBar from '../../components/PaginacionBar.vue'
import VacioEstado from '../../components/VacioEstado.vue'

const pagina = ref<Pagina<Retroalimentacion> | null>(null)
const paginaActual = ref(1)
const cargando = ref(true)
const error = ref('')

async function cargar(): Promise<void> {
  cargando.value = true
  try {
    pagina.value = await api<Pagina<Retroalimentacion>>(
      `/api/v1/instructor/historial?page=${paginaActual.value}&page_size=10`,
    )
  } catch {
    error.value = 'No se pudo cargar el historial.'
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

function fechaCorta(iso: string): string {
  return new Date(iso).toLocaleDateString('es-CO', { dateStyle: 'medium' })
}

onMounted(cargar)
</script>

<template>
  <div>
    <header class="hero">
      <div>
        <div class="migas">Instructor · Seguimiento</div>
        <h1>Historial de evaluaciones</h1>
        <p class="hero-sub">Registro de decisiones y retroalimentaciones emitidas sobre evidencias.</p>
      </div>
      <div class="hero-chip" v-if="pagina"><CalendarDays :size="14" /> {{ pagina.total }} evaluaciones</div>
    </header>

    <div v-if="error" class="alerta-error" role="alert">{{ error }}</div>

    <section class="tarjeta tarjeta-flush">
      <Esqueleto v-if="cargando" :filas="5" />
      <VacioEstado
        v-else-if="!pagina || pagina.items.length === 0"
        :icono="History"
        :ilustracion="vacioBandeja"
        titulo="Sin evaluaciones registradas"
        texto="Las evaluaciones que registres aparecerán aquí."
      />

      <template v-else>
        <div class="tabla-contenedor tabla-plana">
          <table class="tabla">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Evidencia</th>
                <th>Resultado</th>
                <th>Observaciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in pagina.items" :key="r.id_retroalimentacion">
                <td class="mono">{{ fechaCorta(r.fecha_revision) }}</td>
                <td class="mono">#{{ r.id_evidencia }}</td>
                <td><EstadoBadge :estado="r.estado_evaluacion as EstadoEvidencia" /></td>
                <td class="texto-suave obs">{{ r.observaciones }}</td>
              </tr>
            </tbody>
          </table>
          <PaginacionBar :pagina="pagina.page" :total-paginas="pagina.total_pages" :pagina-actual="paginaActual" @cambiar="cambiarPagina" />
        </div>
      </template>
    </section>
  </div>
</template>

<style scoped>
.hero { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; flex-wrap:wrap; margin-bottom:1.25rem; padding-bottom:1rem; border-bottom:1px solid var(--borde); }
.hero h1 { margin:.1rem 0 .2rem; font-size:1.55rem; }
.hero-sub { margin:0; color:var(--texto-suave); font-size:.9rem; }
.hero-chip { display:inline-flex; align-items:center; gap:.4rem; padding:.4rem .7rem; border-radius:999px; border:1px solid var(--borde); background:#f8fafc; color:var(--texto-suave); font-size:.78rem; font-weight:700; }
.obs { max-width: 520px; line-height: 1.45; }
</style>
