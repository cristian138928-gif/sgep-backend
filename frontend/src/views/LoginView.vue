<script setup lang="ts">
// src/views/LoginView.vue
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { ApiError } from '../api/client'
import { rutaPorRol } from '../router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const correo = ref('')
const contraseña = ref('')
const error = ref('')
const cargando = ref(false)

async function enviar(): Promise<void> {
  error.value = ''
  cargando.value = true
  try {
    const rol = await auth.login(correo.value, contraseña.value)
    const destino = route.query.redirigir
    await router.push(typeof destino === 'string' ? destino : rutaPorRol(rol))
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) {
      error.value = 'Correo o contraseña incorrectos.'
    } else if (e instanceof ApiError && e.status === 429) {
      error.value = e.detail
    } else {
      error.value = 'No se pudo conectar con el servidor.'
    }
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <div class="auth">
    <div class="auth-tarjeta">
      <div class="auth-logo">SGE<span>P</span></div>
      <p class="auth-sub">Inicia sesión para gestionar tus evidencias</p>

      <div v-if="error" class="alerta-error">{{ error }}</div>

      <form @submit.prevent="enviar">
        <div class="campo">
          <label for="correo">Correo institucional</label>
          <input
            id="correo"
            v-model.trim="correo"
            type="email"
            placeholder="nombre@sena.edu.co"
            required
            autocomplete="email"
            autofocus
          />
        </div>

        <div class="campo">
          <label for="contraseña">Contraseña</label>
          <input
            id="contraseña"
            v-model="contraseña"
            type="password"
            required
            autocomplete="current-password"
          />
        </div>

        <button class="btn btn-primario" type="submit" :disabled="cargando" style="width: 100%">
          {{ cargando ? 'Ingresando…' : 'Ingresar' }}
        </button>
      </form>

      <p class="auth-pie">
        ¿No tienes cuenta?
        <router-link to="/registro">Regístrate aquí</router-link>
      </p>
    </div>
  </div>
</template>
