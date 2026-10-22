<script setup lang="ts">
// src/views/coordinador/EvidenciasView.vue
// EXPLICACIÓN: filtros de la API + paginación server-side (page/page_size)
import { onMounted, reactive, ref } from 'vue'
import { Download, FileDown, FileSearch, Filter } from 'lucide-vue-next'

import { api, descargar, ApiError } from '../../api/client'
import type { Evidencia, Pagina } from '../../api/types'
import EstadoBadge from '../../components/EstadoBadge.vue'
import PaginacionBar from '../../components/PaginacionBar.vue'
import VacioEstado from '../../components/VacioEstado.vue'

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
  <div>
    <div class="encabezado">
      <div>
        <div class="migas">Coordinación · Documentos</div>
        <h1>Evidencias</h1>
      </div>
      <div class="acciones">
        <button class="btn btn-suave" type="button" @click="exportarCsv">
          <Download :size="15" />
          Exportar CSV
        </button>
      </div>
    </div>

    <div v-if="error" class="alerta-error">{{ error }}</div>

    <div class="tarjeta">
      <div class="rejilla rejilla-estrecha">
        <div class="campo">
          <label for="estado">Estado</label>
          <select id="estado" v-model="filtros.estado">
            <option value="">Todos</option>
            <option>Pendiente</option>
            <option>Aprobada</option>
            <option>Ajuste Requerido</option>
          </select>
        </div>
        <div class="campo">
          <label for="tipo">Tipo de formato</label>
          <input id="tipo" v-model.trim="filtros.tipo_formato" type="text" placeholder="Bitacora, F023…" />
        </div>
        <div class="campo">
          <label for="desde">Cargada desde</label>
          <input id="desde" v-model="filtros.fecha_desde" type="date" />
        </div>
        <div class="campo">
          <label for="hasta">Cargada hasta</label>
          <input id="hasta" v-model="filtros.fecha_hasta" type="date" />
        </div>
      </div>
      <button class="btn btn-primario" type="button" @click="aplicarFiltros">
        <Filter :size="15" />
        Aplicar filtros
      </button>
    </div>

    <div class="tarjeta tarjeta-flush mt-1">
      <VacioEstado
        v-if="cargando || !pagina || pagina.items.length === 0"
        :icono="FileSearch"
        :cargando="cargando"
        titulo="Sin resultados"
        :texto="
          cargando
            ? 'Aplicando filtros y consultando el servidor…'
            : 'Ninguna evidencia coincide con los filtros aplicados.'
        "
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
                <th>Límite</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in pagina.items" :key="e.id_evidencia">
                <td>{{ e.titulo }}</td>
                <td>{{ e.tipo_formato }}</td>
                <td><EstadoBadge :estado="e.estado" /></td>
                <td>{{ e.fecha_carga.slice(0, 10) }}</td>
                <td>{{ e.fecha_deadline ? e.fecha_deadline.slice(0, 10) : '—' }}</td>
                <td class="der">
                  <button class="btn btn-suave" type="button" @click="descargarPdf(e)">
                    <FileDown :size="15" />
                    PDF
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <PaginacionBar
            :pagina="pagina.page"
            :total-paginas="pagina.total_pages"
            :pagina-actual="paginaActual"
            @cambiar="cambiarPagina"
          />
        </div>
      </template>
    </div>
  </div>
</template>
