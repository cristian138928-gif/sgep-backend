<script setup lang="ts">
// src/views/coordinador/BitacorasView.vue
// EXPLICACIÓN: panel claro autocontenido (UI_GUIDELINES.md) dentro del shell oscuro
import { onMounted, reactive, ref } from 'vue'
import { BookOpen, FileDown, FileSearch, Filter, Sparkles } from 'lucide-vue-next'

import { api, descargar } from '../../api/client'
import type { Evidencia, Pagina } from '../../api/types'
// EXPLICACIÓN: un solo módulo de clases => esta vista y el resto comparten botones
import { btnPrimario, btnSecundario, thTabla, trTabla } from '../../styles/ui-classes'
import Esqueleto from '../../components/Esqueleto.vue'
import EstadoBadge from '../../components/EstadoBadge.vue'
import PaginacionBar from '../../components/PaginacionBar.vue'
import VacioEstado from '../../components/VacioEstado.vue'

const filtros = reactive({
  estado: '',
  fecha_desde: '',
  fecha_hasta: '',
})
const pagina = ref<Pagina<Evidencia> | null>(null)
const paginaActual = ref(1)
const cargando = ref(true)
const error = ref('')

// EXPLICACIÓN: el tipo va FIJO en la query: esta vista solo lista bitácoras
function rutaActual(): string {
  const params = new URLSearchParams({
    tipo_formato: 'Bitacora',
    page: String(paginaActual.value),
    page_size: '10',
  })
  if (filtros.estado) params.set('estado', filtros.estado)
  if (filtros.fecha_desde) params.set('fecha_desde', filtros.fecha_desde)
  if (filtros.fecha_hasta) params.set('fecha_hasta', filtros.fecha_hasta)
  return `/api/v1/coordinador/evidencias?${params.toString()}`
}

async function cargar(): Promise<void> {
  cargando.value = true
  error.value = ''
  try {
    pagina.value = await api<Pagina<Evidencia>>(rutaActual())
  } catch {
    error.value = 'No se pudieron cargar las bitácoras.'
  } finally {
    cargando.value = false
  }
}

function aplicarFiltros(): void {
  paginaActual.value = 1
  void cargar()
}

function limpiarFiltros(): void {
  filtros.estado = ''
  filtros.fecha_desde = ''
  filtros.fecha_hasta = ''
  aplicarFiltros()
}

function cambiarPagina(delta: number): void {
  const total = pagina.value?.total_pages ?? 1
  const destino = paginaActual.value + delta
  if (destino >= 1 && destino <= total) {
    paginaActual.value = destino
    void cargar()
  }
}

async function descargarPdf(e: Evidencia): Promise<void> {
  error.value = ''
  try {
    await descargar(`/api/v1/evidencias/${e.id_evidencia}/descarga`, `${e.titulo}.pdf`)
  } catch {
    error.value = 'No se pudo descargar el PDF.'
  }
}

function fechaCorta(iso: string | null): string {
  return iso ? iso.slice(0, 10) : '—'
}

onMounted(cargar)
</script>

<template>
  <div class="min-h-full rounded-xl border border-slate-200 bg-slate-50 p-5 font-sans text-slate-900 sm:p-7">
    <div
      v-if="error"
      role="alert"
      class="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm font-medium text-rose-700"
    >
      {{ error }}
    </div>

    <header class="mb-5 flex flex-wrap items-end justify-between gap-3 border-b border-slate-200 pb-4">
      <div class="flex items-center gap-3">
        <span
          class="flex h-10 w-10 flex-none items-center justify-center rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700"
          aria-hidden="true"
        >
          <BookOpen :size="20" />
        </span>
        <div>
          <p class="m-0 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Coordinación · Documentos
          </p>
          <!-- EXPLICACIÓN: utilities > components (layers.css) => sin '!' -->
          <h1 class="text-2xl font-bold m-0 text-slate-900">Bitácoras</h1>
          <p class="m-0 mt-2 text-sm text-slate-500">
            Bitácoras cargadas por los aprendices y su estado de revisión.
          </p>
        </div>
      </div>
      <span
        class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600 shadow-sm"
      >
        <Sparkles :size="13" class="text-emerald-600" aria-hidden="true" />
        {{ pagina?.total ?? 0 }} registros
      </span>
    </header>

    <section class="mb-5 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-[repeat(3,minmax(0,1fr))_auto]">
        <div>
          <span class="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Tipo de formato
          </span>
          <span
            class="inline-flex items-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700"
          >
            Bitácora <span class="font-normal text-emerald-600/70">(fijo)</span>
          </span>
        </div>
        <div>
          <label for="estado" class="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Estado
          </label>
          <select
            id="estado"
            v-model="filtros.estado"
            class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-sans text-sm text-slate-900 shadow-sm transition-colors outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20"
          >
            <option value="">Todos</option>
            <option>Pendiente</option>
            <option>Aprobada</option>
            <option>Ajuste Requerido</option>
          </select>
        </div>
        <div>
          <label for="desde" class="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Cargada desde
          </label>
          <input
            id="desde"
            v-model="filtros.fecha_desde"
            type="date"
            class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-sans text-sm text-slate-900 shadow-sm transition-colors outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20"
          />
        </div>
        <div>
          <label for="hasta" class="mb-2 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Cargada hasta
          </label>
          <input
            id="hasta"
            v-model="filtros.fecha_hasta"
            type="date"
            class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-sans text-sm text-slate-900 shadow-sm transition-colors outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20"
          />
        </div>
      </div>
      <div class="mt-4 flex flex-wrap gap-2">
        <button :class="btnPrimario" type="button" @click="aplicarFiltros">
          <Filter :size="15" />
          Aplicar filtros
        </button>
        <button :class="btnSecundario" type="button" @click="limpiarFiltros">Limpiar</button>
      </div>
    </section>

    <section class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <Esqueleto v-if="cargando" :filas="5" />
      <VacioEstado
        v-else-if="!pagina || pagina.items.length === 0"
        :icono="FileSearch"
        titulo="Sin bitácoras registradas"
        texto="Ninguna bitácora coincide con los filtros aplicados."
      />

      <template v-else>
        <div class="overflow-x-auto">
          <table class="w-full min-w-[640px] border-collapse text-left text-sm">
            <thead>
              <tr>
                <th :class="thTabla">Título</th>
                <th :class="thTabla">Estado</th>
                <th :class="thTabla">Cargada</th>
                <th :class="thTabla">Límite</th>
                <th :class="[thTabla, 'text-right']">Archivo</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="e in pagina.items"
                :key="e.id_evidencia"
                :class="trTabla"
              >
                <td class="px-4 py-3">
                  <span class="block font-medium text-slate-900">{{ e.titulo }}</span>
                  <span class="mt-0.5 block text-xs text-slate-500">
                    Registro #{{ e.id_evidencia }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <EstadoBadge :estado="e.estado" />
                </td>
                <td class="px-4 py-3 tabular-nums text-slate-600">
                  {{ fechaCorta(e.fecha_carga) }}
                </td>
                <td class="px-4 py-3 tabular-nums text-slate-600">
                  {{ fechaCorta(e.fecha_deadline) }}
                </td>
                <td class="px-4 py-3 text-right">
                  <button
                    :class="btnSecundario"
                    type="button"
                    :aria-label="`Descargar bitácora ${e.titulo}`"
                    @click="descargarPdf(e)"
                  >
                    <FileDown :size="15" />
                    PDF
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <PaginacionBar
          :pagina="pagina.page"
          :total-paginas="pagina.total_pages"
          :pagina-actual="paginaActual"
          @cambiar="cambiarPagina"
        />
      </template>
    </section>
  </div>
</template>
