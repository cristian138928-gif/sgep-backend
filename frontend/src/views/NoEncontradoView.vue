<script setup lang="ts">
// src/views/NoEncontradoView.vue — 404 fuera del shell (sin sidebar)
import { FileQuestion } from 'lucide-vue-next'

import AuthPanel from '../components/AuthPanel.vue'

const features = [
  { icono: FileQuestion, texto: 'Revisa la dirección o vuelve al panel principal' },
  { icono: FileQuestion, texto: 'Tus evidencias y tu avance siguen donde los dejaste' },
  { icono: FileQuestion, texto: 'Si el problema persiste, contacta a la coordinación' },
]
</script>

<template>
  <AuthPanel lema="Ruta no encontrada," resaltado="vuelve al panel" :features="features">
    <div class="auth-tarjeta centrado">
      <div class="auth-logo logo-sm">SGE<span>P</span></div>
      <h1 class="mono">404</h1>
      <p class="auth-sub">La página que buscas no existe.</p>
      <router-link class="btn btn-primario" to="/">Volver al inicio</router-link>
    </div>
  </AuthPanel>
</template>
