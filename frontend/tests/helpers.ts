// frontend/tests/helpers.ts
/**
 * EXPLICACIÓN: JWT de mentira con el payload que queramos; el frontend solo
 * decodifica claims (rol/exp) y nunca verifica la firma, que es del backend.
 */
export function fabricarToken(payload: object): string {
  const body = btoa(JSON.stringify(payload))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '')
  return `eyJhbGciOiJIUzI1NiJ9.${body}.firma-falsa`
}
