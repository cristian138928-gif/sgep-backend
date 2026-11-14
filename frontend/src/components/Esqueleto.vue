<script setup lang="ts">
// src/components/Esqueleto.vue
// EXPLICACIÓN: skeleton de carga con pulso suave (sin gradientes recargados)
// en lugar del círculo giratorio dentro de VacioEstado.
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
  background: var(--borde);
  animation: pulso 1.4s ease-in-out infinite;
}
.esqueleto-linea:nth-child(5n + 1) { width: 100%; }
.esqueleto-linea:nth-child(5n + 2) { width: 92%; }
.esqueleto-linea:nth-child(5n + 3) { width: 78%; }
.esqueleto-linea:nth-child(5n + 4) { width: 96%; }
.esqueleto-linea:nth-child(5n + 5) { width: 64%; }
@keyframes pulso {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.45; }
}
@media (prefers-reduced-motion: reduce) {
  .esqueleto-linea { animation: none; }
}
</style>
