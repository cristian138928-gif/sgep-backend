<script setup lang="ts">
// src/components/AlertaLista.vue
// EXPLICACIÓN: lista reutilizable de alertas de vencimiento (aprendiz/instructor/coordinador)
import type { Alerta, AlertaRol } from '../api/types'

const props = defineProps<{ alertas: Alerta[]; mostrarAprendiz?: boolean }>()

function fechaCorta(iso: string): string {
  return iso.slice(0, 10)
}

/** EXPLICACIÓN: cast puntual porque la API agrega nombre_aprendiz solo en roles con filtro */
function nombreDe(a: Alerta): string {
  return (a as AlertaRol).nombre_aprendiz
}
</script>

<template>
  <div v-if="alertas.length === 0" class="vacio">
    <h3>Sin alertas</h3>
    <p>Ninguna evidencia vence en la ventana seleccionada.</p>
  </div>

  <div v-else class="tabla-contenedor">
    <div v-for="a in alertas" :key="a.id_evidencia" class="lista-item">
      <div>
        <h4>{{ a.titulo }}</h4>
        <p>
          <template v-if="props.mostrarAprendiz">{{ nombreDe(a) }} · </template>
          Fecha límite: {{ fechaCorta(a.fecha_deadline) }}
          · {{ a.dias_restantes > 0 ? `${a.dias_restantes} día(s) restantes` : 'superada' }}
        </p>
      </div>
      <span
        class="badge"
        :class="a.estado_alerta === 'Vencida' ? 'badge-vencida' : 'badge-ajuste'"
      >
        {{ a.estado_alerta }}
      </span>
    </div>
  </div>
</template>
