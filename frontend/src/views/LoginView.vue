<script setup lang="ts">
// src/views/LoginView.vue
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { FileCheck2, Lock, ShieldCheck, TrendingUp } from 'lucide-vue-next'

import { ApiError } from '../api/client'
import AuthPanel from '../components/AuthPanel.vue'
import sgepLogo from '../assets/imagenes/sgep-logo.jpg'
import { rutaPorRol } from '../router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const features = [
  { icono: FileCheck2, texto: 'Carga y seguimiento de bit\u00e1coras y formatos F023/F028' },
  { icono: ShieldCheck, texto: 'Evaluaci\u00f3n con retroalimentaci\u00f3n y control de accesos' },
  { icono: TrendingUp, texto: 'Avance porcentual y alertas de vencimiento en tiempo real' },
]

const correo = ref('')
const contrasena = ref('')
const error = ref('')
const cargando = ref(false)

async function enviar(): Promise<void> {
  error.value = ''
  cargando.value = true
  try {
    const rol = await auth.login(correo.value, contrasena.value)
    const destino = route.query.redirigir
    await router.push(typeof destino === 'string' ? destino : rutaPorRol(rol))
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) {
      error.value = 'Correo o contrase\u00f1a incorrectos.'
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
    lema="Tus evidencias de etapa pr\u00e1ctica,"
    resaltado="bajo control"
    :features="features"
  >
    <div class="auth-tarjeta">
      <img
        :src="sgepLogo"
        alt="SGEP"
        class="mb-2 h-24 w-auto rounded-xl border border-slate-200 object-cover"
      />
      <p class="auth-sub">Inicia sesi\u00f3n para gestionar tus evidencias</p>

      <div v-if="error" class="alerta-error" role="alert">{{ error }}</div>

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
          <label for="contraseña">Contrase\u00f1a</label>
          <input
            id="contraseña"
            v-model="contrasena"
            type="password"
            required
            autocomplete="current-password"
          />
        </div>

        <button class="btn btn-primario btn-ancho" type="submit" :disabled="cargando">
          <Lock v-if="!cargando" :size="15" />
          {{ cargando ? 'Ingresando\u2026' : 'Ingresar' }}
        </button>
      </form>

      <p class="auth-pie">
        \u00bfNo tienes cuenta?
        <router-link to="/registro">Reg\u00edstrate aqu\u00ed</router-link>
      </p>
    </div>
  </AuthPanel>
</template>
