<script setup lang="ts">
// src/views/NotificacionesView.vue
// EXPLICACIÓN: central de avisos de TODOS los roles (mismo endpoint por id_usuario)
import { onMounted, ref } from 'vue'

import type { Notificacion } from '../api/types'
import { useNotificacionesStore } from '../stores/notificaciones'

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

const clasesTipo: Record<string, string> = {
  evaluacion: 'badge badge-pendiente',
  vencimiento: 'badge badge-vencida',
  sistema: 'badge badge-aprobada',
}
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center">
      <h1>Notificaciones</h1>
      <button
        class="btn"
        type="button"
        :disabled="store.noLeidas === 0"
        @click="store.marcarTodas()"
      >
        Marcar todas como leídas
      </button>
    </div>

    <div v-if="store.items.length === 0" class="tarjeta vacio">
      <h3>No tienes notificaciones</h3>
      <p>Aquí aparecerán los resultados de tus evaluaciones y avisos de vencimiento.</p>
    </div>

    <div v-else class="tabla-contenedor">
      <div
        v-for="n in store.items"
        :key="n.id_notificacion"
        class="lista-item"
        :class="{ 'sin-leer': !n.leida }"
      >
        <div>
          <h4>{{ n.mensaje }}</h4>
          <p>{{ fechaCorta(n) }}</p>
        </div>
        <div style="display: flex; gap: 0.5rem; align-items: center">
          <span :class="clasesTipo[n.tipo] ?? 'badge badge-pendiente'">{{ n.tipo }}</span>
          <button
            v-if="!n.leida"
            class="btn btn-suave"
            type="button"
            :disabled="marcando === n.id_notificacion"
            @click="marcar(n.id_notificacion)"
          >
            Marcar leída
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
