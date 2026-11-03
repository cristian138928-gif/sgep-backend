// frontend/tests/vistas2.spec.ts
/**
 * EXPLICACIÓN: segunda tanda de montajes de vista — registro, notificaciones,
 * subida de evidencias, evaluación, historial, filtros y asignaciones RF05.
 */
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter, type RouteRecordRaw, type Router } from 'vue-router'

import { session } from '../src/api/session'
import RegistroView from '../src/views/RegistroView.vue'
import NotificacionesView from '../src/views/NotificacionesView.vue'
import MisEvidenciasView from '../src/views/aprendiz/MisEvidenciasView.vue'
import AsignacionesView from '../src/views/coordinador/AsignacionesView.vue'
import EvidenciasView from '../src/views/coordinador/EvidenciasView.vue'
import EvaluarView from '../src/views/instructor/EvaluarView.vue'
import HistorialView from '../src/views/instructor/HistorialView.vue'
import { fabricarToken } from './helpers'

const fetchMock = vi.fn<(ruta: string, init?: RequestInit) => Promise<Response>>()

function respuesta(status: number, cuerpo: unknown): Response {
  return new Response(JSON.stringify(cuerpo), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function routerDePrueba(rutas: RouteRecordRaw[]): Router {
  return createRouter({ history: createMemoryHistory(), routes: rutas })
}

const rutaVacia: RouteRecordRaw = { path: '/x', component: { template: '<div />' } }

beforeEach(() => {
  setActivePinia(createPinia())
  session.limpiar()
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

describe('RegistroView', () => {
  const rutas: RouteRecordRaw[] = [
    { path: '/registro', component: RegistroView },
    { path: '/login', component: { template: '<div />' } },
    { path: '/app/avance', component: { template: '<div />' } },
    { path: '/app/instructor/pendientes', component: { template: '<div />' } },
    { path: '/app/coordinador/dashboard', component: { template: '<div />' } },
  ]

  async function montarRegistro(): Promise<{ wrapper: ReturnType<typeof mount>; router: Router }> {
    const router = routerDePrueba(rutas)
    await router.push('/registro')
    await router.isReady()
    const wrapper = mount(RegistroView, { global: { plugins: [router] } })
    return { wrapper, router }
  }

  it('cambia los campos según la pestaña de rol', async () => {
    const { wrapper } = await montarRegistro()

    expect(wrapper.find('#ficha').exists()).toBe(true)
    await wrapper.findAll('.pestanas button')[1]!.trigger('click')

    expect(wrapper.find('#ficha').exists()).toBe(false)
    expect(wrapper.find('#centro').exists()).toBe(true)
  })

  it('claves distintas bloquean el envío sin tocar la API', async () => {
    const { wrapper } = await montarRegistro()

    await wrapper.find('#contraseña').setValue('Secreta1!')
    await wrapper.find('#confirmar').setValue('OtraCosa1!')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.alerta-error').text()).toContain('no coinciden')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('registro aprendiz exitoso: POST + /me + redirige al home', async () => {
    fetchMock.mockImplementation((ruta: string) =>
      Promise.resolve(
        ruta === '/api/v1/auth/registro'
          ? respuesta(201, {
              access_token: fabricarToken({ rol: 'aprendiz', exp: 9_999_999_999 }),
              refresh_token: 'r',
              token_type: 'bearer',
            })
          : respuesta(200, { id: 1, nombre_completo: 'Ana', rol: 'aprendiz' }),
      ),
    )
    const { wrapper, router } = await montarRegistro()

    await wrapper.find('#nombre').setValue('Ana Pérez')
    await wrapper.find('#correo').setValue('ana@sena.edu.co')
    await wrapper.find('#documento').setValue('1012345678')
    await wrapper.find('#ficha').setValue('2456789')
    await wrapper.find('#programa').setValue('ADSO')
    await wrapper.find('#contraseña').setValue('Secreta1!')
    await wrapper.find('#confirmar').setValue('Secreta1!')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/app/avance')
    const rutasLlamadas = fetchMock.mock.calls.map((c) => String(c[0]))
    expect(rutasLlamadas).toContain('/api/v1/auth/registro')
    expect(rutasLlamadas).toContain('/api/v1/auth/me')
  })

  it('409 muestra "ya está registrado"', async () => {
    fetchMock.mockResolvedValue(respuesta(409, { detail: 'Correo duplicado' }))
    const { wrapper } = await montarRegistro()

    await wrapper.find('#nombre').setValue('Ana Pérez')
    await wrapper.find('#correo').setValue('ana@sena.edu.co')
    await wrapper.find('#documento').setValue('1012345678')
    await wrapper.find('#ficha').setValue('2456789')
    await wrapper.find('#programa').setValue('ADSO')
    await wrapper.find('#contraseña').setValue('Secreta1!')
    await wrapper.find('#confirmar').setValue('Secreta1!')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.alerta-error').text()).toContain('ya está registrado')
  })
})

describe('NotificacionesView', () => {
  const notis = [
    {
      id_notificacion: 1,
      mensaje: 'Tu evidencia fue aprobada',
      tipo: 'evaluacion',
      id_evidencia: 5,
      leida: false,
      fecha_creacion: '2026-11-01T10:00:00',
    },
    {
      id_notificacion: 2,
      mensaje: 'Vence en 3 días: Bitácora sem 2',
      tipo: 'vencimiento',
      id_evidencia: 6,
      leida: true,
      fecha_creacion: '2026-10-30T08:00:00',
    },
  ]

  it('lista avisos y muestra el contador de no leídas', async () => {
    // EXPLICACIÓN: Response es de un solo uso => fabricar uno por llamada
    fetchMock.mockImplementation(() => Promise.resolve(respuesta(200, notis)))
    const wrapper = mount(NotificacionesView)
    await flushPromises()

    expect(wrapper.text()).toContain('Tu evidencia fue aprobada')
    expect(wrapper.text()).toContain('1 sin leer')
    // EXPLICACIÓN: la leída no ofrece botón de marcar
    expect(wrapper.findAll('button').some((b) => b.text().includes('Marcar leída'))).toBe(true)
  })

  it('marcar leída hace POST y actualiza el contador al instante', async () => {
    fetchMock.mockImplementation(() => Promise.resolve(respuesta(200, notis)))
    const wrapper = mount(NotificacionesView)
    await flushPromises()

    const btnMarcar = wrapper.findAll('button').find((b) => b.text().includes('Marcar leída'))!
    await btnMarcar.trigger('click')
    await flushPromises()

    expect(fetchMock.mock.calls.some((c) => String(c[0]).includes('/marcar-leida'))).toBe(true)
    expect(wrapper.text()).toContain('0 sin leer')
    expect(wrapper.findAll('button').some((b) => b.text().includes('Marcar leída'))).toBe(false)
  })
})

describe('MisEvidenciasView (aprendiz)', () => {
  const evidencia = {
    id_evidencia: 9,
    titulo: 'Bitácora sem 4',
    tipo_formato: 'Bitacora',
    ruta_archivo_pdf: '/uploads/b4.pdf',
    estado: 'Pendiente',
    fecha_carga: '2026-10-20T09:00:00',
    fecha_deadline: '2026-11-15T00:00:00',
  }

  it('renderiza la tabla de evidencias propias', async () => {
    fetchMock.mockResolvedValue(respuesta(200, [evidencia]))
    const wrapper = mount(MisEvidenciasView)
    await flushPromises()

    expect(wrapper.text()).toContain('Bitácora sem 4')
    expect(wrapper.text()).toContain('Pendiente')
  })

  it('subir sin archivo muestra error cliente y no llama a la API', async () => {
    fetchMock.mockResolvedValue(respuesta(200, [evidencia]))
    const wrapper = mount(MisEvidenciasView)
    await flushPromises()
    fetchMock.mockClear()

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.alerta-error').text()).toContain('Selecciona un archivo PDF')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('subir con PDF envía multipart y recarga la lista', async () => {
    fetchMock.mockImplementation((ruta: string) =>
      Promise.resolve(
        ruta.includes('upload') ? respuesta(201, evidencia) : respuesta(200, [evidencia]),
      ),
    )
    const wrapper = mount(MisEvidenciasView)
    await flushPromises()

    const archivo = new File(['%PDF-falso'], 'bitacora.pdf', { type: 'application/pdf' })
    const input = wrapper.find('#archivo').element as HTMLInputElement
    Object.defineProperty(input, 'files', { value: [archivo], configurable: true })
    await wrapper.find('#archivo').trigger('change')
    await wrapper.find('#titulo').setValue('Bitácora sem 4')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const llamada = fetchMock.mock.calls.find((c) => String(c[0]).includes('upload'))!
    expect(String(llamada[0])).toBe('/api/v1/evidencias/upload')
    expect(llamada[1]?.body).toBeInstanceOf(FormData)
    expect(wrapper.find('.alerta-info').text()).toContain('subida correctamente')
  })
})

describe('EvaluarView (instructor)', () => {
  const meta = {
    id_evidencia: 7,
    titulo: 'Bitácora sem 1',
    tipo_formato: 'Bitacora',
    ruta_archivo_pdf: '/uploads/x.pdf',
    estado: 'Pendiente',
    fecha_carga: '2026-10-01T10:00:00',
    fecha_deadline: '2026-11-10T00:00:00',
  }

  async function montarEvaluar(): Promise<{ wrapper: ReturnType<typeof mount>; router: Router }> {
    const router = routerDePrueba([
      { path: '/pendientes', name: 'pendientes', component: rutaVacia.component! },
      { path: '/evaluar/:id', name: 'evaluar', component: EvaluarView, props: true },
    ])
    await router.push('/evaluar/7')
    await router.isReady()
    const wrapper = mount(EvaluarView, {
      props: { id: '7' },
      global: { plugins: [router] },
    })
    await flushPromises()
    return { wrapper, router }
  }

  it('sin history.state baja los metadatos por GET', async () => {
    fetchMock.mockResolvedValue(respuesta(200, meta))
    const { wrapper } = await montarEvaluar()

    expect(wrapper.text()).toContain('Bitácora sem 1')
    expect(fetchMock.mock.calls.some((c) => String(c[0]).includes('/evidencias/7'))).toBe(true)
  })

  it('observaciones cortas bloquean el PUT', async () => {
    fetchMock.mockResolvedValue(respuesta(200, meta))
    const { wrapper } = await montarEvaluar()
    fetchMock.mockClear()

    await wrapper.find('#observaciones').setValue('corta')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.alerta-error').text()).toContain('al menos 10 caracteres')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('evaluación válida hace PUT y vuelve a la bandeja', async () => {
    fetchMock.mockImplementation((_ruta: string, init?: RequestInit) =>
      Promise.resolve(
        init?.method === 'PUT'
          ? respuesta(200, { id_retroalimentacion: 1, estado_evaluacion: 'Aprobada' })
          : respuesta(200, meta),
      ),
    )
    const { wrapper, router } = await montarEvaluar()

    await wrapper.find('#observaciones').setValue('Todo correcto, buen trabajo aprendiz.')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const put = fetchMock.mock.calls.find((c) => c[1]?.method === 'PUT')!
    expect(String(put[0])).toBe('/api/v1/instructor/evaluar/7')
    expect(router.currentRoute.value.name).toBe('pendientes')
  })
})

describe('HistorialView (instructor)', () => {
  const retro = {
    id_retroalimentacion: 3,
    id_evidencia: 12,
    id_instructor: 2,
    observaciones: 'Falta firmar la bitácora.',
    estado_evaluacion: 'Ajuste Requerido',
    fecha_revision: '2026-10-28T15:00:00',
  }

  it('pinta filas del historial paginado', async () => {
    fetchMock.mockResolvedValue(
      respuesta(200, { items: [retro], total: 1, page: 1, page_size: 10, total_pages: 1 }),
    )
    const wrapper = mount(HistorialView)
    await flushPromises()

    expect(wrapper.text()).toContain('Falta firmar la bitácora.')
    expect(wrapper.text()).toContain('Ajuste Requerido')
    expect(wrapper.text()).toContain('Página 1 de 1')
  })

  it('colección vacía muestra el estado vacío', async () => {
    fetchMock.mockResolvedValue(
      respuesta(200, { items: [], total: 0, page: 1, page_size: 10, total_pages: 1 }),
    )
    const wrapper = mount(HistorialView)
    await flushPromises()

    expect(wrapper.text()).toContain('Sin evaluaciones registradas')
  })
})

describe('EvidenciasView (coordinador)', () => {
  const pagina = {
    items: [
      {
        id_evidencia: 4,
        titulo: 'F023 firmado',
        tipo_formato: 'F023',
        ruta_archivo_pdf: '/uploads/f.pdf',
        estado: 'Aprobada',
        fecha_carga: '2026-10-15T12:00:00',
        fecha_deadline: null,
      },
    ],
    total: 1,
    page: 1,
    page_size: 10,
    total_pages: 1,
  }

  it('renderiza la tabla con los filtros por defecto', async () => {
    fetchMock.mockResolvedValue(respuesta(200, pagina))
    const wrapper = mount(EvidenciasView)
    await flushPromises()

    expect(wrapper.text()).toContain('F023 firmado')
    expect(String(fetchMock.mock.calls[0]![0])).toContain('page=1')
    expect(String(fetchMock.mock.calls[0]![0])).toContain('page_size=10')
  })

  it('aplicar filtros agrega estado y fechas a la querystring', async () => {
    fetchMock.mockImplementation(() => Promise.resolve(respuesta(200, pagina)))
    const wrapper = mount(EvidenciasView)
    await flushPromises()

    await wrapper.find('#estado').setValue('Aprobada')
    await wrapper.find('#desde').setValue('2026-10-01')
    await wrapper.findAll('button').find((b) => b.text().includes('Aplicar filtros'))!.trigger('click')
    await flushPromises()

    const ultima = String(fetchMock.mock.calls.at(-1)![0])
    expect(ultima).toContain('estado=Aprobada')
    expect(ultima).toContain('fecha_desde=2026-10-01')
    expect(ultima).toContain('page=1')
  })
})

describe('AsignacionesView (RF05 — regresión Pagina)', () => {
  const pagina = {
    items: [
      {
        id_usuario: 5,
        nombre_completo: 'Ana Gómez',
        numero_ficha: '2456789',
        programa: 'ADSO',
        total_evidencias: 3,
        aprobadas: 2,
        porcentaje_avance: 66.67,
      },
    ],
    total: 11,
    page: 1,
    page_size: 10,
    total_pages: 2,
  }
  const instructores = [
    {
      id_usuario: 2,
      nombre_completo: 'Instructor Uno',
      correo_institucional: 'i@sena.edu.co',
      centro_formacion: 'Centro X',
      especialidad: 'ADS',
    },
  ]

  it('consume .items de la respuesta paginada (no la lista cruda)', async () => {
    fetchMock.mockImplementation((ruta: string) => {
      if (ruta.includes('aprendices')) return Promise.resolve(respuesta(200, pagina))
      if (ruta.includes('instructores')) return Promise.resolve(respuesta(200, instructores))
      return Promise.resolve(respuesta(200, []))
    })
    const wrapper = mount(AsignacionesView)
    await flushPromises()

    expect(wrapper.text()).toContain('Ana Gómez')
    expect(wrapper.text()).toContain('Sin asignar')
    expect(wrapper.text()).toContain('Página 1 de 2')
  })

  it('el listado pedía page=1 al servidor', async () => {
    fetchMock.mockImplementation((ruta: string) => {
      if (ruta.includes('aprendices')) return Promise.resolve(respuesta(200, pagina))
      if (ruta.includes('instructores')) return Promise.resolve(respuesta(200, instructores))
      return Promise.resolve(respuesta(200, []))
    })
    mount(AsignacionesView)
    await flushPromises()

    const llamada = fetchMock.mock.calls.find((c) => String(c[0]).includes('aprendices'))!
    expect(String(llamada[0])).toContain('page=1')
    expect(String(llamada[0])).toContain('page_size=10')
  })
})
