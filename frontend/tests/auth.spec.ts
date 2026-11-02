// frontend/tests/auth.spec.ts
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { session } from '../src/api/session'
import { useAuthStore } from '../src/stores/auth'
import { fabricarToken } from './helpers'

const fetchMock = vi.fn<(ruta: string, init?: RequestInit) => Promise<Response>>()

function respuesta(status: number, cuerpo: unknown): Response {
  return new Response(JSON.stringify(cuerpo), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

beforeEach(() => {
  setActivePinia(createPinia())
  session.limpiar()
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

describe('useAuthStore', () => {
  it('lee el rol desde el claim del JWT, sin tocar el backend', () => {
    session.guardar({ access_token: fabricarToken({ rol: 'instructor' }), refresh_token: 'r', token_type: 'bearer' })

    const auth = useAuthStore()
    auth.sincronizarToken()

    expect(auth.rol).toBe('instructor')
    expect(auth.autenticado).toBe(true)
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('sin token: sin rol, no autenticado y nombre vacío', () => {
    const auth = useAuthStore()

    expect(auth.rol).toBeNull()
    expect(auth.autenticado).toBe(false)
    expect(auth.nombre).toBe('')
  })

  it('login guarda tokens, carga el perfil y devuelve el rol', async () => {
    const token = fabricarToken({ rol: 'coordinador' })
    fetchMock.mockImplementation((ruta: string) =>
      Promise.resolve(
        ruta === '/api/v1/auth/login'
          ? respuesta(200, { access_token: token, refresh_token: 'r', token_type: 'bearer' })
          : respuesta(200, { id: 1, nombre_completo: 'Ana Pérez', rol: 'coordinador' }),
      ),
    )

    const auth = useAuthStore()
    const rol = await auth.login('ana@sena.edu.co', 'Secreta1!')

    expect(rol).toBe('coordinador')
    expect(session.access).toBe(token)
    expect(auth.nombre).toBe('Ana Pérez')
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(fetchMock.mock.calls[1]![0]).toBe('/api/v1/auth/me')
  })

  it('login manda auth:false para no rotar tokens ajenos', async () => {
    fetchMock.mockImplementation((ruta: string) =>
      Promise.resolve(
        ruta === '/api/v1/auth/login'
          ? respuesta(200, {
              access_token: fabricarToken({ rol: 'aprendiz' }),
              refresh_token: 'r1',
            })
          : respuesta(200, { id: 2, nombre_completo: 'Luis', rol: 'aprendiz' }),
      ),
    )

    await useAuthStore().login('luis@sena.edu.co', 'Secreta1!')

    expect(new Headers(fetchMock.mock.calls[0]![1]?.headers).get('Authorization')).toBeNull()
  })

  it('logout borra tokens y estado en memoria', async () => {
    session.guardar({ access_token: fabricarToken({ rol: 'aprendiz' }), refresh_token: 'r', token_type: 'bearer' })
    const auth = useAuthStore()
    auth.sincronizarToken()

    auth.logout()

    expect(auth.autenticado).toBe(false)
    expect(auth.rol).toBeNull()
    expect(session.access).toBeNull()
    expect(session.refresh).toBeNull()
  })

  it('sincronizarToken recoge el access recién roteado por client.ts', () => {
    session.guardar({ access_token: 'viejo', refresh_token: 'r', token_type: 'bearer' })
    const auth = useAuthStore()
    auth.sincronizarToken()

    session.guardar({ access_token: 'nuevo', refresh_token: 'r', token_type: 'bearer' })
    auth.sincronizarToken()

    expect(auth.token).toBe('nuevo')
  })
})
