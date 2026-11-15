<script setup lang="ts">
// src/views/RegistroView.vue
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ClipboardCheck, ShieldCheck, UserCheck } from 'lucide-vue-next'

import { ApiError } from '../api/client'
import AuthPanel from '../components/AuthPanel.vue'
import sgepLogo from '../assets/imagenes/sgep-logo.jpg'
import { rutaPorRol } from '../router'
import { useAuthStore } from '../stores/auth'

type TipoRegistro = 'aprendiz' | 'instructor' | 'coordinador'

const features = [
  { icono: ClipboardCheck, texto: 'Sube bit\u00e1coras y formatos en PDF con fecha l\u00edmite' },
  { icono: ShieldCheck, texto: 'Tu avance y tus comentarios de revisi\u00f3n en un solo lugar' },
  { icono: UserCheck, texto: 'Instructor seguidor asignado desde el primer d\u00eda' },
]

const router = useRouter()
const auth = useAuthStore()

const tipo = ref<TipoRegistro>('aprendiz')
const nombre = ref('')
const correo = ref('')
const documento = ref('')
const contrasena = ref('')
const confirmar = ref('')
const ficha = ref('')
const programa = ref('')
const centro = ref('')
const especialidad = ref('')
const departamento = ref('')

const error = ref('')
const cargando = ref(false)

const errorClave = computed(() => {
  if (contrasena.value && confirmar.value && contrasena.value !== confirmar.value) {
    return 'Las contrase\u00f1as no coinciden.'
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
      ['contrase\u00f1a']: contrasena.value,
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
      error.value = 'Ese correo institucional ya est\u00e1 registrado.'
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
      <img
        :src="sgepLogo"
        alt="SGEP"
        class="h-24 w-auto rounded-xl border border-slate-200 object-cover"
      />
      <p class="auth-sub">Crea tu cuenta en el sistema</p>

      <div class="pestanas">
        <button type="button" :class="{ activa: tipo === 'aprendiz' }" @click="tipo = 'aprendiz'">Aprendiz</button>
        <button type="button" :class="{ activa: tipo === 'instructor' }" @click="tipo = 'instructor'">Instructor</button>
        <button type="button" :class="{ activa: tipo === 'coordinador' }" @click="tipo = 'coordinador'">Coordinador</button>
      </div>

      <div v-if="error" class="alerta-error" role="alert">{{ error }}</div>

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
          <label for="documento">N\u00famero de documento</label>
          <input id="documento" v-model.trim="documento" type="text" required />
        </div>

        <div v-if="tipo === 'aprendiz'" class="rejilla rejilla-2">
          <div class="campo">
            <label for="ficha">N\u00famero de ficha</label>
            <input id="ficha" v-model.trim="ficha" type="text" required />
          </div>
          <div class="campo">
            <label for="programa">Programa</label>
            <input id="programa" v-model.trim="programa" type="text" required />
          </div>
        </div>

        <div v-else-if="tipo === 'instructor'" class="rejilla rejilla-2">
          <div class="campo">
            <label for="centro">Centro de formaci\u00f3n</label>
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
          <label for="contraseña">Contrase\u00f1a</label>
          <input id="contraseña" v-model="contrasena" type="password" required minlength="8" autocomplete="new-password" />
        </div>

        <div class="campo">
          <label for="confirmar">Confirmar contrase\u00f1a</label>
          <input id="confirmar" v-model="confirmar" type="password" required autocomplete="new-password" />
        </div>

        <button class="btn btn-primario btn-ancho" type="submit" :disabled="cargando || !!errorClave">
          {{ cargando ? 'Creando cuenta\u2026' : 'Crear cuenta' }}
        </button>
      </form>

      <p class="auth-pie">
        \u00bfYa tienes cuenta?
        <router-link to="/login">Inicia sesi\u00f3n</router-link>
      </p>
    </div>
  </AuthPanel>
</template>
