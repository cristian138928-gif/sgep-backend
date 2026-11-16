<script setup lang="ts">
// src/views/NotificacionesView.vue
import { onMounted, ref } from 'vue'
import { Bell, BellOff, Check, CheckCheck } from 'lucide-vue-next'

import type { Notificacion } from '../api/types'
import VacioEstado from '../components/VacioEstado.vue'
import { useNotificacionesStore } from '../stores/notificaciones'
import {
  btnSecundario,
  cabeceraPagina,
  chipNeutro,
  iconoCaja,
  paginaWrap,
  pillBase,
} from '../styles/ui-classes'

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
  return new Date(n.fecha_creacion).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })
}

const clasesTipo: Record<string, string> = {
  evaluacion: 'border-amber-200 bg-amber-50 text-amber-700',
  vencimiento: 'border-rose-200 bg-rose-50 text-rose-700',
  sistema: 'border-emerald-200 bg-emerald-50 text-emerald-700',
}
const tipoDesconocido = 'border-slate-200 bg-slate-50 text-slate-600'
</script>

<template>
  <div :class="paginaWrap">
    <header :class="cabeceraPagina">
      <div class="flex items-center gap-3">
        <span :class="iconoCaja" aria-hidden="true"><Bell :size="20" /></span>
        <div>
          <p class="m-0 text-xs font-semibold uppercase tracking-wider text-slate-500">Central de avisos</p>
          <h1 class="m-0 text-2xl font-bold text-slate-900">Notificaciones</h1>
          <p class="m-0 mt-2 text-sm text-slate-500">
            Resultados de evaluaciones, vencimientos y avisos del sistema.
          </p>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <span :class="chipNeutro"><Bell :size="13" class="text-emerald-600" /> {{ store.noLeidas }} sin leer</span>
        <button
          :class="btnSecundario"
          type="button"
          :disabled="store.noLeidas === 0"
          @click="store.marcarTodas()"
        >
          <CheckCheck :size="15" /> Marcar todas como leídas
        </button>
      </div>
    </header>

    <section v-if="store.items.length === 0" class="rounded-xl border border-slate-200 bg-white shadow-sm">
      <VacioEstado
        :icono="BellOff"
        titulo="No tienes notificaciones"
        texto="Aquí aparecerán los resultados de tus evaluaciones y avisos de vencimiento."
      />
    </section>

    <section v-else class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div class="divide-y divide-slate-100">
        <article
          v-for="n in store.items"
          :key="n.id_notificacion"
          class="flex flex-col gap-3 px-4 py-3 transition-colors hover:bg-slate-50/50 sm:flex-row sm:items-center sm:justify-between"
          :class="!n.leida ? 'bg-emerald-50/40' : ''"
        >
          <div class="flex min-w-0 items-start gap-3">
            <span
              class="mt-1.5 h-2.5 w-2.5 flex-none rounded-full"
              :class="n.leida ? 'bg-slate-300' : 'bg-emerald-500 ring-4 ring-emerald-100'"
              aria-hidden="true"
            />
            <div class="min-w-0">
              <p class="m-0 text-sm font-semibold text-slate-900">{{ n.mensaje }}</p>
              <p class="m-0 mt-1 text-xs text-slate-500">{{ fechaCorta(n) }}</p>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-2 sm:justify-end">
            <span :class="[pillBase, clasesTipo[n.tipo] ?? tipoDesconocido]">{{ n.tipo }}</span>
            <button
              v-if="!n.leida"
              :class="btnSecundario"
              type="button"
              :disabled="marcando === n.id_notificacion"
              @click="marcar(n.id_notificacion)"
            >
              <Check :size="15" /> Marcar leída
            </button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>
