// frontend/tests/router.spec.ts
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { session } from '../src/api/session'
import router, { rutaPorRol } from '../src/router/index'
import { useAuthStore } from '../src/stores/auth'
import { fabricarToken } from './helpers'

const fetchMock = vi.fn<(ruta: string, init?: RequestInit) => Promise<Response>>()

function respuesta(status: number, cuerpo: unknown): Response {
  return new Response(JSON.stringify(cuerpo), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

/** EXPLICACIÓN: sesión válida (exp futuro) => los guards no disparan refresh. */
function abrirSesion(rol: 'aprendiz' | 'instructor' | 'coordinador'): void {
  session.guardar({ access_token: fabricarToken({ rol, exp: 9_999_999_999 }), refresh_token: 'r', token_type: 'bearer' })
  useAuthStore().sincronizarToken()
}

beforeEach(async () => {
  setActivePinia(createPinia())
  session.limpiar()
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
  // EXPLICACIÓN: arranca en '/registro' (pública y distinta de '/login') para
  // que push('/login') dispare de verdad el guard en vez de ser un no-op
  await router.replace('/registro')
})

describe('rutaPorRol', () => {
  it('cada rol tiene su home y sin rol cae a aprendiz', () => {
    expect(rutaPorRol('instructor')).toBe('/app/instructor/pendientes')
    expect(rutaPorRol('coordinador')).toBe('/app/coordinador/dashboard')
    expect(rutaPorRol('aprendiz')).toBe('/app/avance')
    expect(rutaPorRol(null)).toBe('/app/avance')
  })
})

describe('guards de navegación', () => {
  it('sin sesión cualquier ruta privada va al login con redirigir', async () => {
    await router.push('/app/coordinador/dashboard')

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirigir).toBe('/app/coordinador/dashboard')
  })

  it('rol equivocado redirige al home del propio rol (sin bucle)', async () => {
    abrirSesion('instructor')

    await router.push('/app/coordinador/dashboard')

    expect(router.currentRoute.value.path).toBe('/app/instructor/pendientes')
  })

  it('rol correcto accede a su ruta', async () => {
    abrirSesion('coordinador')

    await router.push('/app/coordinador/dashboard')

    expect(router.currentRoute.value.name).toBe('dashboard')
  })

  it('logueado no ve /login: cae en su home', async () => {
    abrirSesion('aprendiz')

    await router.push('/login')

    expect(router.currentRoute.value.path).toBe('/app/avance')
  })

  it("'/' resuelve al home del rol", async () => {
    abrirSesion('instructor')

    await router.push('/')

    expect(router.currentRoute.value.path).toBe('/app/instructor/pendientes')
  })

  it("'/' sin sesión va al login", async () => {
    await router.push('/')

    expect(router.currentRoute.value.name).toBe('login')
  })

  it('URL desconocida sin sesión muestra 404, no login', async () => {
    await router.push('/ruta-que-no-existe')

    expect(router.currentRoute.value.name).toBe('no-encontrado')
  })

  it('perfil y notificaciones son de acceso para cualquier rol', async () => {
    abrirSesion('aprendiz')

    await router.push('/app/perfil')

    expect(router.currentRoute.value.name).toBe('perfil')
  })

  it('access caducado + refresh rechazado => logout y al login', async () => {
    session.guardar({
      access_token: fabricarToken({ rol: 'aprendiz', exp: 100 }),
      refresh_token: 'r-viejo',
      token_type: 'bearer',
    })
    useAuthStore().sincronizarToken()
    fetchMock.mockImplementation((ruta: string) =>
      Promise.resolve(
        ruta === '/api/v1/auth/refresh' ? respuesta(401, { detail: 'Refresh inválido' }) : respuesta(200, {}),
      ),
    )

    await router.push('/app/mis-evidencias')

    expect(router.currentRoute.value.name).toBe('login')
    expect(session.access).toBeNull()
  })
})
