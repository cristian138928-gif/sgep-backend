<script setup lang="ts">
// src/views/coordinador/AsignacionesView.vue
// EXPLICACIÓN: RF05 - el coordinador vincula aprendices con su instructor seguidor
import { computed, onMounted, reactive, ref } from 'vue'

import { api, ApiError } from '../../api/client'
import type { Asignacion, AvanceAprendiz, Instructor } from '../../api/types'

const aprendices = ref<AvanceAprendiz[]>([])
const instructores = ref<Instructor[]>([])
const asignaciones = ref<Asignacion[]>([])
const error = ref('')
const info = ref('')
const ocupado = ref(0)

// EXPLICACIÓN: elección pendiente por aprendiz (undefined = aún sin elegir)
const elegidos = reactive<Record<number, number | undefined>>({})

// EXPLICACIÓN: un solo Map => lookup O(1) al pintar, sin N peticiones
const porAprendiz = computed(() => new Map(asignaciones.value.map((a) => [a.id_aprendiz, a])))

async function cargar(): Promise<void> {
  error.value = ''
  try {
    // EXPLICACIÓN: 3 GET independientes en paralelo montan la vista en una ronda de red
    const [aps, ins, asg] = await Promise.all([
      api<AvanceAprendiz[]>('/api/v1/coordinador/aprendices'),
      api<Instructor[]>('/api/v1/coordinador/instructores'),
      api<Asignacion[]>('/api/v1/asignaciones/'),
    ])
    aprendices.value = aps
    instructores.value = ins
    asignaciones.value = asg
  } catch {
    error.value = 'No se pudo cargar la información de asignaciones.'
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
  <div>
    <h1>Asignaciones de seguimiento</h1>
    <p>Vincula cada aprendiz con su instructor seguidor (RF05).</p>

    <div v-if="error" class="alerta-error">{{ error }}</div>
    <div v-if="info" class="alerta-info">{{ info }}</div>

    <div class="tarjeta" style="padding: 0">
      <div v-if="aprendices.length === 0" class="vacio">
        <h3>Sin aprendices</h3>
        <p>No hay aprendices registrados en el sistema.</p>
      </div>

      <div v-else class="tabla-contenedor" style="border: none; box-shadow: none">
        <table class="tabla">
          <thead>
            <tr>
              <th>Aprendiz</th>
              <th>Ficha</th>
              <th>Instructor seguidor</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in aprendices" :key="a.id_usuario">
              <td>{{ a.nombre_completo }}</td>
              <td>{{ a.numero_ficha }}</td>
              <td>
                <template v-if="porAprendiz.get(a.id_usuario)">
                  {{ porAprendiz.get(a.id_usuario)!.nombre_instructor }}
                </template>
                <span v-else><small style="color: var(--texto-suave)">Sin asignar</small></span>
              </td>
              <td style="text-align: right; white-space: nowrap">
                <template v-if="porAprendiz.get(a.id_usuario)">
                  <button
                    class="btn btn-suave"
                    type="button"
                    :disabled="ocupado === a.id_usuario"
                    @click="quitar(a.id_usuario)"
                  >
                    Quitar
                  </button>
                </template>
                <template v-else>
                  <select
                    v-model="elegidos[a.id_usuario]"
                    :aria-label="`Instructor para ${a.nombre_completo}`"
                    style="margin-right: 0.5rem"
                  >
                    <option :value="undefined" disabled>Seleccione…</option>
                    <option v-for="i in instructores" :key="i.id_usuario" :value="i.id_usuario">
                      {{ i.nombre_completo }}
                    </option>
                  </select>
                  <button
                    class="btn btn-primario"
                    type="button"
                    :disabled="ocupado === a.id_usuario || !elegidos[a.id_usuario]"
                    @click="asignar(a.id_usuario)"
                  >
                    Asignar
                  </button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
