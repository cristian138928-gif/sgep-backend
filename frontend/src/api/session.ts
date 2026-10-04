// src/api/session.ts
/**
 * EXPLICACIÓN: Tokens en localStorage vía UN módulo único;
 * client.ts y stores/auth.ts lo comparten (evita dependencia circular).
 */

import type { ParTokens } from './types'

const CLAVE_ACCESS = 'sgep_access'
const CLAVE_REFRESH = 'sgep_refresh'

export const session = {
  get access(): string | null {
    return localStorage.getItem(CLAVE_ACCESS)
  },
  get refresh(): string | null {
    return localStorage.getItem(CLAVE_REFRESH)
  },
  guardar(par: ParTokens): void {
    localStorage.setItem(CLAVE_ACCESS, par.access_token)
    localStorage.setItem(CLAVE_REFRESH, par.refresh_token)
  },
  limpiar(): void {
    localStorage.removeItem(CLAVE_ACCESS)
    localStorage.removeItem(CLAVE_REFRESH)
  },
}
