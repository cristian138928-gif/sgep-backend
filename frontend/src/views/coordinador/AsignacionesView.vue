<script setup lang="ts">
// src/views/coordinador/AsignacionesView.vue
// EXPLICACIÓN: RF05 - el coordinador vincula aprendices con su instructor seguidor
import { computed, onMounted, reactive, ref } from 'vue'
import { UserCheck, UserMinus, UserPlus, Users } from 'lucide-vue-next'

import { api, ApiError } from '../../api/client'
import type { Asignacion, AvanceAprendiz, Instructor, Pagina } from '../../api/types'
import AvatarNombre from '../../components/AvatarNombre.vue'
import Esqueleto from '../../components/Esqueleto.vue'
import PaginacionBar from '../../components/PaginacionBar.vue'
import VacioEstado from '../../components/VacioEstado.vue'
import {
  alertaError,
  alertaInfo,
  btnPrimario,
  btnSecundario,
  cabeceraPagina,
  chipNeutro,
  iconoCaja,
  inputBase,
  paginaWrap,
  thTabla,
  trTabla,
} from '../../styles/ui-classes'

const aprendices = ref<AvanceAprendiz[]>([])
const paginaActual = ref(1)
const totalPaginas = ref(1)
const instructores = ref<Instructor[]>([])
const asignaciones = ref<Asignacion[]>([])
const cargando = ref(true)
const error = ref('')
const info = ref('')
const ocupado = ref(0)

// EXPLICACIÓN: elección pendiente por aprendiz (undefined = aún sin elegir)
const elegidos = reactive<Record<number, number | undefined>>({})

// EXPLICACIÓN: un solo Map => lookup O(1) al pintar, sin N peticiones
const porAprendiz = computed(() => new Map(asignaciones.value.map((a) => [a.id_aprendiz, a])))

async function cargar(): Promise<void> {
  error.value = ''
  cargando.value = true
  try {
    // EXPLICACIÓN: 3 GET independientes en paralelo montan la vista en una ronda de red
    const [aps, ins, asg] = await Promise.all([
      api<Pagina<AvanceAprendiz>>(
        `/api/v1/coordinador/aprendices?page=${paginaActual.value}&page_size=10`,
      ),
      api<Instructor[]>('/api/v1/coordinador/instructores'),
      api<Asignacion[]>('/api/v1/asignaciones/'),
    ])
    aprendices.value = aps.items
    totalPaginas.value = aps.total_pages
    instructores.value = ins
    asignaciones.value = asg
  } catch {
    error.value = 'No se pudo cargar la información de asignaciones.'
  } finally {
    cargando.value = false
  }
}

function cambiarPagina(delta: number): void {
  const destino = paginaActual.value + delta
  if (destino >= 1 && destino <= totalPaginas.value) {
    paginaActual.value = destino
    void cargar()
  }
}

async function asignar(id_aprendiz: number): Promise<void> {
  const id_instructor = elegidos[id_aprendiz]
  if (!id_instructor) {
    error.value = 'Selecciona un instructor antes de asignar.'
    return
  }
  error.value = ''
  info.value = ''
  ocupado.value = id_aprendiz
  try {
    await api<Asignacion>('/api/v1/asignaciones/', {
      method: 'POST',
      body: JSON.stringify({ id_aprendiz, id_instructor }),
    })
    info.value = 'Asignación creada correctamente.'
    delete elegidos[id_aprendiz]
    await cargar()
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail : 'No se pudo crear la asignación.'
  } finally {
    ocupado.value = 0
  }
}

async function quitar(id_aprendiz: number): Promise<void> {
  error.value = ''
  info.value = ''
  ocupado.value = id_aprendiz
  try {
    await api<{ mensaje: string }>(`/api/v1/asignaciones/${id_aprendiz}`, {
      method: 'DELETE',
    })
    info.value = 'Asignación retirada.'
    await cargar()
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail : 'No se pudo retirar la asignación.'
  } finally {
    ocupado.value = 0
  }
}

onMounted(cargar)
</script>

<template>
  <div :class="paginaWrap">
    <div v-if="error" role="alert" :class="alertaError">
      {{ error }}
    </div>
    <div v-if="info" role="status" :class="alertaInfo">
      {{ info }}
    </div>

    <header :class="cabeceraPagina">
      <div class="flex items-center gap-3">
        <span :class="iconoCaja" aria-hidden="true">
          <UserCheck :size="20" />
        </span>
        <div>
          <p class="m-0 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Coordinación · Seguimiento RF05
          </p>
          <h1 class="m-0 text-2xl font-bold text-slate-900">Asignaciones de seguimiento</h1>
          <p class="m-0 mt-2 text-sm text-slate-500">
            Vincula cada aprendiz con su instructor seguidor.
          </p>
        </div>
      </div>
      <span :class="chipNeutro">
        <UserCheck :size="13" class="text-emerald-600" aria-hidden="true" />
        {{ asignaciones.length }} asignadas
      </span>
    </header>

    <section class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <Esqueleto v-if="cargando" :filas="5" />
      <VacioEstado
        v-else-if="aprendices.length === 0"
        :icono="Users"
        titulo="Sin aprendices"
        texto="No hay aprendices registrados en el sistema."
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full min-w-[720px] border-collapse text-left text-sm">
          <thead>
            <tr>
              <th :class="thTabla">Aprendiz</th>
              <th :class="thTabla">Ficha</th>
              <th :class="thTabla">Instructor seguidor</th>
              <th :class="[thTabla, 'text-right']">Acción</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="a in aprendices" :key="a.id_usuario" :class="trTabla">
              <td class="px-4 py-3">
                <AvatarNombre :nombre="a.nombre_completo" />
              </td>
              <td class="px-4 py-3 tabular-nums text-slate-600">{{ a.numero_ficha }}</td>
              <td class="px-4 py-3">
                <AvatarNombre
                  v-if="porAprendiz.get(a.id_usuario)"
                  :nombre="porAprendiz.get(a.id_usuario)!.nombre_instructor"
                />
                <span v-else class="text-sm text-slate-500">Sin asignar</span>
              </td>
              <td class="whitespace-nowrap px-4 py-3 text-right">
                <template v-if="porAprendiz.get(a.id_usuario)">
                  <button
                    :class="btnSecundario"
                    type="button"
                    :disabled="ocupado === a.id_usuario"
                    @click="quitar(a.id_usuario)"
                  >
                    <UserMinus :size="15" />
                    Quitar
                  </button>
                </template>
                <template v-else>
                  <select
                    v-model="elegidos[a.id_usuario]"
                    :aria-label="`Instructor para ${a.nombre_completo}`"
                    :class="[inputBase, 'mr-2']"
                  >
                    <option :value="undefined" disabled>Seleccione…</option>
                    <option v-for="i in instructores" :key="i.id_usuario" :value="i.id_usuario">
                      {{ i.nombre_completo }}
                    </option>
                  </select>
                  <button
                    :class="btnPrimario"
                    type="button"
                    :disabled="ocupado === a.id_usuario || !elegidos[a.id_usuario]"
                    @click="asignar(a.id_usuario)"
                  >
                    <UserPlus :size="15" />
                    Asignar
                  </button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
        <PaginacionBar
          :pagina="paginaActual"
          :total-paginas="totalPaginas"
          :pagina-actual="paginaActual"
          @cambiar="cambiarPagina"
        />
      </div>
    </section>
  </div>
</template>
