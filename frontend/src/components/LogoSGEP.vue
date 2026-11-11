<script setup lang="ts">
// EXPLICACIÓN: SVG inline (no <img>) => hereda currentColor y evita duplicar variantes clara/oscura
// `fuente` equivale al font-size previo (.sidebar-logo 1.2rem / .auth-logo 2rem / .logo-sm 1.5rem)
import icono from '../assets/imagenes/sgep-icono.jpg'

const props = withDefaults(defineProps<{ fuente?: number }>(), { fuente: 28 })

// EXPLICACIÓN: viewBox es 36 unidades para font-size 28 => escalar la caja mantiene la proporción
const ALTO_CAJA = 36 / 28
</script>

<template>
  <span class="inline-flex items-center gap-2">
    <!-- EXPLICACIÓN: el isotipo mide `fuente` px => ~1.4× la altura de mayúscula del wordmark -->
    <img
      :src="icono"
      :style="{ height: `${props.fuente}px` }"
      class="w-auto shrink-0 rounded-md object-cover ring-1 ring-white/10"
      alt=""
      aria-hidden="true"
    />
    <!-- EXPLICACIÓN: textLength fija el ancho => la sigla cabe aunque falle la pila de fuentes -->
    <svg
      :style="{ height: `${props.fuente * ALTO_CAJA}px` }"
      class="block w-auto shrink-0"
      viewBox="0 0 72 36"
      role="img"
      aria-label="SGEP"
    >
      <text
        x="2"
        y="28"
        fill="currentColor"
        font-size="28"
        font-weight="800"
        textLength="66"
        lengthAdjust="spacingAndGlyphs"
        style="font-family: var(--fuente-mono)"
      >SGE<tspan fill="#10b981">P</tspan></text>
    </svg>
  </span>
</template>
