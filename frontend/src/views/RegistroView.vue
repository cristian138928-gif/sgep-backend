<script setup lang="ts">
// src/views/RegistroView.vue
// EXPLICACIÓN: un solo componente con pestañas por rol => evita 3 vistas casi idénticas
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ClipboardCheck, ShieldCheck, UserCheck } from 'lucide-vue-next'

import { ApiError } from '../api/client'
import AuthPanel from '../components/AuthPanel.vue'
import { rutaPorRol } from '../router'
import { useAuthStore } from '../stores/auth'

type TipoRegistro = 'aprendiz' | 'instructor' | 'coordinador'

const features = [
  { icono: ClipboardCheck, texto: 'Sube bitácoras y formatos en PDF con fecha límite' },
  { icono: ShieldCheck, texto: 'Tu avance y tus comentarios de revisión en un solo lugar' },
  { icono: UserCheck, texto: 'Instructor seguidor asignado desde el primer día' },
]

const router = useRouter()
const auth = useAuthStore()

const tipo = ref<TipoRegistro>('aprendiz')
const nombre = ref('')
const correo = ref('')
const documento = ref('')
const contraseña = ref('')
const confirmar = ref('')
const ficha = ref('')
const programa = ref('')
const centro = ref('')
const especialidad = ref('')
const departamento = ref('')

const error = ref('')
const cargando = ref(false)

const errorClave = computed(() => {
  if (contraseña.value && confirmar.value && contraseña.value !== confirmar.value) {
    return 'Las contraseñas no coinciden.'
  }
  return ''
})

async function enviar(): Promise<void> {
  error.value = ''
  if (errorClave.value) {
    error.value = errorClave.value
    return
  }
  cargando.value = true
  try {
    const base = {
      nombre_completo: nombre.value,
      correo_institucional: correo.value,
      contraseña: contraseña.value,
      numero_documento: documento.value,
    }
    let rol
    if (tipo.value === 'aprendiz') {
      rol = await auth.registrarAprendiz({
        ...base,
        numero_ficha: ficha.value,
        programa: programa.value,
      })
    } else if (tipo.value === 'instructor') {
      rol = await auth.registrarInstructor({
        ...base,
        centro_formacion: centro.value,
        especialidad: especialidad.value,
      })
    } else {
      rol = await auth.registrarCoordinador({ ...base, departamento: departamento.value })
    }
    await router.push(rutaPorRol(rol))
  } catch (e) {
    if (e instanceof ApiError && e.status === 409) {
      error.value = 'Ese correo institucional ya está registrado.'
    } else if (e instanceof ApiError && (e.status === 400 || e.status === 422)) {
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
    lema="Crea tu cuenta y registra tus evidencias"
    resaltado="en minutos"
    :features="features"
  >
    <div class="auth-tarjeta">
      <div class="auth-logo">SGE<span>P</span></div>
      <p class="auth-sub">Crea tu cuenta en el sistema</p>

      <div class="pestanas">
        <button
          type="button"
          :class="{ activa: tipo === 'aprendiz' }"
          @click="tipo = 'aprendiz'"
        >
          Aprendiz
        </button>
        <button
          type="button"
          :class="{ activa: tipo === 'instructor' }"
          @click="tipo = 'instructor'"
        >
          Instructor
        </button>
        <button
          type="button"
          :class="{ activa: tipo === 'coordinador' }"
          @click="tipo = 'coordinador'"
        >
          Coordinador
        </button>
      </div>

      <div v-if="error" class="alerta-error">{{ error }}</div>

      <form @submit.prevent="enviar">
        <div class="campo">
          <label for="nombre">Nombre completo</label>
          <input id="nombre" v-model.trim="nombre" type="text" required autofocus />
        </div>

        <div class="campo">
          <label for="correo">Correo institucional</label>
          <input id="correo" v-model.trim="correo" type="email" required autocomplete="email" />
        </div>

        <div class="campo">
          <label for="documento">Número de documento</label>
          <input id="documento" v-model.trim="documento" type="text" required />
        </div>

        <div v-if="tipo === 'aprendiz'" class="rejilla rejilla-2">
          <div class="campo">
            <label for="ficha">Número de ficha</label>
            <input id="ficha" v-model.trim="ficha" type="text" required />
          </div>
          <div class="campo">
            <label for="programa">Programa</label>
            <input id="programa" v-model.trim="programa" type="text" required />
          </div>
        </div>

        <div v-else-if="tipo === 'instructor'" class="rejilla rejilla-2">
          <div class="campo">
            <label for="centro">Centro de formación</label>
            <input id="centro" v-model.trim="centro" type="text" required />
          </div>
          <div class="campo">
            <label for="especialidad">Especialidad</label>
            <input id="especialidad" v-model.trim="especialidad" type="text" required />
          </div>
        </div>

        <div v-else class="campo">
          <label for="departamento">Departamento</label>
          <input id="departamento" v-model.trim="departamento" type="text" required />
        </div>

        <div class="campo">
          <label for="contraseña">Contraseña</label>
          <input
            id="contraseña"
            v-model="contraseña"
            type="password"
            required
            minlength="8"
            autocomplete="new-password"
          />
        </div>

        <div class="campo">
          <label for="confirmar">Confirmar contraseña</label>
          <input
            id="confirmar"
            v-model="confirmar"
            type="password"
            required
            autocomplete="new-password"
          />
        </div>

        <button
          class="btn btn-primario btn-ancho"
          type="submit"
          :disabled="cargando || !!errorClave"
        >
          {{ cargando ? 'Creando cuenta…' : 'Crear cuenta' }}
        </button>
      </form>

      <p class="auth-pie">
        ¿Ya tienes cuenta?
        <router-link to="/login">Inicia sesión</router-link>
      </p>
    </div>
  </AuthPanel>
</template>
