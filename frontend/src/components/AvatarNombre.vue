<script setup lang="ts">
// src/components/AvatarNombre.vue
// EXPLICACIÓN: avatar de iniciales + nombre => filas de tabla con identidad
// visual (patrón de plataformas) sin endpoint de fotos.
import { computed } from 'vue'

const props = defineProps<{ nombre: string }>()

/** EXPLICACIÓN: hasta 2 iniciales (nombre + primer apellido) en mayúsculas */
const iniciales = computed(() => {
  const partes = props.nombre.trim().split(/\s+/).slice(0, 2)
  if (!partes[0]) return '??'
  return partes.map((p) => p[0]?.toUpperCase() ?? '').join('')
})
</script>

<template>
  <span class="avatar-nombre">
    <span class="avatar avatar-sm" aria-hidden="true">{{ iniciales }}</span>
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
.avatar-sm {
  width: 28px;
  height: 28px;
  font-size: 0.66rem;
}
.avatar-nombre-texto {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
