<script setup lang="ts">
// src/views/instructor/EvaluarView.vue
// EXPLICACIÓN: los metadatos llegan via history.state desde la bandeja
// (GET /evidencias/{id} exige ser asignado; evaluar no) => fallback a fetch.
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api, ApiError } from '../../api/client'
import type { Evidencia, Retroalimentacion } from '../../api/types'

const props = defineProps<{ id: string }>()
const router = useRouter()

const estado = ref<'Aprobada' | 'Ajuste Requerido'>('Aprobada')
const observaciones = ref('')
const error = ref('')
const enviando = ref(false)

const meta = ref<Pick<Evidencia, 'titulo' | 'tipo_formato' | 'fecha_deadline'> | null>(
  (history.state as { evidencia?: Pick<Evidencia, 'titulo' | 'tipo_formato' | 'fecha_deadline'> })
    .evidencia ?? null,
)

onMounted(async () => {
  if (meta.value) return
  try {
    meta.value = await api<Evidencia>(`/api/v1/evidencias/${props.id}`)
  } catch {
    // EXPLICACIÓN: sin metadatos el instructor aún puede evaluar (solo verá el ID)
  }
})

async function enviar(): Promise<void> {
  error.value = ''
  if (observaciones.value.trim().length < 10) {
    error.value = 'Las observaciones deben tener al menos 10 caracteres.'
    return
  }

  enviando.value = true
  try {
    await api<Retroalimentacion>(`/api/v1/instructor/evaluar/${props.id}`, {
      method: 'PUT',
      body: JSON.stringify({
        estado: estado.value,
        observaciones: observaciones.value.trim(),
      }),
    })
    await router.push({ name: 'pendientes' })
  } catch (e) {
    if (e instanceof ApiError && e.status === 409) {
      error.value = 'Esta evidencia ya fue evaluada.'
      setTimeout(() => void router.push({ name: 'pendientes' }), 1500)
    } else if (e instanceof ApiError) {
      error.value = e.detail
    } else {
      error.value = 'No se pudo registrar la evaluación.'
    }
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <div>
    <h1>Evaluar evidencia #{{ id }}</h1>

    <div class="tarjeta">
      <div v-if="meta">
        <h2>{{ meta.titulo }}</h2>
        <p style="color: var(--texto-suave); margin-top: 0">
          {{ meta.tipo_formato }}
          <template v-if="meta.fecha_deadline">
            · Límite: {{ meta.fecha_deadline.slice(0, 10) }}
          </template>
        </p>
      </div>
      <p v-else style="color: var(--texto-suave)">Cargando metadatos…</p>

      <div v-if="error" class="alerta-error">{{ error }}</div>

      <form @submit.prevent="enviar">
        <div class="campo">
          <label>Decisión</label>
          <label style="font-weight: 400; display: inline-flex; gap: 0.4rem; margin-right: 1.2rem">
            <input v-model="estado" type="radio" value="Aprobada" required />
            Aprobada
          </label>
          <label style="font-weight: 400; display: inline-flex; gap: 0.4rem">
            <input v-model="estado" type="radio" value="Ajuste Requerido" required />
            Ajuste Requerido
          </label>
        </div>

        <div class="campo">
          <label for="observaciones">Observaciones (10–1000 caracteres)</label>
          <textarea
            id="observaciones"
            v-model="observaciones"
            rows="5"
            minlength="10"
            maxlength="1000"
            required
            placeholder="Describe qué está bien y qué debe corregir el aprendiz…"
          />
        </div>

        <div style="display: flex; gap: 0.7rem">
          <button class="btn btn-primario" type="submit" :disabled="enviando">
            {{ enviando ? 'Guardando…' : 'Registrar evaluación' }}
          </button>
          <button class="btn" type="button" @click="router.push({ name: 'pendientes' })">
            Cancelar
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
