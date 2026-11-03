<script setup lang="ts">
// src/components/Esqueleto.vue
// EXPLICACIÓN: skeleton shimmer genérico => la carga se ve "viva" estilo
// Linear/Notion en vez del círculo giratorio dentro de VacioEstado.
withDefaults(
  defineProps<{
    /** Número de líneas/ranuras a pintar */
    filas?: number
  }>(),
  { filas: 4 },
)
</script>

<template>
  <div class="esqueleto" aria-hidden="true">
    <div v-for="n in filas" :key="n" class="esqueleto-linea" />
  </div>
</template>

<style scoped>
.esqueleto {
  display: grid;
  gap: 0.9rem;
  padding: 1.4rem 1.25rem;
}
.esqueleto-linea {
  height: 14px;
  border-radius: 6px;
  background: linear-gradient(90deg, var(--superficie-alta) 25%, var(--borde) 50%, var(--superficie-alta) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.3s linear infinite;
}
/* EXPLICACIÓN: anchos irregulares => simula contenido real, no un bloque monótono */
.esqueleto-linea:nth-child(5n + 1) { width: 100%; }
.esqueleto-linea:nth-child(5n + 2) { width: 92%; }
.esqueleto-linea:nth-child(5n + 3) { width: 78%; }
.esqueleto-linea:nth-child(5n + 4) { width: 96%; }
.esqueleto-linea:nth-child(5n + 5) { width: 64%; }
@keyframes shimmer {
  to { background-position: -200% 0; }
}
@media (prefers-reduced-motion: reduce) {
  .esqueleto-linea { animation: none; }
}
</style>
