// frontend/tests/notificaciones.spec.ts
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { Notificacion } from '../src/api/types'
import { useNotificacionesStore } from '../src/stores/notificaciones'

const fetchMock = vi.fn<(ruta: string, init?: RequestInit) => Promise<Response>>()

function notificacion(id: number, leida: boolean): Notificacion {
  return {
    id_notificacion: id,
    mensaje: `Mensaje ${id}`,
    tipo: 'evaluacion',
    id_evidencia: null,
    leida,
    fecha_creacion: '2026-10-27T10:00:00',
  }
}

function respuesta(cuerpo: unknown): Response {
  return new Response(JSON.stringify(cuerpo), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })
}

/** EXPLICACIÓN: promesa que el test libera a mano => simula red lenta en vuelo. */
function pendiente(): { resolver: () => void; promesa: Promise<void> } {
  let resolver!: () => void
  const promesa = new Promise<void>((r) => {
    resolver = r
  })
  return { resolver, promesa }
}

beforeEach(() => {
  setActivePinia(createPinia())
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

describe('useNotificacionesStore', () => {
  it('cuenta no leídas y acota el badge a 9+', () => {
    const store = useNotificacionesStore()
    store.items = [notificacion(1, false), notificacion(2, true)]

    expect(store.noLeidas).toBe(1)
    expect(store.badge).toBe('1')

    store.items = Array.from({ length: 12 }, (_, i) => notificacion(i, false))
    expect(store.badge).toBe('9+')
  })

  it('refrescar reemplaza la lista y apaga el flag de carga', async () => {
    fetchMock.mockResolvedValue(respuesta([notificacion(1, false)]))
    const store = useNotificacionesStore()

    await store.refrescar()

    expect(store.items).toHaveLength(1)
    expect(store.cargando).toBe(false)
  })

  it('refrescar concurrente no duplica la petición (guard cargando)', async () => {
    const { resolver, promesa } = pendiente()
    fetchMock.mockImplementation(() => promesa.then(() => respuesta([notificacion(1, false)])))
    const store = useNotificacionesStore()

    const primera = store.refrescar()
    const segunda = store.refrescar()
    resolver()
    await Promise.all([primera, segunda])

    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('marcarLeida hace POST y marca solo esa en local', async () => {
    fetchMock.mockResolvedValue(respuesta({ ok: true }))
    const store = useNotificacionesStore()
    store.items = [notificacion(1, false), notificacion(2, false)]

    await store.marcarLeida(1)

    expect(store.items[0]!.leida).toBe(true)
    expect(store.items[1]!.leida).toBe(false)
    expect(fetchMock.mock.calls[0]![0]).toBe('/api/v1/notificaciones/1/marcar-leida')
    expect(fetchMock.mock.calls[0]![1]?.method).toBe('POST')
  })

  it('marcarTodas envía una sola petición y deja todo leído', async () => {
    fetchMock.mockResolvedValue(respuesta({ ok: true }))
    const store = useNotificacionesStore()
    store.items = [notificacion(1, false), notificacion(2, false)]

    await store.marcarTodas()

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(store.noLeidas).toBe(0)
    expect(store.badge).toBe('0')
  })

  it('limpiar vacía la lista (logout)', () => {
    const store = useNotificacionesStore()
    store.items = [notificacion(1, false)]

    store.limpiar()

    expect(store.items).toHaveLength(0)
  })
})
