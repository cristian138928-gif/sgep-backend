<script setup lang="ts">
// src/views/PerfilView.vue
// EXPLICACIÓN: perfil de los 3 roles — nombre editable + cambio de contraseña (PUT /auth/me)
import { onMounted, reactive, ref } from 'vue'
import { KeyRound, Save, ShieldCheck } from 'lucide-vue-next'

import { api, ApiError } from '../api/client'
import type { Perfil } from '../api/types'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

const perfil = ref<Perfil | null>(null)
const nombre = ref('')
const cargando = ref(true)

const error = ref('')
const info = ref('')

const clave = reactive({ actual: '', nueva: '', confirmar: '' })
const guardandoNombre = ref(false)
const guardandoClave = ref(false)

const etiquetaRol = () => auth.rol ?? 'usuario'

onMounted(async () => {
  try {
    perfil.value = await api<Perfil>('/api/v1/auth/me')
    nombre.value = perfil.value.nombre_completo
  } catch {
    error.value = 'No se pudo cargar tu perfil.'
  } finally {
    cargando.value = false
  }
})

async function guardarNombre(): Promise<void> {
  error.value = ''
  info.value = ''
  guardandoNombre.value = true
  try {
    perfil.value = await api<Perfil>('/api/v1/auth/me', {
      method: 'PUT',
      body: JSON.stringify({ nombre_completo: nombre.value }),
    })
    // EXPLICACIÓN: recarga el store => el nombre del topbar se actualiza al instante
    await auth.cargarPerfil()
    info.value = 'Nombre actualizado correctamente.'
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail : 'No se pudo guardar el nombre.'
  } finally {
    guardandoNombre.value = false
  }
}

async function cambiarClave(): Promise<void> {
  error.value = ''
  info.value = ''

  if (clave.nueva.length < 8) {
    error.value = 'La contraseña nueva debe tener al menos 8 caracteres.'
    return
  }
  if (clave.nueva !== clave.confirmar) {
    error.value = 'La confirmación no coincide con la contraseña nueva.'
    return
  }

  guardandoClave.value = true
  try {
    await api<Perfil>('/api/v1/auth/me', {
      method: 'PUT',
      body: JSON.stringify({
        contraseña_actual: clave.actual,
        contraseña_nueva: clave.nueva,
      }),
    })
    clave.actual = ''
    clave.nueva = ''
    clave.confirmar = ''
    // EXPLICACIÓN: el backend purgó los refresh => otros dispositivos re-login
    info.value = 'Contraseña actualizada. Los demás dispositivos deberán iniciar sesión de nuevo.'
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail : 'No se pudo cambiar la contraseña.'
  } finally {
    guardandoClave.value = false
  }
}
</script>

<template>
  <div>
    <div class="encabezado">
      <div>
        <div class="migas">Cuenta · {{ etiquetaRol() }}</div>
        <h1>Mi perfil</h1>
      </div>
    </div>

    <div v-if="error" class="alerta-error">{{ error }}</div>
    <div v-if="info" class="alerta-info">{{ info }}</div>

    <div class="tarjeta">
      <h2>Datos de la cuenta</h2>
      <form @submit.prevent="guardarNombre">
        <div class="rejilla rejilla-2">
          <div class="campo">
            <label for="nombre">Nombre completo</label>
            <input
              id="nombre"
              v-model.trim="nombre"
              type="text"
              minlength="5"
              maxlength="150"
              required
              :disabled="cargando"
            />
          </div>
          <div class="campo">
            <label for="correo">Correo institucional</label>
            <!-- EXPLICACIÓN: el correo es la clave del JWT/login => solo lectura -->
            <input id="correo" :value="perfil?.correo_institucional ?? '—'" type="email" disabled />
          </div>
        </div>
        <button class="btn btn-primario" type="submit" :disabled="guardandoNombre || cargando">
          <Save v-if="!guardandoNombre" :size="15" />
          {{ guardandoNombre ? 'Guardando…' : 'Guardar nombre' }}
        </button>
      </form>
    </div>

    <div class="tarjeta tarjeta-flush mt-1">
      <h2><ShieldCheck :size="17" /> Cambiar contraseña</h2>
      <form @submit.prevent="cambiarClave">
        <div class="rejilla rejilla-2">
          <div class="campo">
            <label for="actual">Contraseña actual</label>
            <input
              id="actual"
              v-model="clave.actual"
              type="password"
              required
              minlength="8"
              autocomplete="current-password"
            />
          </div>
          <div class="campo">
            <label for="nueva">Contraseña nueva</label>
            <input
              id="nueva"
              v-model="clave.nueva"
              type="password"
              required
              minlength="8"
              autocomplete="new-password"
            />
          </div>
          <div class="campo">
            <label for="confirmar">Confirmar contraseña nueva</label>
            <input
              id="confirmar"
              v-model="clave.confirmar"
              type="password"
              required
              minlength="8"
              autocomplete="new-password"
            />
          </div>
        </div>
        <button class="btn btn-primario" type="submit" :disabled="guardandoClave">
          <KeyRound v-if="!guardandoClave" :size="15" />
          {{ guardandoClave ? 'Actualizando…' : 'Cambiar contraseña' }}
        </button>
      </form>
    </div>
  </div>
</template>
