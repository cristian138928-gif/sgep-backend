// frontend/tests/client.spec.ts
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { api, ApiError, intentarRefrescar, nombreSeguro } from '../src/api/client'
import { session } from '../src/api/session'

/** EXPLICACIÓN: Response falso con JSON => evita red real y controla status/body. */
function respuesta(status: number, cuerpo?: unknown): Response {
  if (cuerpo === undefined) return new Response(null, { status })
  return new Response(JSON.stringify(cuerpo), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const fetchMock = vi.fn<(ruta: string, init?: RequestInit) => Promise<Response>>()

beforeEach(() => {
  session.limpiar()
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('nombreSeguro', () => {
  it('reemplaza caracteres prohibidos en nombres de archivo', () => {
    expect(nombreSeguro('F023: firma / 2026')).toBe('F023_ firma _ 2026')
  })

  it('recorta a 150 caracteres conservando la extensión', () => {
    const largo = `${'a'.repeat(200)}.pdf`
    const resultado = nombreSeguro(largo)

    expect(resultado).toHaveLength(150)
    expect(resultado.endsWith('.pdf')).toBe(true)
  })

  it('vacío o solo espacios cae a un nombre por defecto', () => {
    expect(nombreSeguro('   ')).toBe('descarga')
  })
})

describe('api()', () => {
  it('envía Authorization con el access token y Content-Type JSON', async () => {
    session.guardar({ access_token: 'tok-1', refresh_token: 'r', token_type: 'bearer' })
    fetchMock.mockResolvedValue(respuesta(200, { ok: true }))

    await api<{ ok: boolean }>('/api/v1/x', { method: 'POST', body: '{"a":1}' })

    const [ruta, init] = fetchMock.mock.calls[0]!
    const cabeceras = new Headers(init?.headers)
    expect(ruta).toBe('/api/v1/x')
    expect(cabeceras.get('Authorization')).toBe('Bearer tok-1')
    expect(cabeceras.get('Content-Type')).toBe('application/json')
  })

  it('auth:false no manda Authorization (login/registro)', async () => {
    session.guardar({ access_token: 'tok-1', refresh_token: 'r', token_type: 'bearer' })
    fetchMock.mockResolvedValue(respuesta(200, { ok: true }))

    await api('/api/v1/auth/login', { method: 'POST', auth: false, body: '{}' })

    expect(new Headers(fetchMock.mock.calls[0]![1]?.headers).get('Authorization')).toBeNull()
  })

  it('no pisa el Content-Type si la ruta ya trae uno (multipart)', async () => {
    session.guardar({ access_token: 'tok-1', refresh_token: 'r', token_type: 'bearer' })
    fetchMock.mockResolvedValue(respuesta(200, { ok: true }))

    await api('/api/v1/evidencias/upload', {
      method: 'POST',
      body: new FormData(),
      headers: { 'Content-Type': 'application/pdf' },
    })

    expect(new Headers(fetchMock.mock.calls[0]![1]?.headers).get('Content-Type')).toBe('application/pdf')
  })

  it('204 resuelve undefined sin intentar leer JSON', async () => {
    fetchMock.mockResolvedValue(respuesta(204))

    await expect(api('/api/v1/x')).resolves.toBeUndefined()
  })

  it('lanza ApiError con el detail del backend', async () => {
    fetchMock.mockResolvedValue(respuesta(400, { detail: 'Archivo mayor a 5MB' }))

    const error = await api('/api/v1/x').catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).status).toBe(400)
    expect((error as ApiError).detail).toBe('Archivo mayor a 5MB')
  })

  it('detalle no string (validación Pydantic) se serializa a texto', async () => {
    fetchMock.mockResolvedValue(
      respuesta(422, { detail: [{ msg: 'campo obligatorio', loc: ['body', 'titulo'] }] }),
    )

    const error = await api('/api/v1/x').catch((e: unknown) => e)

    expect((error as ApiError).detail).toContain('campo obligatorio')
  })
})

describe('rotación de refresh (mutex)', () => {
  it('N peticiones en 401 disparan UN solo refresh', async () => {
    let refrescos = 0
    session.guardar({ access_token: 'viejo', refresh_token: 'r', token_type: 'bearer' })

    fetchMock.mockImplementation((ruta: string, init?: RequestInit) => {
      if (ruta === '/api/v1/auth/refresh') {
        refrescos += 1
        return Promise.resolve(respuesta(200, { access_token: 'nuevo', refresh_token: 'r-nuevo', token_type: 'bearer' }))
      }
      const auth = new Headers(init?.headers).get('Authorization')
      // EXPLICACIÓN: 401 salvo que el cliente ya rote el token => simula expiración
      return auth === 'Bearer nuevo'
        ? Promise.resolve(respuesta(200, { ok: true }))
        : Promise.resolve(respuesta(401, { detail: 'Token expirado' }))
    })

    const resultados = await Promise.all(
      Array.from({ length: 10 }, () => api<{ ok: boolean }>('/api/v1/datos')),
    )

    expect(refrescos).toBe(1)
    expect(resultados).toHaveLength(10)
    expect(session.access).toBe('nuevo')
    expect(session.refresh).toBe('r-nuevo')
  })

  it('refresh rechazado limpia la sesión y propaga el 401', async () => {
    session.guardar({ access_token: 'viejo', refresh_token: 'r', token_type: 'bearer' })
    fetchMock.mockImplementation((ruta: string) =>
      Promise.resolve(
        ruta === '/api/v1/auth/refresh'
          ? respuesta(401, { detail: 'Refresh inválido' })
          : respuesta(401, { detail: 'Token expirado' }),
      ),
    )

    await expect(api('/api/v1/datos')).rejects.toThrow('Token expirado')
    expect(session.access).toBeNull()
    expect(session.refresh).toBeNull()
  })

  it('intentarRefrescar devuelve false sin refresh token (sin red)', async () => {
    expect(await intentarRefrescar()).toBe(false)
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
