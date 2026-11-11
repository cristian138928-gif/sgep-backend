<script setup lang="ts">
// src/components/AvatarCirculo.vue
// EXPLICACIÓN: un solo componente concentra el sistema de avatares (foto,
// iniciales y punto de sesión) => navbar y listados nunca divergen visualmente.
import { computed, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    /** Nombre completo: origen de las iniciales */
    nombre: string
    /** Foto registrada; sin URL o con error => respaldo de iniciales */
    foto?: string | null
    /** Punto verde = sesión activa */
    enLinea?: boolean
  }>(),
  { foto: '', enLinea: true },
)

const fotoRota = ref(false)

// EXPLICACIÓN: cambiar de foto reactiva el intento; sin reset quedaría en iniciales
watch(
  () => props.foto,
  () => {
    fotoRota.value = false
  },
)

const mostrarFoto = computed(() => Boolean(props.foto) && !fotoRota.value)

/** EXPLICACIÓN: hasta 2 iniciales (nombre + primer apellido) en mayúsculas */
const iniciales = computed(() => {
  const partes = props.nombre.trim().split(/\s+/).slice(0, 2)
  if (!partes[0]) return '??'
  return partes.map((p) => p[0]?.toUpperCase() ?? '').join('')
})
</script>

<template>
  <span class="relative inline-flex h-9 w-9 flex-none">
    <img
      v-if="mostrarFoto"
      :src="foto ?? ''"
      alt=""
      class="avatar-foto h-9 w-9 rounded-full border border-slate-200 object-cover"
      @error="fotoRota = true"
    />
    <span
      v-else
      class="avatar-iniciales flex h-9 w-9 items-center justify-center rounded-full bg-slate-200 font-semibold text-slate-700"
      aria-hidden="true"
    >
      {{ iniciales }}
    </span>
    <!-- EXPLICACIÓN: inset 6px => el punto (8px + ring 2px) cabe entero DENTRO del arco del círculo -->
    <span
      v-if="enLinea"
      class="avatar-estado absolute bottom-1.5 right-1.5 h-2 w-2 rounded-full bg-emerald-500 ring-2 ring-white"
      aria-hidden="true"
    />
  </span>
</template>
