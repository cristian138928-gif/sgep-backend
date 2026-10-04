// src/api/jwt.ts
/**
 * EXPLICACIÓN: Decodificar el payload (base64url) SIN verificar firma:
 * la firma la valida el backend; aquí solo leemos rol/exp para guards.
 */

export interface PayloadToken {
  sub?: string
  id?: number
  rol?: string
  type?: string
  exp?: number
}

export function decodificarToken(token: string): PayloadToken | null {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(base64)) as PayloadToken
  } catch {
    return null
  }
}

export function tokenExpirado(token: string): boolean {
  const payload = decodificarToken(token)
  if (!payload?.exp) return true
  // EXPLICACIÓN: 5s de margen para evitar carreras con el backend
  return payload.exp * 1000 <= Date.now() + 5000
}
