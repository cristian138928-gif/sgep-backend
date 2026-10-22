<script setup lang="ts">
// src/components/VacioEstado.vue
// EXPLICACIÓN: estado vacío/carga compartido => una sola voz visual y un solo
// lugar para añadir (más adelante) botón de reintento o esqueleto de carga.
import type { Component } from 'vue'

withDefaults(
  defineProps<{
    titulo: string
    texto: string
    icono: Component
    cargando?: boolean
  }>(),
  { cargando: false },
)
</script>

<template>
  <div class="vacio">
    <span class="vacio-ico" :class="{ girando: cargando }">
      <component :is="icono" :size="26" />
    </span>
    <h3>{{ titulo }}</h3>
    <p>{{ texto }}</p>
  </div>
</template>

<style scoped>
/* EXPLICACIÓN: el icono se estiliza aquí para no engordar el CSS global */
.vacio-ico {
  display: inline-grid;
  place-items: center;
  width: 52px;
  height: 52px;
  margin-bottom: 0.6rem;
  border-radius: 50%;
  background: var(--superficie-alta);
  border: 1px solid var(--borde-fuerte);
  color: var(--texto-suave);
}
.vacio-ico.girando {
  color: var(--cian);
  border-color: rgba(34, 211, 238, 0.35);
  animation: pulso 1.1s ease-in-out infinite;
}
@keyframes pulso {
  0%, 100% { opacity: 0.45; }
  50% { opacity: 1; }
}
</style>
