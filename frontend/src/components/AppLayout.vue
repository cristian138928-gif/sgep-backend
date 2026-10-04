<script setup lang="ts">
// src/components/AppLayout.vue
// EXPLICACIÓN: shell de la sesión: sidebar por rol + badge de notificaciones + logout
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import { useNotificacionesStore } from '../stores/notificaciones'

const router = useRouter()
const auth = useAuthStore()
const notificaciones = useNotificacionesStore()

interface ItemNav {
  ruta: string
  etiqueta: string
}

const navAprendiz: ItemNav[] = [
  { ruta: '/app/avance', etiqueta: 'Mi avance' },
  { ruta: '/app/mis-evidencias', etiqueta: 'Mis evidencias' },
  { ruta: '/app/notificaciones', etiqueta: 'Notificaciones' },
]
const navInstructor: ItemNav[] = [
  { ruta: '/app/instructor/pendientes', etiqueta: 'Por evaluar' },
  { ruta: '/app/instructor/historial', etiqueta: 'Historial' },
  { ruta: '/app/notificaciones', etiqueta: 'Notificaciones' },
]
const navCoordinador: ItemNav[] = [
  { ruta: '/app/coordinador/dashboard', etiqueta: 'Dashboard' },
  { ruta: '/app/coordinador/evidencias', etiqueta: 'Evidencias' },
  { ruta: '/app/coordinador/aprendices', etiqueta: 'Aprendices' },
  { ruta: '/app/notificaciones', etiqueta: 'Notificaciones' },
]

const items = computed<ItemNav[]>(() => {
  if (auth.rol === 'instructor') return navInstructor
  if (auth.rol === 'coordinador') return navCoordinador
  return navAprendiz
})

const etiquetaRol = computed(() => auth.rol ?? 'usuario')

let intervalo: number | undefined

onMounted(() => {
  void notificaciones.refrescar()
  // EXPLICACIÓN: poll ligero (badge) cada 60s; /no-leidas pesa menos que la lista
  intervalo = window.setInterval(() => {
    void notificaciones.refrescar()
  }, 60_000)
})

onBeforeUnmount(() => {
  if (intervalo !== undefined) window.clearInterval(intervalo)
})

function cerrarSesion(): void {
  notificaciones.limpiar()
  auth.logout()
  void router.push('/login')
}
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-logo">SGE<span>P</span></div>
      <div class="sidebar-seccion">Menú · {{ etiquetaRol }}</div>
      <router-link v-for="item in items" :key="item.ruta" :to="item.ruta">
        {{ item.etiqueta }}
      </router-link>
    </aside>

    <header class="topbar">
      <strong>Sistema de Gestión de Evidencias</strong>
      <div class="topbar-usuario">
        <router-link to="/app/notificaciones" class="campana" aria-label="Notificaciones">
          Avisos
          <span v-if="notificaciones.noLeidas > 0" class="campana-badge">
            {{ notificaciones.badge }}
          </span>
        </router-link>
        <span>{{ auth.nombre || auth.perfil?.correo_institucional }}</span>
        <button class="btn" type="button" @click="cerrarSesion">Cerrar sesión</button>
      </div>
    </header>

    <main class="contenido">
      <router-view />
    </main>
  </div>
</template>
