<script setup lang="ts">
// src/components/AuthPanel.vue
// EXPLICACIÓN: shell visual de autenticación (marca + formulario) compartido
// por Login, Registro y 404 => una sola fuente de verdad del layout partido.
import type { Component } from 'vue'
// EXPLICACIÓN: Vite convierte la importación de SVG en URL estática (fingerprint en build)
import heroAuth from '../assets/imagenes/hero-auth.svg'

// EXPLICACIÓN: interface sin `export` porque <script setup> no admite exports de módulo
interface FeatureAuth {
  icono: Component
  texto: string
}

withDefaults(
  defineProps<{
    lema: string
    resaltado: string
    features: FeatureAuth[]
    meta?: string
  }>(),
  { meta: 'SENA · Programa ADSO · Ficha 3388939' },
)
</script>

<template>
  <div class="auth">
    <section class="auth-marca">
      <div>
        <div class="auth-logo">SGE<span>P</span></div>
        <p class="auth-lema">{{ lema }} <em>{{ resaltado }}</em>.</p>
        <img class="auth-hero" :src="heroAuth" alt="" aria-hidden="true" />
      </div>

      <ul class="auth-features">
        <li v-for="f in features" :key="f.texto">
          <component :is="f.icono" :size="18" />
          {{ f.texto }}
        </li>
      </ul>

      <div class="auth-meta">{{ meta }}</div>
    </section>

    <div class="auth-form-wrap">
      <slot />
    </div>
  </div>
</template>

<style scoped>
/* EXPLICACIÓN: hero decorativo bajo el lema; se oculta en pantallas angostas */
.auth-hero {
  display: block;
  width: 100%;
  max-width: 380px;
  max-height: 240px;
  margin-top: 1.5rem;
  opacity: 0.92;
}
@media (max-width: 900px) {
  .auth-hero {
    display: none;
  }
}
</style>
