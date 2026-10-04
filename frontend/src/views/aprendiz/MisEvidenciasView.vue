<script setup lang="ts">
// src/views/aprendiz/MisEvidenciasView.vue
// EXPLICACIÓN: subida Multipart/form-data + descarga con Bearer => 2 casos de uso del RF01
import { onMounted, reactive, ref } from 'vue'

import { api, descargar, ApiError } from '../../api/client'
import type { Evidencia } from '../../api/types'
import EstadoBadge from '../../components/EstadoBadge.vue'

const evidencias = ref<Evidencia[]>([])
const error = ref('')
const info = ref('')
const subiendo = ref(false)

const form = reactive({
  titulo: '',
  tipo_formato: 'Bitacora',
  fecha_deadline: '',
  archivo: null as File | null,
})

function seleccionarArchivo(event: Event): void {
  const input = event.target as HTMLInputElement
  form.archivo = input.files?.[0] ?? null
}

async function subir(): Promise<void> {
  error.value = ''
  info.value = ''

  if (!form.archivo) {
    error.value = 'Selecciona un archivo PDF.'
    return
  }

  subiendo.value = true
  try {
    // EXPLICACIÓN: FormData => el browser pone el boundary multipart automáticamente
    const datos = new FormData()
    datos.append('titulo', form.titulo)
    datos.append('tipo_formato', form.tipo_formato)
    if (form.fecha_deadline) datos.append('fecha_deadline', form.fecha_deadline)
    datos.append('file', form.archivo)

    await api<Evidencia>('/api/v1/evidencias/upload', { method: 'POST', body: datos })
    info.value = `Evidencia "${form.titulo}" subida correctamente.`
    form.titulo = ''
    form.fecha_deadline = ''
    form.archivo = null
    await cargar()
  } catch (e) {
    error.value =
      e instanceof ApiError ? e.detail : 'No se pudo subir la evidencia (¿pesa más de 10 MB?).'
  } finally {
    subiendo.value = false
  }
}

async function descargarEvidencia(e: Evidencia): Promise<void> {
  error.value = ''
  try {
    await descargar(`/api/v1/evidencias/${e.id_evidencia}/descarga`, `${e.titulo}.pdf`)
  } catch {
    error.value = 'No se pudo descargar la evidencia.'
  }
}

async function cargar(): Promise<void> {
  evidencias.value = await api<Evidencia[]>('/api/v1/evidencias/mis-evidencias')
}

onMounted(async () => {
  try {
    await cargar()
  } catch {
    error.value = 'No se pudieron cargar tus evidencias.'
  }
})

function fechaCorta(iso: string | null): string {
  return iso ? iso.slice(0, 10) : '—'
}
</script>

<template>
  <div>
    <h1>Mis evidencias</h1>

    <div v-if="error" class="alerta-error">{{ error }}</div>
    <div v-if="info" class="alerta-info">{{ info }}</div>

    <div class="tarjeta">
      <h2>Subir nueva evidencia</h2>
      <form @submit.prevent="subir">
        <div class="rejilla rejilla-2">
          <div class="campo">
            <label for="titulo">Título</label>
            <input id="titulo" v-model.trim="form.titulo" type="text" required />
          </div>
          <div class="campo">
            <label for="tipo">Tipo de formato</label>
            <select id="tipo" v-model="form.tipo_formato">
              <option>Bitacora</option>
              <option>F023</option>
              <option>Informe</option>
              <option>Otro</option>
            </select>
          </div>
          <div class="campo">
            <label for="deadline">Fecha límite (opcional)</label>
            <input id="deadline" v-model="form.fecha_deadline" type="date" />
          </div>
          <div class="campo">
            <label for="archivo">Archivo PDF (máx. 10 MB)</label>
            <input id="archivo" type="file" accept=".pdf" required @change="seleccionarArchivo" />
          </div>
        </div>
        <button class="btn btn-primario" type="submit" :disabled="subiendo">
          {{ subiendo ? 'Subiendo…' : 'Subir evidencia' }}
        </button>
      </form>
    </div>

    <div class="tarjeta" style="margin-top: 1rem; padding: 0">
      <div v-if="evidencias.length === 0" class="vacio">
        <h3>Aún no has subido evidencias</h3>
        <p>Usa el formulario superior para adjuntar tu primera evidencia.</p>
      </div>

      <div v-else class="tabla-contenedor" style="border: none; box-shadow: none">
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
            <tr v-for="e in evidencias" :key="e.id_evidencia">
              <td>{{ e.titulo }}</td>
              <td>{{ e.tipo_formato }}</td>
              <td><EstadoBadge :estado="e.estado" /></td>
              <td>{{ fechaCorta(e.fecha_carga) }}</td>
              <td>{{ fechaCorta(e.fecha_deadline) }}</td>
              <td style="text-align: right">
                <button class="btn btn-suave" type="button" @click="descargarEvidencia(e)">
                  Descargar PDF
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
