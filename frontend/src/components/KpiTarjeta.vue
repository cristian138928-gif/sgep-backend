<script setup lang="ts">
// src/components/KpiTarjeta.vue
// EXPLICACIÓN: KPI reutilizable (icono + valor mono + barra de tono) para que
// los tableros de coordinador/instructor compartan exactamente el mismo lenguaje.
import type { Component } from 'vue'

type Tono = 'verde' | 'azul' | 'cian' | 'ambar' | 'rojo'

withDefaults(
  defineProps<{
    etiqueta: string
    valor: string | number
    icono: Component
    tono?: Tono
  }>(),
  { tono: 'verde' },
)
</script>

<template>
  <div class="tarjeta kpi" :class="tono">
    <div class="cabecera-fila">
      <span class="kpi-ico" :class="tono">
        <component :is="icono" :size="18" />
      </span>
    </div>
    <div>
      <div class="kpi-valor">{{ valor }}</div>
      <div class="kpi-etiqueta">{{ etiqueta }}</div>
    </div>
  </div>
</template>
