// src/api/client.ts
/**
 * Cliente HTTP tipado con rotación de refresh tokens.
 *
 * EXPLICACIÓN: ante un 401 se refresca UNA sola vez (mutex compartido)
 * y se reintenta la petición original; el resto del código ignora JWT.
 */

import { session } from './session'
import type { ParTokens } from './types'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

async function parsearError(res: Response): Promise<ApiError> {
  let detalle = res.statusText || 'Error de red'
  try {
    const cuerpo = (await res.json()) as { detail?: unknown }
    if (typeof cuerpo.detail === 'string') detalle = cuerpo.detail
    else if (cuerpo.detail) detalle = JSON.stringify(cuerpo.detail)
  } catch {
    // EXPLICACIÓN: Respuesta sin JSON (HTML de proxy/500) => mensaje genérico
  }
  return new ApiError(res.status, detalle)
}

let enCurso: Promise<boolean> | null = null

export async function intentarRefrescar(): Promise<boolean> {
  const refresh = session.refresh
  if (!refresh) return false
  try {
    const res = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    })
    if (!res.ok) {
      session.limpiar()
      return false
    }
    session.guardar((await res.json()) as ParTokens)
    return true
  } catch {
    return false
  }
}

interface OpcionesApi extends RequestInit {
  /** Enviar Authorization (por defecto true) */
  auth?: boolean
}

export async function api<T>(ruta: string, opciones: OpcionesApi = {}): Promise<T> {
  const { auth = true, headers, ...resto } = opciones

  const ejecutar = async (): Promise<Response> => {
    const cabeceras = new Headers(headers)
    if (auth && session.access) {
      cabeceras.set('Authorization', `Bearer ${session.access}`)
    }
    if (
      resto.body &&
      !(resto.body instanceof FormData) &&
      !cabeceras.has('Content-Type')
    ) {
      cabeceras.set('Content-Type', 'application/json')
    }
    return fetch(ruta, { ...resto, headers: cabeceras })
  }

  let res = await ejecutar()

  if (res.status === 401 && auth && session.refresh) {
    // EXPLICACIÓN: mutex => 10 peticiones en 401 disparan UN refresh, no 10
    enCurso ??= intentarRefrescar().finally(() => {
      enCurso = null
    })
    if (await enCurso) res = await ejecutar()
  }

  if (!res.ok) throw await parsearError(res)
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

/** Descarga un archivo protegido (CSV/PDF) y lo guarda con nombre sugerido. */
export async function descargar(ruta: string, nombreArchivo: string): Promise<void> {
  const cabeceras: Record<string, string> = {}
  if (session.access) cabeceras.Authorization = `Bearer ${session.access}`

  const res = await fetch(ruta, { headers: cabeceras })
  if (!res.ok) throw await parsearError(res)

  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombreArchivo
  enlace.click()
  URL.revokeObjectURL(url)
}
