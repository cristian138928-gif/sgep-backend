// frontend/tests/bitacoras.spec.ts
/**
 * EXPLICACIÓN: vista dedicada de bitácoras del coordinador — query con
 * tipo_formato fijo, badges de estado según UI_GUIDELINES.md y paginación.
 */
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import BitacorasView from '../src/views/coordinador/BitacorasView.vue'

const fetchMock = vi.fn<(ruta: string, init?: RequestInit) => Promise<Response>>()

function respuesta(status: number, cuerpo: unknown): Response {
  return new Response(JSON.stringify(cuerpo), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function fabricarPagina(items: Record<string, unknown>[], totalPages = 1) {
  return { items, total: items.length, page: 1, page_size: 10, total_pages: totalPages }
}

const bitacora = {
  id_evidencia: 12,
  titulo: 'Bitácora sem 4',
  tipo_formato: 'Bitacora',
  ruta_archivo_pdf: '/uploads/b4.pdf',
  estado: 'Pendiente',
  fecha_carga: '2026-10-20T09:00:00',
  fecha_deadline: '2026-11-15T00:00:00',
}

beforeEach(() => {
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

describe('BitacorasView (coordinador)', () => {
  it('lista bitácoras con tipo_formato fijo en la query', async () => {
    fetchMock.mockResolvedValue(respuesta(200, fabricarPagina([bitacora])))
    const wrapper = mount(BitacorasView)
    await flushPromises()

    expect(wrapper.text()).toContain('Bitácora sem 4')
    const llamada = String(fetchMock.mock.calls[0]![0])
    expect(llamada).toContain('tipo_formato=Bitacora')
    expect(llamada).toContain('page=1')
    expect(llamada).toContain('page_size=10')
  })

  it('pinta badges con la paleta de la guía (emerald/amber/rose)', async () => {
    fetchMock.mockResolvedValue(
      respuesta(
        200,
        fabricarPagina([
          bitacora,
          { ...bitacora, id_evidencia: 13, estado: 'Aprobada' },
          { ...bitacora, id_evidencia: 14, estado: 'Ajuste Requerido' },
        ]),
      ),
    )
    const wrapper = mount(BitacorasView)
    await flushPromises()

    const badgeDe = (estado: string) =>
      wrapper.findAll('span').find((s) => s.text().includes(estado))!

    expect(badgeDe('Pendiente').classes()).toContain('bg-amber-50')
    expect(badgeDe('Pendiente').classes()).toContain('border-amber-200')
    expect(badgeDe('Aprobada').classes()).toContain('bg-emerald-50')
    expect(badgeDe('Aprobada').classes()).toContain('text-emerald-700')
    expect(badgeDe('Ajuste Requerido').classes()).toContain('bg-rose-50')
    expect(badgeDe('Ajuste Requerido').classes()).toContain('border-rose-200')
  })

  it('aplicar filtros mantiene el tipo y reinicia la página', async () => {
    fetchMock.mockImplementation(() => Promise.resolve(respuesta(200, fabricarPagina([bitacora]))))
    const wrapper = mount(BitacorasView)
    await flushPromises()

    await wrapper.find('#estado').setValue('Aprobada')
    await wrapper.find('#desde').setValue('2026-10-01')
    await wrapper.findAll('button').find((b) => b.text().includes('Aplicar filtros'))!.trigger('click')
    await flushPromises()

    const ultima = String(fetchMock.mock.calls.at(-1)![0])
    expect(ultima).toContain('tipo_formato=Bitacora')
    expect(ultima).toContain('estado=Aprobada')
    expect(ultima).toContain('fecha_desde=2026-10-01')
    expect(ultima).toContain('page=1')
  })

  it('la paginación avanza a la página 2', async () => {
    fetchMock.mockImplementation(() =>
      Promise.resolve(respuesta(200, fabricarPagina([bitacora], 2))),
    )
    const wrapper = mount(BitacorasView)
    await flushPromises()

    await wrapper.findAll('button').find((b) => b.text().includes('Siguiente'))!.trigger('click')
    await flushPromises()

    expect(String(fetchMock.mock.calls.at(-1)![0])).toContain('page=2')
  })

  it('colección vacía muestra el estado vacío de la guía', async () => {
    fetchMock.mockResolvedValue(respuesta(200, fabricarPagina([])))
    const wrapper = mount(BitacorasView)
    await flushPromises()

    expect(wrapper.text()).toContain('Sin bitácoras registradas')
  })

  it('fallo de red muestra alerta en rose sin romper el panel', async () => {
    fetchMock.mockResolvedValue(respuesta(500, { detail: 'boom' }))
    const wrapper = mount(BitacorasView)
    await flushPromises()

    expect(wrapper.find('[role="alert"]').text()).toContain('No se pudieron cargar')
  })
})
