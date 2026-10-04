// src/stores/auth.ts
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { api } from '../api/client'
import { decodificarToken } from '../api/jwt'
import { session } from '../api/session'
import type { ParTokens, Perfil, RegistroAprendiz, RegistroCoordinador, RegistroInstructor, Rol } from '../api/types'

export const useAuthStore = defineStore('auth', () => {
  const perfil = ref<Perfil | null>(null)
  const token = ref<string | null>(session.access)

  // EXPLICACIÓN: rol desde el claim del JWT => guards sin petición extra al backend
  const rol = computed<Rol | null>(() => {
    const payload = token.value ? decodificarToken(token.value) : null
    return (payload?.rol as Rol | undefined) ?? null
  })
  const autenticado = computed(() => !!token.value)
  const nombre = computed(() => perfil.value?.nombre_completo ?? '')

  async function login(correo: string, contraseña: string): Promise<Rol> {
    const par = await api<ParTokens>('/api/v1/auth/login', {
      method: 'POST',
      auth: false,
      body: JSON.stringify({ correo_institucional: correo, contraseña }),
    })
    session.guardar(par)
    token.value = par.access_token
    await cargarPerfil()
    return rol.value ?? 'aprendiz'
  }

  async function registrarAprendiz(datos: RegistroAprendiz): Promise<Rol> {
    return registrarCon('/api/v1/auth/registro', datos)
  }
  async function registrarInstructor(datos: RegistroInstructor): Promise<Rol> {
    return registrarCon('/api/v1/auth/registro-instructor', datos)
  }
  async function registrarCoordinador(datos: RegistroCoordinador): Promise<Rol> {
    return registrarCon('/api/v1/auth/registro-coordinador', datos)
  }

  /** El registro del backend devuelve el par de tokens => login automático. */
  async function registrarCon(ruta: string, datos: object): Promise<Rol> {
    const par = await api<ParTokens>(ruta, {
      method: 'POST',
      auth: false,
      body: JSON.stringify(datos),
    })
    session.guardar(par)
    token.value = par.access_token
    await cargarPerfil()
    return rol.value ?? 'aprendiz'
  }

  async function cargarPerfil(): Promise<void> {
    perfil.value = await api<Perfil>('/api/v1/auth/me')
  }

  /** Tras un refresh exitoso (client.ts), actualiza el token en memoria. */
  function sincronizarToken(): void {
    token.value = session.access
  }

  function logout(): void {
    session.limpiar()
    token.value = null
    perfil.value = null
  }

  return {
    perfil,
    token,
    rol,
    autenticado,
    nombre,
    login,
    registrarAprendiz,
    registrarInstructor,
    registrarCoordinador,
    cargarPerfil,
    sincronizarToken,
    logout,
  }
})
