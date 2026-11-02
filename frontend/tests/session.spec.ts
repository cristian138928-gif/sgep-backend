// frontend/tests/session.spec.ts
import { beforeEach, describe, expect, it } from 'vitest'

import { session } from '../src/api/session'

describe('session (localStorage)', () => {
  beforeEach(() => session.limpiar())

  it('guardar escribe access y refresh en claves distintas', () => {
    session.guardar({ access_token: 'aaa', refresh_token: 'rrr', token_type: 'bearer' })

    expect(session.access).toBe('aaa')
    expect(session.refresh).toBe('rrr')
  })

  it('limpiar borra ambos tokens (logout)', () => {
    session.guardar({ access_token: 'aaa', refresh_token: 'rrr', token_type: 'bearer' })
    session.limpiar()

    expect(session.access).toBeNull()
    expect(session.refresh).toBeNull()
  })

  it('leer sin nada devuelve null, no undefined', () => {
    expect(session.access).toBeNull()
    expect(session.refresh).toBeNull()
  })
})
