<script setup lang="ts">
// src/views/coordinador/EvidenciasView.vue
// EXPLICACIÓN: filtros de la API + paginación server-side (page/page_size)
import { onMounted, reactive, ref } from 'vue'
import { Download, FileDown, FileSearch, Filter, Sparkles } from 'lucide-vue-next'

import { api, descargar, ApiError } from '../../api/client'
import type { Evidencia, Pagina } from '../../api/types'
import vacioDocumentos from '../../assets/imagenes/vacio-documentos.svg'
import EstadoBadge from '../../components/EstadoBadge.vue'
import Esqueleto from '../../components/Esqueleto.vue'
import PaginacionBar from '../../components/PaginacionBar.vue'
import VacioEstado from '../../components/VacioEstado.vue'
import {
  btnPrimario,
  btnSecundario,
  btnSuave,
  etiquetaCampo,
  inputCampo,
  thTabla,
  trTabla,
} from '../../styles/ui-classes'

const filtros = reactive({
  estado: '',
  tipo_formato: '',
  fecha_desde: '',
  fecha_hasta: '',
})
const pagina = ref<Pagina<Evidencia> | null>(null)
const paginaActual = ref(1)
const cargando = ref(true)
const error = ref('')

function rutaActual(): string {
  const params = new URLSearchParams({ page: String(paginaActual.value), page_size: '10' })
  if (filtros.estado) params.set('estado', filtros.estado)
  if (filtros.tipo_formato) params.set('tipo_formato', filtros.tipo_formato)
  if (filtros.fecha_desde) params.set('fecha_desde', filtros.fecha_desde)
  if (filtros.fecha_hasta) params.set('fecha_hasta', filtros.fecha_hasta)
  return `/api/v1/coordinador/evidencias?${params.toString()}`
}

async function cargar(): Promise<void> {
  cargando.value = true
  try {
    pagina.value = await api<Pagina<Evidencia>>(rutaActual())
  } catch {
    error.value = 'No se pudieron cargar las evidencias.'
  } finally {
    cargando.value = false
  }
}

function aplicarFiltros(): void {
  paginaActual.value = 1
  void cargar()
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

async function exportarCsv(): Promise<void> {
  error.value = ''
  try {
    await descargar('/api/v1/coordinador/exportar-evidencias', 'evidencias_sgep.csv')
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail : 'No se pudo generar el CSV.'
  }
}

onMounted(cargar)
</script>

<template>
  <div class="min-h-full bg-slate-50 font-sans text-slate-900">
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
          <FileSearch :size="20" />
        </span>
        <div>
          <p class="m-0 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Coordinación · Documentos
          </p>
          <!-- EXPLICACIÓN: utilities > components (layers.css) => sin '!' -->
          <h1 class="text-2xl font-bold m-0 text-slate-900">Evidencias</h1>
          <p class="m-0 mt-2 text-sm text-slate-500">
            Documentos cargados por los aprendices y su estado de revisión.
          </p>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <span
          class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600 shadow-sm"
        >
          <Sparkles :size="13" class="text-emerald-600" aria-hidden="true" />
          {{ pagina?.total ?? 0 }} registros
        </span>
        <button :class="btnSuave" type="button" @click="exportarCsv">
          <Download :size="15" />
          Exportar CSV
        </button>
      </div>
    </header>

    <section class="mb-5 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-[repeat(4,minmax(0,1fr))_auto]">
        <div>
          <label for="estado" :class="etiquetaCampo">Estado</label>
          <select id="estado" v-model="filtros.estado" :class="inputCampo">
            <option value="">Todos</option>
            <option>Pendiente</option>
            <option>Aprobada</option>
            <option>Ajuste Requerido</option>
          </select>
        </div>
        <div>
          <label for="tipo" :class="etiquetaCampo">Tipo de formato</label>
          <input
            id="tipo"
            v-model.trim="filtros.tipo_formato"
            type="text"
            placeholder="Bitacora, F023…"
            :class="inputCampo"
          />
        </div>
        <div>
          <label for="desde" :class="etiquetaCampo">Cargada desde</label>
          <input id="desde" v-model="filtros.fecha_desde" type="date" :class="inputCampo" />
        </div>
        <div>
          <label for="hasta" :class="etiquetaCampo">Cargada hasta</label>
          <input id="hasta" v-model="filtros.fecha_hasta" type="date" :class="inputCampo" />
        </div>
        <div class="flex items-end">
          <button :class="btnPrimario" type="button" @click="aplicarFiltros">
            <Filter :size="15" />
            Aplicar filtros
          </button>
        </div>
      </div>
    </section>

    <section class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <Esqueleto v-if="cargando" :filas="5" />
      <VacioEstado
        v-else-if="!pagina || pagina.items.length === 0"
        :icono="FileSearch"
        :ilustracion="vacioDocumentos"
        titulo="Sin resultados"
        texto="Ninguna evidencia coincide con los filtros aplicados."
      />

      <template v-else>
        <div class="overflow-x-auto">
          <table class="w-full min-w-[720px] border-collapse text-left text-sm">
            <thead>
              <tr>
                <th :class="thTabla">Título</th>
                <th :class="thTabla">Tipo</th>
                <th :class="thTabla">Estado</th>
                <th :class="thTabla">Cargada</th>
                <th :class="thTabla">Límite</th>
                <th :class="[thTabla, 'text-right']">Acción</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="e in pagina.items" :key="e.id_evidencia" :class="trTabla">
                <td class="px-4 py-3 font-medium text-slate-900">{{ e.titulo }}</td>
                <td class="px-4 py-3 text-slate-600">{{ e.tipo_formato }}</td>
                <td class="px-4 py-3">
                  <EstadoBadge :estado="e.estado" />
                </td>
                <td class="px-4 py-3 tabular-nums text-slate-600">
                  {{ e.fecha_carga.slice(0, 10) }}
                </td>
                <td class="px-4 py-3 tabular-nums text-slate-600">
                  {{ e.fecha_deadline ? e.fecha_deadline.slice(0, 10) : '—' }}
                </td>
                <td class="whitespace-nowrap px-4 py-3 text-right">
                  <button
                    :class="btnSecundario"
                    type="button"
                    :aria-label="`Descargar ${e.titulo}`"
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
