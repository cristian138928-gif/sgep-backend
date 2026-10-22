<script setup lang="ts">
// src/views/aprendiz/MisEvidenciasView.vue
// EXPLICACIÓN: subida Multipart/form-data + descarga con Bearer => 2 casos de uso del RF01
import { computed, onMounted, reactive, ref } from 'vue'
import { FileDown, MessageSquareText, Upload } from 'lucide-vue-next'

import { api, descargar, ApiError } from '../../api/client'
import type { Evidencia, Retroalimentacion } from '../../api/types'
import EstadoBadge from '../../components/EstadoBadge.vue'
import VacioEstado from '../../components/VacioEstado.vue'

const evidencias = ref<Evidencia[]>([])
const cargando = ref(true)
const error = ref('')
const info = ref('')
const subiendo = ref(false)

// EXPLICACIÓN: 'sin' = aún no evaluada (404); 'error' = fallo; ausente = sin consultar
const retros = reactive<Record<number, Retroalimentacion | 'sin' | 'error'>>({})
const cargandoRetro = ref(0)
const retroAbierta = ref<number | null>(null)

// EXPLICACIÓN: variable simple => vue-tsc estrecha la unión en las ramas del template
const retroVisible = computed<Retroalimentacion | 'sin' | 'error' | undefined>(() =>
  retroAbierta.value === null ? undefined : retros[retroAbierta.value],
)

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

async function alternarRetro(e: Evidencia): Promise<void> {
  error.value = ''
  const id = e.id_evidencia
  retroAbierta.value = retroAbierta.value === id ? null : id
  // EXPLICACIÓN: 'error' se reintenta al reabrir; el resto ya está en caché local
  if (retroAbierta.value === null || (id in retros && retros[id] !== 'error')) return

  cargandoRetro.value = id
  try {
    retros[id] = await api<Retroalimentacion>(
      `/api/v1/evidencias/${id}/retroalimentacion`,
    )
  } catch (err) {
    // EXPLICACIÓN: 404 = aún no evaluada (mensaje neutro); el resto sí se reporta
    const sinRetro = err instanceof ApiError && err.status === 404
    retros[id] = sinRetro ? 'sin' : 'error'
    if (!sinRetro) {
      error.value = 'No se pudo cargar la retroalimentación.'
      retroAbierta.value = null
    }
  } finally {
    cargandoRetro.value = 0
  }
}

async function cargar(): Promise<void> {
  cargando.value = true
  try {
    evidencias.value = await api<Evidencia[]>('/api/v1/evidencias/mis-evidencias')
  } finally {
    cargando.value = false
  }
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
    <div class="encabezado">
      <div>
        <div class="migas">Aprendiz · Etapa práctica</div>
        <h1>Mis evidencias</h1>
      </div>
    </div>

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
          <Upload v-if="!subiendo" :size="15" />
          {{ subiendo ? 'Subiendo…' : 'Subir evidencia' }}
        </button>
      </form>
    </div>

    <div class="tarjeta tarjeta-flush mt-1">
      <VacioEstado
        v-if="cargando || evidencias.length === 0"
        :icono="Upload"
        :cargando="cargando"
        titulo="Aún no has subido evidencias"
        texto="Usa el formulario superior para adjuntar tu primera evidencia."
      />

      <div v-else class="tabla-contenedor tabla-plana">
        <table class="tabla">
          <thead>
            <tr>
              <th>Título</th>
              <th>Tipo</th>
              <th>Estado</th>
              <th>Cargada</th>
              <th>Límite</th>
              <th></th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <template v-for="e in evidencias" :key="e.id_evidencia">
              <tr>
                <td>{{ e.titulo }}</td>
                <td>{{ e.tipo_formato }}</td>
                <td><EstadoBadge :estado="e.estado" /></td>
                <td>{{ fechaCorta(e.fecha_carga) }}</td>
                <td>{{ fechaCorta(e.fecha_deadline) }}</td>
                <td class="der">
                  <button class="btn btn-suave" type="button" @click="descargarEvidencia(e)">
                    <FileDown :size="15" />
                    PDF
                  </button>
                </td>
                <td class="der">
                  <button class="btn btn-suave" type="button" @click="alternarRetro(e)">
                    <MessageSquareText :size="15" />
                    {{ retroAbierta === e.id_evidencia ? 'Ocultar' : 'Retroalimentación' }}
                  </button>
                </td>
              </tr>
              <tr v-if="retroAbierta === e.id_evidencia">
                <td colspan="7" class="fila-expandida">
                  <p v-if="cargandoRetro === e.id_evidencia">Cargando retroalimentación…</p>
                  <p v-else-if="retroVisible === 'sin'">
                    Aún no hay retroalimentación para esta evidencia.
                  </p>
                  <div v-else-if="typeof retroVisible === 'object'">
                    <p>
                      <strong>{{ retroVisible.estado_evaluacion }}</strong>
                      · {{ fechaCorta(retroVisible.fecha_revision) }}
                    </p>
                    <p>{{ retroVisible.observaciones }}</p>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
