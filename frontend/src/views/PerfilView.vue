<script setup lang="ts">
// src/views/PerfilView.vue
// EXPLICACIÓN: perfil de los 3 roles — foto local + nombre editable + cambio de contraseña
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { Camera, KeyRound, Save, ShieldCheck, Trash2, Upload } from 'lucide-vue-next'

import { api, ApiError } from '../api/client'
import { borrarFoto, escribirFoto, leerFoto, recortarAvatar } from '../api/foto'
import type { Instructor, Perfil } from '../api/types'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

const perfil = ref<Perfil | null>(null)
// EXPLICACIÓN: datos del instructor (centro/especialidad) no viajan en /auth/me
const perfilInstructor = ref<Instructor | null>(null)
const nombre = ref('')
const cargando = ref(true)

const error = ref('')
const info = ref('')

const clave = reactive({ actual: '', nueva: '', confirmar: '' })
const guardandoNombre = ref(false)
const guardandoClave = ref(false)

// EXPLICACIÓN: foto = archivo elegido (aún sin guardar) + URL de vista previa circular
const archivoFoto = ref<File | null>(null)
const fotoUrl = ref('')
const urlPendiente = ref('')
const MAXIMO_FOTO = 2 * 1024 * 1024

const etiquetaRol = () => auth.rol ?? 'usuario'

/** EXPLICACIÓN: respaldo con iniciales mientras no haya foto (mismo lenguaje que el navbar) */
const iniciales = computed(() => {
  const partes = (nombre.value || perfil.value?.nombre_completo || '').trim().split(/\s+/).slice(0, 2)
  if (!partes[0]) return '??'
  return partes.map((p) => p[0]?.toUpperCase() ?? '').join('')
})

onMounted(async () => {
  try {
    perfil.value = await api<Perfil>('/api/v1/auth/me')
    nombre.value = perfil.value.nombre_completo
    fotoUrl.value = leerFoto(perfil.value.id_usuario)
    if (auth.rol === 'instructor') {
      // EXPLICACIÓN: endpoint propio del rol; solo el instructor lo consume
      perfilInstructor.value = await api<Instructor>('/api/v1/instructor/perfil')
    }
  } catch {
    error.value = 'No se pudo cargar tu perfil.'
  } finally {
    cargando.value = false
  }
})

// EXPLICACIÓN: liberar el objectURL evita fuga de memoria en cada cambio de foto
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
  // EXPLICACIÓN: objectURL => vista previa instantánea sin leer el archivo en el hilo principal
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
    // EXPLICACIÓN: recorte a 256px antes de persistir => cuota mínima y recorte circular exacto
    const dataUrl = await recortarAvatar(archivoFoto.value)
    if (!escribirFoto(perfil.value.id_usuario, dataUrl)) {
      error.value = 'No se pudo guardar la fotografía (almacenamiento local no disponible).'
      return
    }
    liberarUrlPendiente()
    fotoUrl.value = dataUrl
    archivoFoto.value = null
    info.value = 'Fotografía actualizada. Ya se muestra en tu navbar.'
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
      <h2><Camera :size="17" /> Fotografía de perfil</h2>
      <div class="flex flex-wrap items-center gap-5">
        <!-- EXPLICACIÓN: preview circular con las mismas clases del avatar del navbar -->
        <div class="flex-none">
          <img
            v-if="fotoUrl"
            :src="fotoUrl"
            alt="Vista previa de tu fotografía"
            class="h-24 w-24 rounded-full border border-slate-200 object-cover bg-slate-50"
          />
          <span
            v-else
            class="flex h-24 w-24 items-center justify-center rounded-full border border-slate-200 bg-slate-200 text-2xl font-semibold text-slate-700"
            aria-hidden="true"
          >
            {{ iniciales }}
          </span>
        </div>

        <div class="ancho-max">
          <p class="texto-suave sin-margen">
            JPG, PNG o WEBP de máximo 2 MB. Se recorta en círculo para el navbar y las listas.
          </p>
          <div class="acciones mt-4">
            <label class="btn btn-suave" for="foto">
              <Upload :size="15" />
              Elegir archivo
              <input
                id="foto"
                type="file"
                accept="image/*"
                class="sr-only"
                @change="seleccionarFoto"
              />
            </label>
            <button
              v-if="archivoFoto"
              class="btn btn-primario"
              type="button"
              @click="guardarFoto"
            >
              <Save :size="15" />
              Guardar foto
            </button>
            <button
              v-if="fotoUrl && !archivoFoto"
              class="btn"
              type="button"
              @click="quitarFoto"
            >
              <Trash2 :size="15" />
              Quitar
            </button>
          </div>
          <p class="dato mt-2">
            {{ archivoFoto ? archivoFoto.name : fotoUrl ? 'Foto guardada en este dispositivo' : 'Sin fotografía' }}
          </p>
        </div>
      </div>
    </div>

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
          <template v-if="perfilInstructor">
            <div class="campo">
              <label for="centro">Centro de formación</label>
              <input id="centro" :value="perfilInstructor.centro_formacion" type="text" disabled />
            </div>
            <div class="campo">
              <label for="especialidad">Especialidad</label>
              <input id="especialidad" :value="perfilInstructor.especialidad" type="text" disabled />
            </div>
          </template>
        </div>
        <button class="btn btn-primario" type="submit" :disabled="guardandoNombre || cargando">
          <Save v-if="!guardandoNombre" :size="15" />
          {{ guardandoNombre ? 'Guardando…' : 'Guardar nombre' }}
        </button>
      </form>
    </div>

    <div class="tarjeta tarjeta-flush mt-4">
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
