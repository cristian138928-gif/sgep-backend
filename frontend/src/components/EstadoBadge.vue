<script setup lang="ts">
// src/components/EstadoBadge.vue
// EXPLICACIÓN: píldora de estado compartida => misma paleta de guía en todas las vistas
import type { EstadoEvidencia } from '../api/types'
import { clasesEstado, pillBase } from '../styles/ui-classes'

const props = defineProps<{ estado: EstadoEvidencia }>()
</script>

<template>
  <span :class="[pillBase, clasesEstado[props.estado]]">
    <!-- EXPLICACIÓN: punto con color actual => se distingue el estado sin leer el texto -->
    <span class="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
    {{ props.estado }}
  </span>
</template>
