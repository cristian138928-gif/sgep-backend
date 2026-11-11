<script setup lang="ts">
// src/views/NotificacionesView.vue
// EXPLICACIÓN: central de avisos de TODOS los roles (mismo endpoint por id_usuario)
import { onMounted, ref } from 'vue'
import { Bell, BellOff, Check, CheckCheck } from 'lucide-vue-next'

import type { Notificacion } from '../api/types'
import VacioEstado from '../components/VacioEstado.vue'
import { useNotificacionesStore } from '../stores/notificaciones'
import { btnSecundario, pillBase } from '../styles/ui-classes'

const store = useNotificacionesStore()
const marcando = ref<number | null>(null)

onMounted(() => {
  void store.refrescar()
})

async function marcar(id: number): Promise<void> {
  marcando.value = id
  try {
    await store.marcarLeida(id)
  } finally {
    marcando.value = null
  }
}

function fechaCorta(n: Notificacion): string {
  return new Date(n.fecha_creacion).toLocaleString('es-CO', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

// EXPLICACIÓN: tipo de aviso => píldora con la paleta de la guía (amber/rose/emerald)
const clasesTipo: Record<string, string> = {
  evaluacion: 'border-amber-200 bg-amber-50 text-amber-700',
  vencimiento: 'border-rose-200 bg-rose-50 text-rose-700',
  sistema: 'border-emerald-200 bg-emerald-50 text-emerald-700',
}
const tipoDesconocido = 'border-slate-200 bg-slate-50 text-slate-600'
</script>

<template>
  <div class="min-h-full bg-slate-50 font-sans text-slate-900">
    <header class="mb-5 flex flex-wrap items-end justify-between gap-3 border-b border-slate-200 pb-4">
      <div class="flex items-center gap-3">
        <span
          class="flex h-10 w-10 flex-none items-center justify-center rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700"
          aria-hidden="true"
        >
          <Bell :size="20" />
        </span>
        <div>
          <p class="m-0 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Central de avisos
          </p>
          <!-- EXPLICACIÓN: utilities > components (layers.css) => sin '!' -->
          <h1 class="text-2xl font-bold m-0 text-slate-900">Notificaciones</h1>
          <p class="m-0 mt-2 text-sm text-slate-500">
            Resultados de tus evaluaciones, vencimientos y avisos del sistema.
          </p>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <span
          class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600 shadow-sm"
        >
          <Bell :size="13" class="text-emerald-600" aria-hidden="true" />
          {{ store.noLeidas }} sin leer
        </span>
        <button
          :class="btnSecundario"
          type="button"
          :disabled="store.noLeidas === 0"
          @click="store.marcarTodas()"
        >
          <CheckCheck :size="15" />
          Marcar todas como leídas
        </button>
      </div>
    </header>

    <section
      v-if="store.items.length === 0"
      class="rounded-xl border border-slate-200 bg-white shadow-sm"
    >
      <VacioEstado
        :icono="BellOff"
        titulo="No tienes notificaciones"
        texto="Aquí aparecerán los resultados de tus evaluaciones y avisos de vencimiento."
      />
    </section>

    <section v-else class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div class="divide-y divide-slate-100">
        <div
          v-for="n in store.items"
          :key="n.id_notificacion"
          class="flex flex-wrap items-center justify-between gap-3 px-4 py-3.5 transition-colors hover:bg-slate-50/50"
          :class="{ 'bg-emerald-50/60': !n.leida }"
        >
          <div class="min-w-0">
            <p class="m-0 text-sm font-medium text-slate-900">{{ n.mensaje }}</p>
            <p class="m-0 mt-2 text-xs text-slate-500">{{ fechaCorta(n) }}</p>
          </div>
          <div class="flex flex-none items-center gap-3">
            <span :class="[pillBase, clasesTipo[n.tipo] ?? tipoDesconocido]">{{ n.tipo }}</span>
            <button
              v-if="!n.leida"
              :class="btnSecundario"
              type="button"
              :disabled="marcando === n.id_notificacion"
              @click="marcar(n.id_notificacion)"
            >
              <Check :size="15" />
              Marcar leída
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
