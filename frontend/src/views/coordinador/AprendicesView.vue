<script setup lang="ts">
// src/views/coordinador/AprendicesView.vue
// EXPLICACIÓN: avance por aprendiz con paginación server-side + reporte RF07 (CSV)
import { onMounted, ref } from 'vue'
import { Download, Search, Users, X } from 'lucide-vue-next'

import { api, descargar, ApiError } from '../../api/client'
import type { AvanceAprendiz, Pagina } from '../../api/types'
import vacioDocumentos from '../../assets/imagenes/vacio-documentos.svg'
import AvatarNombre from '../../components/AvatarNombre.vue'
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

const pagina = ref<Pagina<AvanceAprendiz> | null>(null)
const paginaActual = ref(1)
const programa = ref('')
const cargando = ref(true)
const error = ref('')
const exportando = ref(false)

async function cargar(): Promise<void> {
  cargando.value = true
  try {
    const params = new URLSearchParams({ page: String(paginaActual.value), page_size: '10' })
    if (programa.value) params.set('programa', programa.value)
    pagina.value = await api<Pagina<AvanceAprendiz>>(
      `/api/v1/coordinador/aprendices?${params.toString()}`,
    )
  } catch {
    error.value = 'No se pudo cargar la lista de aprendices.'
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

function aplicarFiltro(): void {
  // EXPLICACIÓN: un filtro nuevo invalida la página actual (evita páginas vacías)
  paginaActual.value = 1
  void cargar()
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
          <Users :size="20" />
        </span>
        <div>
          <p class="m-0 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Coordinación · Reportes
          </p>
          <!-- EXPLICACIÓN: utilities > components (layers.css) => sin '!' -->
          <h1 class="text-2xl font-bold m-0 text-slate-900">Aprendices y avance</h1>
          <p class="m-0 mt-2 text-sm text-slate-500">
            Avance de evidencias por aprendiz y reporte RF07.
          </p>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <span
          class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600 shadow-sm"
        >
          <Users :size="13" class="text-emerald-600" aria-hidden="true" />
          {{ pagina?.total ?? 0 }} aprendices
        </span>
        <button :class="btnSuave" type="button" :disabled="exportando" @click="exportarAvance">
          <Download :size="15" />
          {{ exportando ? 'Generando…' : 'Exportar avance (RF07)' }}
        </button>
      </div>
    </header>

    <section class="mb-5 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <form class="flex flex-wrap items-end gap-3" @submit.prevent="aplicarFiltro">
        <div class="min-w-[220px] flex-1">
          <label for="programa" :class="etiquetaCampo">Filtrar por programa</label>
          <input
            id="programa"
            v-model.trim="programa"
            type="text"
            placeholder="ADSO…"
            :class="inputCampo"
          />
        </div>
        <button :class="btnPrimario" type="submit">
          <Search :size="15" />
          Buscar
        </button>
        <button
          v-if="programa"
          :class="btnSecundario"
          type="button"
          @click="programa = ''; aplicarFiltro()"
        >
          <X :size="15" />
          Limpiar
        </button>
      </form>
    </section>

    <section class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <Esqueleto v-if="cargando" :filas="5" />
      <VacioEstado
        v-else-if="!pagina || pagina.items.length === 0"
        :icono="Users"
        :ilustracion="vacioDocumentos"
        titulo="Sin aprendices"
        texto="No hay aprendices registrados o el filtro no coincide."
      />

      <template v-else>
        <div class="overflow-x-auto">
          <table class="w-full min-w-[760px] border-collapse text-left text-sm">
            <thead>
              <tr>
                <th :class="thTabla">Nombre</th>
                <th :class="thTabla">Ficha</th>
                <th :class="thTabla">Programa</th>
                <th :class="thTabla">Evidencias</th>
                <th :class="thTabla">Aprobadas</th>
                <th :class="thTabla">Avance</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="a in pagina.items" :key="a.id_usuario" :class="trTabla">
                <td class="px-4 py-3">
                  <AvatarNombre :nombre="a.nombre_completo" />
                </td>
                <td class="px-4 py-3 tabular-nums text-slate-600">{{ a.numero_ficha }}</td>
                <td class="px-4 py-3 text-slate-600">{{ a.programa }}</td>
                <td class="px-4 py-3 tabular-nums text-slate-600">{{ a.total_evidencias }}</td>
                <td class="px-4 py-3 tabular-nums text-slate-600">{{ a.aprobadas }}</td>
                <td class="min-w-[160px] px-4 py-3">
                  <div class="barra-progreso">
                    <div :style="{ width: `${a.porcentaje_avance}%` }" />
                  </div>
                  <small class="dato">{{ a.porcentaje_avance }} %</small>
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
