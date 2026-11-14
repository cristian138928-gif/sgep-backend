<script setup lang="ts">
// src/views/aprendiz/MisEvidenciasView.vue
// EXPLICACIÓN: subida Multipart/form-data + descarga con Bearer => 2 casos de uso del RF01
import { computed, onMounted, reactive, ref } from 'vue'
import { FileDown, MessageSquareText, Upload, X } from 'lucide-vue-next'

import { api, descargar, ApiError } from '../../api/client'
import type { Evidencia, Retroalimentacion } from '../../api/types'
import vacioDocumentos from '../../assets/imagenes/vacio-documentos.svg'
import EstadoBadge from '../../components/EstadoBadge.vue'
import Esqueleto from '../../components/Esqueleto.vue'
import VacioEstado from '../../components/VacioEstado.vue'
import {
  btnPrimario,
  btnSecundario,
  etiquetaCampo,
  inputCampo,
  thTabla,
  trTabla,
} from '../../styles/ui-classes'

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

// ---- Zona de arrastre (drag & drop) ----
const MAXIMO_ARCHIVO = 10 * 1024 * 1024
// EXPLICACIÓN: RF01 ampliado => documento, paquete comprimido o video corto
const EXTENSIONES_OK = ['.pdf', '.zip', '.mp4', '.mov', '.webm']

const arrastrando = ref(false)
const inputArchivo = ref<HTMLInputElement | null>(null)

const extension = computed(() => {
  const nombre = form.archivo?.name ?? ''
  return nombre.includes('.') ? (nombre.split('.').pop() ?? '').toUpperCase() : ''
})

function validarArchivo(archivo: File): string {
  const nombre = archivo.name.toLowerCase()
  const valido =
    EXTENSIONES_OK.some((ext) => nombre.endsWith(ext)) || archivo.type.startsWith('video/')
  if (!valido) return 'Formato no admitido: usa PDF, ZIP o un video corto (MP4, MOV o WEBM).'
  if (archivo.size > MAXIMO_ARCHIVO) return 'El archivo supera el límite de 10 MB.'
  return ''
}

/** EXPLICACIÓN: una sola puerta de entrada => el selector y el drop validan igual */
function asignarArchivo(archivo: File | null | undefined): boolean {
  if (!archivo) return false
  const problema = validarArchivo(archivo)
  if (problema) {
    error.value = problema
    form.archivo = null
    return false
  }
  error.value = ''
  form.archivo = archivo
  return true
}

function seleccionarArchivo(event: Event): void {
  const input = event.target as HTMLInputElement
  if (!asignarArchivo(input.files?.[0])) input.value = ''
}

function alEntrar(): void {
  arrastrando.value = true
}

function alSalir(event: DragEvent): void {
  const actual = event.currentTarget as HTMLElement
  const destino = event.relatedTarget as Node | null
  // EXPLICACIÓN: dragleave salta al entrar en un hijo => se ignora para no parpadear
  if (destino && actual.contains(destino)) return
  arrastrando.value = false
}

function alSoltar(event: DragEvent): void {
  arrastrando.value = false
  if (!asignarArchivo(event.dataTransfer?.files?.[0]) && inputArchivo.value) {
    inputArchivo.value.value = ''
  }
}

function quitarArchivo(): void {
  form.archivo = null
  if (inputArchivo.value) inputArchivo.value.value = ''
}

async function subir(): Promise<void> {
  error.value = ''
  info.value = ''

  if (!form.archivo) {
    error.value = 'Selecciona un archivo PDF, ZIP o video corto.'
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
    quitarArchivo()
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
  <div class="min-h-full bg-slate-50 font-sans text-slate-900">
    <!-- EXPLICACIÓN: .alerta-error/.alerta-info (main.css) ya usa la paleta rose/blue de la guía -->
    <div v-if="error" role="alert" class="alerta-error">{{ error }}</div>
    <div v-if="info" role="status" class="alerta-info">{{ info }}</div>

    <header class="mb-5 flex flex-wrap items-end justify-between gap-3 border-b border-slate-200 pb-4">
      <div class="flex items-center gap-3">
        <span
          class="flex h-10 w-10 flex-none items-center justify-center rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700"
          aria-hidden="true"
        >
          <Upload :size="20" />
        </span>
        <div>
          <p class="m-0 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Aprendiz · Etapa práctica
          </p>
          <!-- EXPLICACIÓN: utilities > components (layers.css) => sin '!' -->
          <h1 class="text-2xl font-bold m-0 text-slate-900">Mis evidencias</h1>
          <p class="m-0 mt-2 text-sm text-slate-500">
            Sube tus evidencias y consulta su estado de revisión.
          </p>
        </div>
      </div>
      <span
        class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600 shadow-sm"
      >
        <Upload :size="13" class="text-emerald-600" aria-hidden="true" />
        {{ evidencias.length }} registros
      </span>
    </header>

    <section class="mb-5 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
      <div class="mb-4 flex items-center gap-3">
        <span
          class="flex h-10 w-10 flex-none items-center justify-center rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700"
          aria-hidden="true"
        >
          <Upload :size="20" />
        </span>
        <div>
          <h2 class="m-0 text-base font-semibold text-slate-900">Subir nueva evidencia</h2>
          <p class="m-0 mt-0.5 text-sm text-slate-500">
            Adjunta un PDF, un ZIP o un video corto de tu evidencia.
          </p>
        </div>
      </div>

      <form class="space-y-4" @submit.prevent="subir">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <label for="titulo" :class="etiquetaCampo">Título</label>
            <input
              id="titulo"
              v-model.trim="form.titulo"
              type="text"
              required
              :class="inputCampo"
            />
          </div>
          <div>
            <label for="tipo" :class="etiquetaCampo">Tipo de formato</label>
            <select id="tipo" v-model="form.tipo_formato" :class="inputCampo">
              <option>Bitacora</option>
              <option>F023</option>
              <option>F028</option>
              <option>Informe</option>
              <option>Otro</option>
            </select>
          </div>
          <div>
            <label for="deadline" :class="etiquetaCampo">Fecha límite (opcional)</label>
            <input id="deadline" v-model="form.fecha_deadline" type="date" :class="inputCampo" />
          </div>
        </div>

        <div>
          <span :class="etiquetaCampo">Archivo · PDF, ZIP o video (máx. 10 MB)</span>
          <label
            for="archivo"
            class="flex cursor-pointer flex-col items-center justify-center gap-1.5 rounded-xl border-2 border-dashed px-4 py-7 text-center transition-colors"
            :class="
              arrastrando
                ? 'border-emerald-500 bg-emerald-50'
                : 'border-slate-300 bg-slate-50 hover:border-emerald-400 hover:bg-emerald-50/40'
            "
            @dragenter.prevent="alEntrar"
            @dragover.prevent="alEntrar"
            @dragleave.prevent="alSalir"
            @drop.prevent="alSoltar"
          >
            <Upload :size="26" class="text-emerald-600" aria-hidden="true" />
            <span class="text-sm font-medium text-slate-700">
              Arrastra aquí tu archivo o
              <span class="text-emerald-600 underline">selecciónalo</span>
            </span>
            <span class="text-xs text-slate-500">PDF · ZIP · MP4 / MOV / WEBM</span>
            <input
              id="archivo"
              ref="inputArchivo"
              type="file"
              class="sr-only"
              accept=".pdf,.zip,video/mp4,video/quicktime,video/webm"
              @change="seleccionarArchivo"
            />
          </label>

          <div
            v-if="form.archivo"
            class="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm"
          >
            <div class="flex min-w-0 items-center gap-2">
              <span
                class="flex-none rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-xs font-semibold uppercase text-emerald-700"
              >
                {{ extension }}
              </span>
              <span class="truncate text-sm font-medium text-slate-700">
                {{ form.archivo.name }}
              </span>
              <span class="flex-none text-xs text-slate-500">
                {{ (form.archivo.size / 1024).toFixed(1) }} KB
              </span>
            </div>
            <button :class="btnSecundario" type="button" @click="quitarArchivo">
              <X :size="14" />
              Quitar
            </button>
          </div>
        </div>

        <button :class="btnPrimario" type="submit" :disabled="subiendo">
          <Upload v-if="!subiendo" :size="15" />
          {{ subiendo ? 'Subiendo…' : 'Subir evidencia' }}
        </button>
      </form>
    </section>

    <section class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <Esqueleto v-if="cargando" :filas="5" />
      <VacioEstado
        v-else-if="evidencias.length === 0"
        :icono="Upload"
        :ilustracion="vacioDocumentos"
        titulo="Aún no has subido evidencias"
        texto="Usa la zona superior para adjuntar tu primera evidencia."
      />

      <div v-else class="overflow-x-auto">
        <table class="w-full min-w-[860px] border-collapse text-left text-sm">
          <thead>
            <tr>
              <th :class="thTabla">Título</th>
              <th :class="thTabla">Tipo</th>
              <th :class="thTabla">Estado</th>
              <th :class="thTabla">Cargada</th>
              <th :class="thTabla">Límite</th>
              <th :class="[thTabla, 'text-right']">Archivo</th>
              <th :class="[thTabla, 'text-right']">Retroalimentación</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <template v-for="e in evidencias" :key="e.id_evidencia">
              <tr :class="trTabla">
                <td class="px-4 py-3 font-medium text-slate-900">{{ e.titulo }}</td>
                <td class="px-4 py-3 text-slate-600">{{ e.tipo_formato }}</td>
                <td class="px-4 py-3">
                  <EstadoBadge :estado="e.estado" />
                </td>
                <td class="px-4 py-3 tabular-nums text-slate-600">{{ fechaCorta(e.fecha_carga) }}</td>
                <td class="px-4 py-3 tabular-nums text-slate-600">
                  {{ fechaCorta(e.fecha_deadline) }}
                </td>
                <td class="whitespace-nowrap px-4 py-3 text-right">
                  <button
                    :class="btnSecundario"
                    type="button"
                    :aria-label="`Descargar ${e.titulo}`"
                    @click="descargarEvidencia(e)"
                  >
                    <FileDown :size="15" />
                    PDF
                  </button>
                </td>
                <td class="whitespace-nowrap px-4 py-3 text-right">
                  <button
                    :class="btnSecundario"
                    type="button"
                    :aria-expanded="retroAbierta === e.id_evidencia"
                    :aria-label="`${retroAbierta === e.id_evidencia ? 'Ocultar' : 'Ver'} retroalimentación de ${e.titulo}`"
                    @click="alternarRetro(e)"
                  >
                    <MessageSquareText :size="15" />
                    {{ retroAbierta === e.id_evidencia ? 'Ocultar' : 'Retroalimentación' }}
                  </button>
                </td>
              </tr>
              <tr v-if="retroAbierta === e.id_evidencia" class="bg-slate-50/70">
                <td colspan="7" class="px-4 py-3 text-sm text-slate-600">
                  <p v-if="cargandoRetro === e.id_evidencia" class="m-0">
                    Cargando retroalimentación…
                  </p>
                  <p v-else-if="retroVisible === 'sin'" class="m-0">
                    Aún no hay retroalimentación para esta evidencia.
                  </p>
                  <div v-else-if="typeof retroVisible === 'object'">
                    <p class="m-0">
                      <strong>{{ retroVisible.estado_evaluacion }}</strong>
                      · {{ fechaCorta(retroVisible.fecha_revision) }}
                    </p>
                    <p class="m-0 mt-2">{{ retroVisible.observaciones }}</p>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
