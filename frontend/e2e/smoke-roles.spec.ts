import { expect, test } from '@playwright/test'

// EXPLICACIÓN: credenciales demo sembradas por scripts/seed_demo.py (idempotente)
const PASS = 'Demo1234!'

async function login(page: import('@playwright/test').Page, correo: string) {
  await page.goto('/login', { waitUntil: 'domcontentloaded' })
  await page.locator('input[type="email"]').fill(correo)
  await page.locator('input[type="password"]').fill(PASS)
  await Promise.all([
    page.waitForURL(/\/app\//, { timeout: 20_000 }),
    page.locator('button[type="submit"]').click(),
  ])
}

test.describe('Smoke UI por rol (#9)', () => {
  test('aprendiz: login, avance y mis evidencias', async ({ page }) => {
    await login(page, 'aprendiz.demo@sena.edu.co')
    await expect(page).toHaveURL(/\/app\/avance/, { timeout: 15_000 })
    await expect(page.getByRole('heading', { name: /Mi avance/i })).toBeVisible()

    await page.goto('/app/mis-evidencias')
    await expect(page).toHaveURL(/\/app\/mis-evidencias/)
    await expect(page.getByRole('heading', { name: /Mis evidencias/i })).toBeVisible()
  })

  test('instructor: login, pendientes e historial', async ({ page }) => {
    await login(page, 'instructor.demo@sena.edu.co')
    await expect(page).toHaveURL(/\/app\/instructor\/pendientes/, { timeout: 15_000 })
    await expect(page.getByRole('heading', { name: /Bandeja de pendientes/i })).toBeVisible()

    await page.goto('/app/instructor/historial')
    await expect(page).toHaveURL(/\/app\/instructor\/historial/)
    await expect(page.getByRole('heading', { name: /Historial de evaluaciones/i })).toBeVisible()
  })

  test('coordinador: login, dashboard y asignaciones', async ({ page }) => {
    await login(page, 'coordinador.demo@sena.edu.co')
    await expect(page).toHaveURL(/\/app\/coordinador\/dashboard/, { timeout: 15_000 })
    await expect(page.getByRole('heading', { name: /Dashboard/i })).toBeVisible()

    await page.goto('/app/coordinador/asignaciones')
    await expect(page).toHaveURL(/\/app\/coordinador\/asignaciones/)
    await expect(page.getByRole('heading', { name: /Asignaciones de seguimiento/i })).toBeVisible()
  })
})
