<script setup lang="ts">
// src/components/PaginacionBar.vue
// EXPLICACIÓN: un solo componente para la paginación server-side => las 3 vistas
// paginadas no pueden divergir (ni olvidar el guard de página fuera de rango).
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

const props = defineProps<{
  pagina: number
  totalPaginas: number
  paginaActual: number
}>()

const emit = defineEmits<{ cambiar: [delta: number] }>()

/** EXPLICACIÓN: total_pages puede llegar 0 en una colección vacía => nunca "Página 1 de 0" */
const total = () => Math.max(props.totalPaginas, 1)
</script>

<template>
  <div class="paginacion">
    <button
      class="btn"
      type="button"
      :disabled="paginaActual === 1"
      @click="emit('cambiar', -1)"
    >
      <ChevronLeft :size="15" />
      Anterior
    </button>
    <span>Página {{ pagina }} de {{ total() }}</span>
    <button
      class="btn"
      type="button"
      :disabled="paginaActual >= total()"
      @click="emit('cambiar', 1)"
    >
      Siguiente
      <ChevronRight :size="15" />
    </button>
  </div>
</template>
