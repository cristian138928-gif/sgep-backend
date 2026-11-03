<script setup lang="ts">
// EXPLICACIÓN: vista = un solo componente => fade-up al entrar/salir por cambio de ruta
import { Transition } from 'vue'
</script>

<template>
  <router-view v-slot="{ Component }">
    <Transition name="vista" mode="out-in">
      <component :is="Component" />
    </Transition>
  </router-view>
</template>

<style>
.vista-enter-active { transition: opacity 0.22s ease, transform 0.22s ease; }
.vista-leave-active { transition: opacity 0.22s ease, transform 0.22s ease; }
.vista-enter-from, .vista-leave-to { opacity: 0; transform: translateY(10px); }
.vista-enter-to, .vista-leave-from { opacity: 1; transform: none; }
</style>
