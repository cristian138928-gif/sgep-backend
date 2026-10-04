<script setup lang="ts">
// src/components/EstadoBadge.vue
// EXPLICACIÓN: un solo componente => colores de estado consistentes en toda la UI
import type { EstadoEvidencia } from '../api/types'

const props = defineProps<{ estado: EstadoEvidencia }>()

const clases: Record<EstadoEvidencia, string> = {
  Aprobada: 'badge badge-aprobada',
  Pendiente: 'badge badge-pendiente',
  'Ajuste Requerido': 'badge badge-ajuste',
}
</script>

<template>
  <span :class="clases[props.estado]">{{ props.estado }}</span>
</template>
