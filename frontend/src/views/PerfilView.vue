<script setup lang="ts">
// src/views/PerfilView.vue
// EXPLICACIÓN: perfil de los 3 roles - foto local + nombre editable + cambio de contraseña
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { Camera, KeyRound, Mail, Save, ShieldCheck, Trash2, Upload, User } from 'lucide-vue-next'

import { api, ApiError } from '../api/client'
import { borrarFoto, escribirFoto, leerFoto, recortarAvatar } from '../api/foto'
import type { Instructor, Perfil } from '../api/types'
import { useAuthStore } from '../stores/auth'
import {
  alertaError,
  alertaInfo,
  btnPrimario,
  btnSecundario,
  btnSuave,
  cabeceraPagina,
  chipNeutro,
  etiquetaCampo,
  iconoCaja,
  inputCampo,
  paginaWrap,
  tarjeta,
} from '../styles/ui-classes'

const auth = useAuthStore()

const perfil = ref<Perfil | null>(null)
const perfilInstructor = ref<Instructor | null>(null)
const nombre = ref('')
const cargando = ref(true)

const error = ref('')
const info = ref('')

const clave = reactive({ actual: '', nueva: '', confirmar: '' })
const guardandoNombre = ref(false)
const guardandoClave = ref(false)

const archivoFoto = ref<File | null>(null)
const fotoUrl = ref('')
const urlPendiente = ref('')
const MAXIMO_FOTO = 2 * 1024 * 1024

const etiquetaRol = () => auth.rol ?? 'usuario'

const iniciales = computed(() => {
  const partes = (nombre.value || perfil.value?.nombre_completo || '').trim().split(/\s+/).slice(0, 2)
  if (!partes[0]) return 'U'
  return partes.map((p) => p[0]?.toUpperCase() ?? '').join('')
})

onMounted(async () => {
  try {
    perfil.value = await api<Perfil>('/api/v1/auth/me')
    nombre.value = perfil.value.nombre_completo
    fotoUrl.value = leerFoto(perfil.value.id_usuario)
    if (auth.rol === 'instructor') {
      perfilInstructor.value = await api<Instructor>('/api/v1/instructor/perfil')
    }
  } catch {
    error.value = 'No se pudo cargar tu perfil.'
  } finally {
    cargando.value = false
  }
})

function liberarUrlPendiente(): void {
  if (urlPendiente.value) {
    URL.revokeObjectURL(urlPendiente.value)
    urlPendiente.value = ''
  }
}

onBeforeUnmount(liberarUrlPendiente)

function seleccionarFoto(event: Event): void {
  const input = event.target as HTMLInputElement
  const archivo = input.files?.[0] ?? null
  error.value = ''
  info.value = ''
  if (!archivo) return
  if (!archivo.type.startsWith('image/')) {
    error.value = 'Selecciona un archivo de imagen (JPG, PNG o WEBP).'
    input.value = ''
    return
  }
  if (archivo.size > MAXIMO_FOTO) {
    error.value = 'La fotografía no puede superar 2 MB.'
    input.value = ''
    return
  }
  archivoFoto.value = archivo
  liberarUrlPendiente()
  urlPendiente.value = URL.createObjectURL(archivo)
  fotoUrl.value = urlPendiente.value
}

async function guardarFoto(): Promise<void> {
  error.value = ''
  info.value = ''
  if (!archivoFoto.value || !perfil.value) {
    error.value = 'Selecciona una fotografía primero.'
    return
  }
  try {
    const dataUrl = await recortarAvatar(archivoFoto.value)
    if (!escribirFoto(perfil.value.id_usuario, dataUrl)) {
      error.value = 'No se pudo guardar la fotografía (almacenamiento local no disponible).'
      return
    }
    liberarUrlPendiente()
    fotoUrl.value = dataUrl
    archivoFoto.value = null
    info.value = 'Fotografía actualizada. Ya se muestra en tu barra superior.'
  } catch {
    error.value = 'No se pudo procesar la fotografía.'
  }
}

function quitarFoto(): void {
  if (perfil.value) borrarFoto(perfil.value.id_usuario)
  liberarUrlPendiente()
  archivoFoto.value = null
  fotoUrl.value = ''
  info.value = 'Fotografía eliminada.'
}

async function guardarNombre(): Promise<void> {
  error.value = ''
  info.value = ''
  guardandoNombre.value = true
  try {
    perfil.value = await api<Perfil>('/api/v1/auth/me', {
      method: 'PUT',
      body: JSON.stringify({ nombre_completo: nombre.value }),
    })
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
    info.value = 'Contraseña actualizada. Los demás dispositivos deberán iniciar sesión de nuevo.'
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail : 'No se pudo cambiar la contraseña.'
  } finally {
    guardandoClave.value = false
  }
}
</script>

<template>
  <div :class="paginaWrap">
    <header :class="cabeceraPagina">
      <div class="flex items-center gap-3">
        <span :class="iconoCaja" aria-hidden="true"><User :size="20" /></span>
        <div>
          <p class="m-0 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Cuenta · {{ etiquetaRol() }}
          </p>
          <h1 class="m-0 text-2xl font-bold text-slate-900">Mi perfil</h1>
          <p class="m-0 mt-2 text-sm text-slate-500">
            Gestiona tu información personal, fotografía y seguridad de acceso.
          </p>
        </div>
      </div>
      <span :class="chipNeutro"><ShieldCheck :size="13" class="text-emerald-600" /> Sesión segura</span>
    </header>

    <div v-if="error" role="alert" class="alerta-error" :class="alertaError">{{ error }}</div>
    <div v-if="info" role="status" class="alerta-info" :class="alertaInfo">{{ info }}</div>

    <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <section :class="tarjeta">
        <div class="mb-4 flex items-center gap-3">
          <span :class="iconoCaja" aria-hidden="true"><Camera :size="18" /></span>
          <div>
            <h2 class="m-0 text-base font-semibold text-slate-900">Fotografía de perfil</h2>
            <p class="m-0 mt-0.5 text-sm text-slate-500">Imagen visible en la barra superior y listados.</p>
          </div>
        </div>
        <div class="flex flex-wrap items-center gap-4">
          <div class="h-24 w-24 flex-none">
            <img
              v-if="fotoUrl"
              :src="fotoUrl"
              alt="Vista previa de tu fotografía"
              class="h-24 w-24 rounded-full border border-slate-200 object-cover"
            />
            <span
              v-else
              class="flex h-24 w-24 items-center justify-center rounded-full border border-slate-200 bg-slate-200 text-2xl font-bold text-slate-700"
              aria-hidden="true"
            >{{ iniciales }}</span>
          </div>
          <div class="min-w-[240px] flex-1">
            <p class="m-0 text-sm text-slate-500">
              JPG, PNG o WEBP de máximo 2 MB. Se recorta automáticamente en formato circular.
            </p>
            <div class="mt-3 flex flex-wrap items-center gap-2">
              <label :class="btnSuave" for="foto">
                <Upload :size="15" /> Elegir archivo
                <input id="foto" type="file" accept="image/*" class="sr-only" @change="seleccionarFoto" />
              </label>
              <button v-if="archivoFoto" :class="btnPrimario" type="button" @click="guardarFoto">
                <Save :size="15" /> Guardar foto
              </button>
              <button v-if="fotoUrl && !archivoFoto" :class="btnSecundario" type="button" @click="quitarFoto">
                <Trash2 :size="15" /> Quitar
              </button>
            </div>
            <p class="m-0 mt-2 text-xs text-slate-500">
              {{ archivoFoto ? archivoFoto.name : fotoUrl ? 'Foto guardada en este dispositivo' : 'Sin fotografía' }}
            </p>
          </div>
        </div>
      </section>

      <section :class="tarjeta">
        <div class="mb-4 flex items-center gap-3">
          <span :class="iconoCaja" aria-hidden="true"><User :size="18" /></span>
          <div>
            <h2 class="m-0 text-base font-semibold text-slate-900">Datos de la cuenta</h2>
            <p class="m-0 mt-0.5 text-sm text-slate-500">Información básica asociada a tu usuario.</p>
          </div>
        </div>
        <form @submit.prevent="guardarNombre">
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label for="nombre" :class="etiquetaCampo">Nombre completo</label>
              <input
                id="nombre"
                v-model.trim="nombre"
                type="text"
                minlength="5"
                maxlength="150"
                required
                :disabled="cargando"
                :class="inputCampo"
              />
            </div>
            <div>
              <label for="correo" :class="etiquetaCampo">
                <Mail :size="12" class="mr-1 inline -translate-y-px" /> Correo institucional
              </label>
              <input
                id="correo"
                :value="perfil?.correo_institucional ?? '—'"
                type="email"
                disabled
                :class="[inputCampo, 'bg-slate-50 text-slate-500']"
              />
            </div>
            <template v-if="perfilInstructor">
              <div>
                <label for="centro" :class="etiquetaCampo">Centro de formación</label>
                <input id="centro" :value="perfilInstructor.centro_formacion" type="text" disabled :class="[inputCampo, 'bg-slate-50 text-slate-500']" />
              </div>
              <div>
                <label for="especialidad" :class="etiquetaCampo">Especialidad</label>
                <input id="especialidad" :value="perfilInstructor.especialidad" type="text" disabled :class="[inputCampo, 'bg-slate-50 text-slate-500']" />
              </div>
            </template>
          </div>
          <p class="mb-3 mt-2 text-xs text-slate-500">
            El correo institucional es tu identificador de acceso y no se puede modificar.
          </p>
          <button :class="btnPrimario" type="submit" :disabled="guardandoNombre || cargando">
            <Save v-if="!guardandoNombre" :size="15" />
            {{ guardandoNombre ? 'Guardando…' : 'Guardar nombre' }}
          </button>
        </form>
      </section>

      <section :class="[tarjeta, 'lg:col-span-2']">
        <div class="mb-4 flex items-center gap-3">
          <span :class="iconoCaja" aria-hidden="true"><ShieldCheck :size="18" /></span>
          <div>
            <h2 class="m-0 text-base font-semibold text-slate-900">Seguridad y contraseña</h2>
            <p class="m-0 mt-0.5 text-sm text-slate-500">Actualiza tu contraseña para mantener tu cuenta protegida.</p>
          </div>
        </div>
        <form @submit.prevent="cambiarClave">
          <div class="grid grid-cols-1 gap-3 md:grid-cols-3">
            <div>
              <label for="actual" :class="etiquetaCampo">Contraseña actual</label>
              <input
                id="actual"
                v-model="clave.actual"
                type="password"
                required
                minlength="8"
                autocomplete="current-password"
                :class="inputCampo"
              />
            </div>
            <div>
              <label for="nueva" :class="etiquetaCampo">Contraseña nueva</label>
              <input
                id="nueva"
                v-model="clave.nueva"
                type="password"
                required
                minlength="8"
                autocomplete="new-password"
                :class="inputCampo"
              />
            </div>
            <div>
              <label for="confirmar" :class="etiquetaCampo">Confirmar contraseña nueva</label>
              <input
                id="confirmar"
                v-model="clave.confirmar"
                type="password"
                required
                minlength="8"
                autocomplete="new-password"
                :class="inputCampo"
              />
            </div>
          </div>
          <p class="mb-3 mt-2 text-xs text-slate-500">
            Mínimo 8 caracteres. Al cambiarla, los demás dispositivos deberán iniciar sesión de nuevo.
          </p>
          <button :class="btnPrimario" type="submit" :disabled="guardandoClave">
            <KeyRound v-if="!guardandoClave" :size="15" />
            {{ guardandoClave ? 'Actualizando…' : 'Cambiar contraseña' }}
          </button>
        </form>
      </section>
    </div>
  </div>
</template>
