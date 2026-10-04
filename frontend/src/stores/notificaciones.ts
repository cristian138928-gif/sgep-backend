// src/stores/notificaciones.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { api } from '../api/client'
import type { Notificacion } from '../api/types'

export const useNotificacionesStore = defineStore('notificaciones', () => {
  const items = ref<Notificacion[]>([])
  const cargando = ref(false)

  const noLeidas = computed(() => items.value.filter((n) => !n.leida).length)
  /** Sufijo para el badge: 9+ en vez de un número infinito en la UI */
  const badge = computed(() => (noLeidas.value > 9 ? '9+' : String(noLeidas.value)))

  async function refrescar(): Promise<void> {
    // EXPLICACIÓN: sesión iniciada obligatoria => ignorar 401 en poll del layout
    if (cargando.value) return
    cargando.value = true
    try {
      items.value = await api<Notificacion[]>('/api/v1/notificaciones')
    } finally {
      cargando.value = false
    }
  }

  async function marcarLeida(id: number): Promise<void> {
    // EXPLICACIÓN: POST (no PUT) porque el backend define POST /{id}/marcar-leida
    await api(`/api/v1/notificaciones/${id}/marcar-leida`, { method: 'POST' })
    const n = items.value.find((x) => x.id_notificacion === id)
    if (n) n.leida = true
  }

  async function marcarTodas(): Promise<void> {
    await api('/api/v1/notificaciones/marcar-todas-leidas', { method: 'POST' })
    items.value.forEach((n) => {
      n.leida = true
    })
  }

  function limpiar(): void {
    items.value = []
  }

  return { items, cargando, noLeidas, badge, refrescar, marcarLeida, marcarTodas, limpiar }
})
