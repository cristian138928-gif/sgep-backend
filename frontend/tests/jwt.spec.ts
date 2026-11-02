// frontend/tests/jwt.spec.ts
import { describe, expect, it } from 'vitest'

import { decodificarToken, tokenExpirado } from '../src/api/jwt'
import { fabricarToken } from './helpers'

describe('decodificarToken', () => {
  it('lee rol, sub y exp desde el payload base64url', () => {
    const token = fabricarToken({ sub: '7', rol: 'instructor', type: 'access', exp: 1_800_000_000 })

    expect(decodificarToken(token)).toEqual({ sub: '7', rol: 'instructor', type: 'access', exp: 1_800_000_000 })
  })

  it('devuelve null con token basura (sin punto ni payload)', () => {
    expect(decodificarToken('no-es-un-jwt')).toBeNull()
  })

  it('devuelve null si el payload no es JSON', () => {
    const body = btoa('esto no es json').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
    expect(decodificarToken(`a.${body}.c`)).toBeNull()
  })
})

describe('tokenExpirado', () => {
  const ahora = Math.floor(Date.now() / 1000)

  it('true si no trae exp (token malformado o sin vencimiento)', () => {
    expect(tokenExpirado(fabricarToken({ rol: 'aprendiz' }))).toBe(true)
  })

  it('true con exp pasado', () => {
    expect(tokenExpirado(fabricarToken({ exp: ahora - 60 }))).toBe(true)
  })

  it('false con exp futuro', () => {
    expect(tokenExpirado(fabricarToken({ exp: ahora + 3600 }))).toBe(false)
  })

  it('true dentro de los 5s de margen (evita carrera con el backend)', () => {
    expect(tokenExpirado(fabricarToken({ exp: ahora + 3 }))).toBe(true)
  })
})
