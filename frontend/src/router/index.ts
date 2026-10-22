// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'

import { intentarRefrescar } from '../api/client'
import { tokenExpirado } from '../api/jwt'
import { session } from '../api/session'
import type { Rol } from '../api/types'
import { useAuthStore } from '../stores/auth'
import { useNotificacionesStore } from '../stores/notificaciones'

/** Ruta de entrada según el rol (usada por '/' y tras login). */
export function rutaPorRol(rol: Rol | null): string {
  if (rol === 'instructor') return '/app/instructor/pendientes'
  if (rol === 'coordinador') return '/app/coordinador/dashboard'
  return '/app/avance'
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // EXPLICACIÓN: SIN ruta '/' con redirect a sí mismo — Vue Router recursa en
    // push() hasta explotar el stack. El beforeEach (más abajo) resuelve '/'.
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { publico: true },
    },
    {
      path: '/registro',
      name: 'registro',
      component: () => import('../views/RegistroView.vue'),
      meta: { publico: true },
    },
    {
      path: '/app',
      component: () => import('../components/AppLayout.vue'),
      children: [
        {
          path: 'avance',
          name: 'avance',
          component: () => import('../views/aprendiz/AvanceView.vue'),
          meta: { roles: ['aprendiz'] },
        },
        {
          path: 'mis-evidencias',
          name: 'mis-evidencias',
          component: () => import('../views/aprendiz/MisEvidenciasView.vue'),
          meta: { roles: ['aprendiz'] },
        },
        {
          path: 'notificaciones',
          name: 'notificaciones',
          component: () => import('../views/NotificacionesView.vue'),
        },
        {
          path: 'instructor/pendientes',
          name: 'pendientes',
          component: () => import('../views/instructor/PendientesView.vue'),
          meta: { roles: ['instructor'] },
        },
        {
          path: 'instructor/evaluar/:id',
          name: 'evaluar',
          component: () => import('../views/instructor/EvaluarView.vue'),
          meta: { roles: ['instructor'] },
          props: true,
        },
        {
          path: 'instructor/historial',
          name: 'historial',
          component: () => import('../views/instructor/HistorialView.vue'),
          meta: { roles: ['instructor'] },
        },
        {
          path: 'coordinador/dashboard',
          name: 'dashboard',
          component: () => import('../views/coordinador/DashboardView.vue'),
          meta: { roles: ['coordinador'] },
        },
        {
          path: 'coordinador/evidencias',
          name: 'evidencias-coordinador',
          component: () => import('../views/coordinador/EvidenciasView.vue'),
          meta: { roles: ['coordinador'] },
        },
        {
          path: 'coordinador/aprendices',
          name: 'aprendices',
          component: () => import('../views/coordinador/AprendicesView.vue'),
          meta: { roles: ['coordinador'] },
        },
        {
          path: 'coordinador/asignaciones',
          name: 'asignaciones',
          component: () => import('../views/coordinador/AsignacionesView.vue'),
          meta: { roles: ['coordinador'] },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'no-encontrado',
      component: () => import('../views/NoEncontradoView.vue'),
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // EXPLICACIÓN: access caducado => 1 refresh silencioso antes de decidir guards
  if (session.access && tokenExpirado(session.access)) {
    if (await intentarRefrescar()) {
      auth.sincronizarToken()
    } else {
      auth.logout()
      useNotificacionesStore().limpiar()
    }
  }

  // EXPLICACIÓN: 404 es público (URL desconocida sin sesión => 404, no login);
  // '/' cae en el catch-all => se resuelve como home del rol o login
  if (to.name === 'no-encontrado') {
    if (to.path === '/') {
      return auth.autenticado ? rutaPorRol(auth.rol) : { name: 'login', query: { redirigir: '/' } }
    }
    return true
  }

  // Usuario ya logueado no debe ver login/registro
  if (to.meta.publico === true) {
    return auth.autenticado ? rutaPorRol(auth.rol) : true
  }

  if (!auth.autenticado) {
    return { name: 'login', query: { redirigir: to.fullPath } }
  }

  const roles = to.meta.roles as Rol[] | undefined
  if (roles && auth.rol && !roles.includes(auth.rol)) {
    // EXPLICACIÓN: rol equivocado => home del propio rol (sin bucle por ruta actual)
    return rutaPorRol(auth.rol)
  }

  return true
})

export default router
