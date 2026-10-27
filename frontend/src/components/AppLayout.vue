<script setup lang="ts">
// src/components/AppLayout.vue
// EXPLICACIÓN: shell de la sesión: sidebar por rol + badge de notificaciones + logout
import { computed, onBeforeUnmount, onMounted, ref, watch, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Bell,
  ClipboardCheck,
  Files,
  History,
  Inbox,
  LayoutDashboard,
  LogOut,
  Menu,
  TrendingUp,
  User,
  UserCheck,
  Users,
  X,
} from 'lucide-vue-next'

import { useAuthStore } from '../stores/auth'
import { useNotificacionesStore } from '../stores/notificaciones'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const notificaciones = useNotificacionesStore()

interface ItemNav {
  ruta: string
  etiqueta: string
  icono: Component
}

const navAprendiz: ItemNav[] = [
  { ruta: '/app/avance', etiqueta: 'Mi avance', icono: TrendingUp },
  { ruta: '/app/mis-evidencias', etiqueta: 'Mis evidencias', icono: Files },
  { ruta: '/app/notificaciones', etiqueta: 'Notificaciones', icono: Bell },
  { ruta: '/app/perfil', etiqueta: 'Mi perfil', icono: User },
]
const navInstructor: ItemNav[] = [
  { ruta: '/app/instructor/pendientes', etiqueta: 'Por evaluar', icono: Inbox },
  { ruta: '/app/instructor/historial', etiqueta: 'Historial', icono: History },
  { ruta: '/app/notificaciones', etiqueta: 'Notificaciones', icono: Bell },
  { ruta: '/app/perfil', etiqueta: 'Mi perfil', icono: User },
]
const navCoordinador: ItemNav[] = [
  { ruta: '/app/coordinador/dashboard', etiqueta: 'Dashboard', icono: LayoutDashboard },
  { ruta: '/app/coordinador/evidencias', etiqueta: 'Evidencias', icono: ClipboardCheck },
  { ruta: '/app/coordinador/aprendices', etiqueta: 'Aprendices', icono: Users },
  { ruta: '/app/coordinador/asignaciones', etiqueta: 'Asignaciones', icono: UserCheck },
  { ruta: '/app/notificaciones', etiqueta: 'Notificaciones', icono: Bell },
  { ruta: '/app/perfil', etiqueta: 'Mi perfil', icono: User },
]

const items = computed<ItemNav[]>(() => {
  if (auth.rol === 'instructor') return navInstructor
  if (auth.rol === 'coordinador') return navCoordinador
  return navAprendiz
})

const etiquetaRol = computed(() => auth.rol ?? 'usuario')

/** EXPLICACIÓN: iniciales del nombre => avatar identificable sin endpoint de foto */
const iniciales = computed(() => {
  const partes = auth.nombre.trim().split(/\s+/).slice(0, 2)
  if (!partes[0]) return '??'
  return partes.map((p) => p[0]?.toUpperCase() ?? '').join('')
})

const menuAbierto = ref(false)

// EXPLICACIÓN: al cambiar de ruta el drawer móvil se cierra solo (si no, tapa el contenido)
watch(
  () => route.fullPath,
  () => {
    menuAbierto.value = false
  },
)

let intervalo: number | undefined

onMounted(() => {
  // EXPLICACIÓN: F5 conserva tokens en localStorage pero no el perfil (Pinia vive en memoria)
  if (auth.autenticado && !auth.perfil) void auth.cargarPerfil()
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
    <div class="fondo-tecnico" aria-hidden="true" />

    <div v-if="menuAbierto" class="scrim" @click="menuAbierto = false" />

    <aside class="sidebar" :class="{ abierta: menuAbierto }">
      <div class="sidebar-logo">
        SGE<span>P</span>
        <button
          class="btn btn-fantasma menu-toggle cerrar-menu"
          type="button"
          aria-label="Cerrar menú"
          @click="menuAbierto = false"
        >
          <X :size="16" />
        </button>
      </div>
      <div class="sidebar-version">Gestión de evidencias</div>

      <div class="sidebar-seccion">Menú · {{ etiquetaRol }}</div>
      <router-link v-for="item in items" :key="item.ruta" :to="item.ruta">
        <component :is="item.icono" :size="17" />
        {{ item.etiqueta }}
      </router-link>

      <div class="sidebar-pie">SENA · ADSO · Ficha 3388939</div>
    </aside>

    <header class="topbar">
      <div class="fila">
        <button
          class="menu-toggle"
          type="button"
          aria-label="Abrir menú"
          @click="menuAbierto = true"
        >
          <Menu :size="18" />
        </button>
        <span class="topbar-titulo">Sistema de Gestión de <strong>Evidencias</strong></span>
      </div>

      <div class="topbar-usuario">
        <router-link to="/app/notificaciones" class="campana" aria-label="Notificaciones">
          <Bell :size="17" />
          <span v-if="notificaciones.noLeidas > 0" class="campana-badge">
            {{ notificaciones.badge }}
          </span>
        </router-link>

        <span class="usuario-nombre">
          <b>{{ auth.nombre || auth.perfil?.correo_institucional }}</b>
          <span>{{ etiquetaRol }}</span>
        </span>
        <span class="avatar">{{ iniciales }}</span>

        <button class="btn" type="button" @click="cerrarSesion">
          <LogOut :size="15" />
          <span class="salir-texto">Salir</span>
        </button>
      </div>
    </header>

    <main class="contenido">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
/* EXPLICACIÓN: el texto del botón se oculta en móvil para que quepan las 3 acciones */
@media (max-width: 560px) {
  .salir-texto { display: none; }
}

.cerrar-menu {
  margin-left: auto;
  width: 30px;
  height: 30px;
  padding: 0;
}
</style>
