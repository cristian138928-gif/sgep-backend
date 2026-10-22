<script setup lang="ts">
// src/views/LoginView.vue
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { FileCheck2, Lock, ShieldCheck, TrendingUp } from 'lucide-vue-next'

import { ApiError } from '../api/client'
import AuthPanel from '../components/AuthPanel.vue'
import { rutaPorRol } from '../router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const features = [
  { icono: FileCheck2, texto: 'Carga y seguimiento de bitácoras y formatos F023/F028' },
  { icono: ShieldCheck, texto: 'Evaluación con retroalimentación y control de accesos' },
  { icono: TrendingUp, texto: 'Avance porcentual y alertas de vencimiento en tiempo real' },
]

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
  <AuthPanel
    lema="Tus evidencias de etapa práctica,"
    resaltado="bajo control"
    :features="features"
  >
    <div class="auth-tarjeta">
      <div class="auth-logo logo-sm mb-1">SGE<span>P</span></div>
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

        <button class="btn btn-primario btn-ancho" type="submit" :disabled="cargando">
          <Lock v-if="!cargando" :size="15" />
          {{ cargando ? 'Ingresando…' : 'Ingresar' }}
        </button>
      </form>

      <p class="auth-pie">
        ¿No tienes cuenta?
        <router-link to="/registro">Regístrate aquí</router-link>
      </p>
    </div>
  </AuthPanel>
</template>
