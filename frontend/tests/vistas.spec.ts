// frontend/tests/vistas.spec.ts
/**
 * EXPLICACIÓN: tests de montaje de vistas completas con fetch simulado;
 * validan el cableado vista ↔ API ↔ store sin levantar el backend.
 */
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter, type RouteRecordRaw, type Router } from 'vue-router'

import { session } from '../src/api/session'
import LoginView from '../src/views/LoginView.vue'
import PerfilView from '../src/views/PerfilView.vue'
import AprendicesView from '../src/views/coordinador/AprendicesView.vue'
import DashboardView from '../src/views/coordinador/DashboardView.vue'
import PendientesView from '../src/views/instructor/PendientesView.vue'
import { useAuthStore } from '../src/stores/auth'
import { fabricarToken } from './helpers'

const fetchMock = vi.fn<(ruta: string, init?: RequestInit) => Promise<Response>>()

function respuesta(status: number, cuerpo: unknown): Response {
  return new Response(JSON.stringify(cuerpo), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

/** EXPLICACIÓN: router en memoria propio => sin guards/globales del router real. */
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

describe('LoginView', () => {
  const rutas: RouteRecordRaw[] = [
    { path: '/login', component: LoginView },
    { path: '/registro', component: { template: '<div />' } },
    { path: '/app/avance', component: { template: '<div />' } },
    { path: '/app/instructor/pendientes', component: { template: '<div />' } },
    { path: '/app/coordinador/dashboard', component: { template: '<div />' } },
  ]

  async function montarLogin(): Promise<{ wrapper: ReturnType<typeof mount>; router: Router }> {
    const router = routerDePrueba(rutas)
    await router.push('/login')
    await router.isReady()
    const wrapper = mount(LoginView, { global: { plugins: [router] } })
    return { wrapper, router }
  }

  it('login correcto redirige al home del rol', async () => {
    fetchMock.mockImplementation((ruta: string) =>
      Promise.resolve(
        ruta === '/api/v1/auth/login'
          ? respuesta(200, {
              access_token: fabricarToken({ rol: 'aprendiz', exp: 9_999_999_999 }),
              refresh_token: 'r',
              token_type: 'bearer',
            })
          : respuesta(200, { id: 1, nombre_completo: 'Ana Pérez', rol: 'aprendiz' }),
      ),
    )
    const { wrapper, router } = await montarLogin()

    await wrapper.find('#correo').setValue('ana@sena.edu.co')
    await wrapper.find('#contraseña').setValue('Secreta1!')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(router.currentRoute.value.path).toBe('/app/avance')
    expect(session.access).not.toBeNull()
  })

  it('401 muestra "Correo o contraseña incorrectos." sin navegar', async () => {
    fetchMock.mockResolvedValue(respuesta(401, { detail: 'Credenciales inválidas' }))
    const { wrapper, router } = await montarLogin()

    await wrapper.find('#correo').setValue('ana@sena.edu.co')
    await wrapper.find('#contraseña').setValue('mala')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.alerta-error').text()).toContain('Correo o contraseña incorrectos.')
    expect(router.currentRoute.value.path).toBe('/login')
  })
})

describe('DashboardView (coordinador)', () => {
  const stats = {
    total_evidencias: 42,
    aprobadas: 30,
    pendientes: 8,
    ajustes_requeridos: 4,
    total_aprendices: 12,
    total_instructores: 3,
    porcentaje_aprobacion: 71.43,
  }
  const alertas = [
    {
      id_evidencia: 1,
      titulo: 'Bitácora semana 3',
      fecha_deadline: '2026-11-05T00:00:00',
      dias_restantes: 3,
      estado_alerta: 'Por vencer',
      nombre_aprendiz: 'Luis Pérez',
    },
  ]

  it('pinta KPIs y alertas desde la API', async () => {
    fetchMock.mockImplementation((ruta: string) =>
      Promise.resolve(
        ruta.includes('estadisticas') ? respuesta(200, stats) : respuesta(200, alertas),
      ),
    )
    const wrapper = mount(DashboardView)
    await flushPromises()

    expect(wrapper.text()).toContain('42')
    expect(wrapper.text()).toContain('71.43%')
    expect(wrapper.text()).toContain('Bitácora semana 3')
    expect(wrapper.text()).toContain('Luis Pérez')
    expect(wrapper.text()).toContain('Por vencer')
  })

  it('sin respuesta del backend muestra alerta de error', async () => {
    fetchMock.mockRejectedValue(new Error('red caída'))
    const wrapper = mount(DashboardView)
    await flushPromises()

    expect(wrapper.find('.alerta-error').text()).toContain('No se pudo cargar el dashboard.')
  })
})

describe('PendientesView (instructor)', () => {
  const evidencia = {
    id_evidencia: 7,
    titulo: 'Bitácora sem 1',
    tipo_formato: 'Bitacora',
    ruta_archivo_pdf: '/uploads/x.pdf',
    estado: 'Pendiente',
    fecha_carga: '2026-10-01T10:00:00',
    fecha_deadline: '2026-11-10T00:00:00',
  }
  const stats = {
    total_evaluadas: 10,
    aprobadas: 6,
    ajustes_requeridos: 2,
    pendientes_por_evaluar: 5,
  }

  async function montarBandeja(): Promise<{ wrapper: ReturnType<typeof mount>; router: Router }> {
    const router = routerDePrueba([
      { path: '/pendientes', component: PendientesView },
      { path: '/app/instructor/evaluar/:id', name: 'evaluar', component: rutaVacia.component! },
    ])
    await router.push('/pendientes')
    await router.isReady()
    const wrapper = mount(PendientesView, { global: { plugins: [router] } })
    await flushPromises()
    return { wrapper, router }
  }

  it('carga bandeja, KPIs y alertas en paralelo', async () => {
    fetchMock.mockImplementation((ruta: string) => {
      if (ruta.includes('evidencias-pendientes')) {
        return Promise.resolve(
          respuesta(200, { items: [evidencia], total: 1, page: 1, page_size: 10, total_pages: 1 }),
        )
      }
      if (ruta.includes('estadisticas')) return Promise.resolve(respuesta(200, stats))
      return Promise.resolve(respuesta(200, []))
    })
    const { wrapper } = await montarBandeja()

    expect(wrapper.text()).toContain('Bitácora sem 1')
    expect(wrapper.text()).toContain('5')
    expect(wrapper.text()).toContain('Sin alertas') // ventana sin vencimientos
    expect(wrapper.find('a[href="/app/instructor/evaluar/7"]').exists()).toBe(true)
  })

  it('Siguiente pagina reconsulta con page=2', async () => {
    fetchMock.mockImplementation((ruta: string) => {
      if (ruta.includes('evidencias-pendientes')) {
        const pagina = ruta.includes('page=2') ? 2 : 1
        return Promise.resolve(
          respuesta(200, { items: [evidencia], total: 11, page: pagina, page_size: 10, total_pages: 2 }),
        )
      }
      if (ruta.includes('estadisticas')) return Promise.resolve(respuesta(200, stats))
      return Promise.resolve(respuesta(200, []))
    })
    const { wrapper } = await montarBandeja()

    const [, siguiente] = wrapper.findAll('button')
    await siguiente!.trigger('click')
    await flushPromises()

    const llamadas = fetchMock.mock.calls.map((c) => String(c[0]))
    expect(llamadas.some((r) => r.includes('evidencias-pendientes') && r.includes('page=2'))).toBe(true)
  })
})

describe('PerfilView', () => {
  const perfil = {
    id_usuario: 1,
    nombre_completo: 'Juan Pérez',
    correo_institucional: 'juan@sena.edu.co',
    rol: 'aprendiz',
  }

  it('carga /auth/me y pinta el nombre en el formulario', async () => {
    fetchMock.mockResolvedValue(respuesta(200, perfil))
    const wrapper = mount(PerfilView)
    await flushPromises()

    expect((wrapper.find('#nombre').element as HTMLInputElement).value).toBe('Juan Pérez')
    expect(wrapper.find('#centro').exists()).toBe(false)
  })

  it('rol instructor consume GET /instructor/perfil (centro + especialidad)', async () => {
    session.guardar({
      access_token: fabricarToken({ rol: 'instructor', exp: 9_999_999_999 }),
      refresh_token: 'r',
      token_type: 'bearer',
    })
    useAuthStore().sincronizarToken()
    fetchMock.mockImplementation((ruta: string) =>
      Promise.resolve(
        ruta.endsWith('/instructor/perfil')
          ? respuesta(200, {
              id_usuario: 9,
              nombre_completo: 'Docente Uno',
              correo_institucional: 'doc@sena.edu.co',
              centro_formacion: 'Centro de Bogotá',
              especialidad: 'ADS',
            })
          : respuesta(200, { ...perfil, rol: 'instructor' }),
      ),
    )
    const wrapper = mount(PerfilView)
    await flushPromises()

    expect((wrapper.find('#centro').element as HTMLInputElement).value).toBe('Centro de Bogotá')
    expect((wrapper.find('#especialidad').element as HTMLInputElement).value).toBe('ADS')
    expect(fetchMock.mock.calls.some((c) => String(c[0]).endsWith('/instructor/perfil'))).toBe(true)
  })

  it('contraseña nueva corta falla en cliente sin tocar la API', async () => {
    fetchMock.mockResolvedValue(respuesta(200, perfil))
    const wrapper = mount(PerfilView)
    await flushPromises()
    fetchMock.mockClear()

    const forms = wrapper.findAll('form')
    await forms[1]!.find('#actual').setValue('Actual123!')
    await forms[1]!.find('#nueva').setValue('corta')
    await forms[1]!.find('#confirmar').setValue('corta')
    await forms[1]!.trigger('submit')
    await flushPromises()

    expect(wrapper.find('.alerta-error').text()).toContain('al menos 8 caracteres')
    expect(fetchMock).not.toHaveBeenCalled()
  })
})

describe('AprendicesView (coordinador)', () => {
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
    total: 1,
    page: 1,
    page_size: 10,
    total_pages: 1,
  }

  it('renderiza la tabla desde items y muestra el total paginado', async () => {
    fetchMock.mockResolvedValue(respuesta(200, pagina))
    const wrapper = mount(AprendicesView)
    await flushPromises()

    expect(wrapper.text()).toContain('Ana Gómez')
    expect(wrapper.text()).toContain('66.67 %')
    expect(wrapper.text()).toContain('Página 1 de 1')
  })

  it('el filtro de programa viaja en la querystring', async () => {
    fetchMock.mockResolvedValue(respuesta(200, pagina))
    const wrapper = mount(AprendicesView)
    await flushPromises()

    await wrapper.find('#programa').setValue('ADSO')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const ultima = String(fetchMock.mock.calls.at(-1)![0])
    expect(ultima).toContain('/api/v1/coordinador/aprendices?')
    expect(ultima).toContain('programa=ADSO')
    expect(ultima).toContain('page=1')
  })
})
