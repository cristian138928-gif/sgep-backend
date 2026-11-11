<script setup lang="ts">
// src/components/AvatarNombre.vue
// EXPLICACIÓN: AvatarCirculo + nombre => filas de tabla con identidad visual
// (patrón de plataformas) reutilizando el sistema de avatares profesional.
import AvatarCirculo from './AvatarCirculo.vue'

defineProps<{
  nombre: string
  /** URL de foto registrada (opcional; sin ella => iniciales) */
  foto?: string | null
  /** Muestra el punto verde de sesión activa */
  enLinea?: boolean
}>()
</script>

<template>
  <span class="avatar-nombre">
    <AvatarCirculo :nombre="nombre" :foto="foto" :en-linea="enLinea" />
    <span class="avatar-nombre-texto">{{ nombre }}</span>
  </span>
</template>

<style scoped>
.avatar-nombre {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  min-width: 0;
}
.avatar-nombre-texto {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
