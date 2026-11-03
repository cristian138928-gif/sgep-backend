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
  <div>
    <div class="encabezado">
      <div>
        <div class="migas">Coordinación · Reportes</div>
        <h1>Aprendices y avance</h1>
      </div>
      <div class="acciones">
        <button class="btn btn-suave" type="button" :disabled="exportando" @click="exportarAvance">
          <Download :size="15" />
          {{ exportando ? 'Generando…' : 'Exportar avance (RF07)' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="alerta-error">{{ error }}</div>

    <div class="tarjeta">
      <form class="fila fila-fin" @submit.prevent="aplicarFiltro">
        <div class="campo">
          <label for="programa">Filtrar por programa</label>
          <input id="programa" v-model.trim="programa" type="text" placeholder="ADSO…" />
        </div>
        <button class="btn btn-primario" type="submit">
          <Search :size="15" />
          Buscar
        </button>
        <button
          v-if="programa"
          class="btn"
          type="button"
          @click="programa = ''; aplicarFiltro()"
        >
          <X :size="15" />
          Limpiar
        </button>
      </form>
    </div>

    <div class="tarjeta tarjeta-flush mt-1">
      <Esqueleto v-if="cargando" :filas="5" />
      <VacioEstado
        v-else-if="!pagina || pagina.items.length === 0"
        :icono="Users"
        :ilustracion="vacioDocumentos"
        titulo="Sin aprendices"
        texto="No hay aprendices registrados o el filtro no coincide."
      />

      <template v-else>
        <div class="tabla-contenedor tabla-plana">
          <table class="tabla">
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Ficha</th>
                <th>Programa</th>
                <th>Evidencias</th>
                <th>Aprobadas</th>
                <th>Avance</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in pagina.items" :key="a.id_usuario">
                <td><AvatarNombre :nombre="a.nombre_completo" /></td>
                <td>{{ a.numero_ficha }}</td>
                <td>{{ a.programa }}</td>
                <td>{{ a.total_evidencias }}</td>
                <td>{{ a.aprobadas }}</td>
                <td class="ancho-min">
                  <div class="barra-progreso">
                    <div :style="{ width: `${a.porcentaje_avance}%` }" />
                  </div>
                  <small class="dato">{{ a.porcentaje_avance }} %</small>
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
