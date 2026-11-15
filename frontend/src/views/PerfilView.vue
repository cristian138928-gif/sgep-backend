<script setup lang="ts">
// src/views/PerfilView.vue
// EXPLICACI?N: perfil de los 3 roles - foto local + nombre editable + cambio de contrase?a
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { Camera, KeyRound, Mail, Save, ShieldCheck, Trash2, Upload, User } from 'lucide-vue-next'

import { api, ApiError } from '../api/client'
import { borrarFoto, escribirFoto, leerFoto, recortarAvatar } from '../api/foto'
import type { Instructor, Perfil } from '../api/types'
import { useAuthStore } from '../stores/auth'

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
    error.value = 'La fotograf?a no puede superar 2 MB.'
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
    error.value = 'Selecciona una fotograf?a primero.'
    return
  }
  try {
    const dataUrl = await recortarAvatar(archivoFoto.value)
    if (!escribirFoto(perfil.value.id_usuario, dataUrl)) {
      error.value = 'No se pudo guardar la fotograf?a (almacenamiento local no disponible).'
      return
    }
    liberarUrlPendiente()
    fotoUrl.value = dataUrl
    archivoFoto.value = null
    info.value = 'Fotograf?a actualizada. Ya se muestra en tu barra superior.'
  } catch {
    error.value = 'No se pudo procesar la fotograf?a.'
  }
}

function quitarFoto(): void {
  if (perfil.value) borrarFoto(perfil.value.id_usuario)
  liberarUrlPendiente()
  archivoFoto.value = null
  fotoUrl.value = ''
  info.value = 'Fotograf?a eliminada.'
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
    error.value = 'La contrase?a nueva debe tener al menos 8 caracteres.'
    return
  }
  if (clave.nueva !== clave.confirmar) {
    error.value = 'La confirmaci?n no coincide con la contrase?a nueva.'
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
    info.value = 'Contrase?a actualizada. Los dem?s dispositivos deber?n iniciar sesi?n de nuevo.'
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail : 'No se pudo cambiar la contrase?a.'
  } finally {
    guardandoClave.value = false
  }
}
</script>

<template>
  <div class="perfil-view">
    <header class="hero">
      <div>
        <div class="migas">Cuenta ? {{ etiquetaRol() }}</div>
        <h1>Mi perfil</h1>
        <p class="hero-sub">Gestiona tu informaci?n personal, fotograf?a y seguridad de acceso.</p>
      </div>
      <div class="hero-chip"><ShieldCheck :size="14" /> Sesi?n segura</div>
    </header>

    <div v-if="error" class="alerta-error" role="alert">{{ error }}</div>
    <div v-if="info" class="alerta-info" role="status">{{ info }}</div>

    <div class="perfil-grid">
      <section class="tarjeta perfil-card">
        <div class="card-head">
          <h2><Camera :size="17" /> Fotograf?a de perfil</h2>
          <p>Imagen visible en la barra superior y listados.</p>
        </div>
        <div class="foto-wrap">
          <div class="avatar-preview">
            <img v-if="fotoUrl" :src="fotoUrl" alt="Vista previa de tu fotografía" class="avatar-img rounded-full object-cover" />
            <span v-else class="avatar-fallback" aria-hidden="true">{{ iniciales }}</span>
          </div>
          <div class="foto-info">
            <p class="texto-suave">JPG, PNG o WEBP de m?ximo 2 MB. Se recorta autom?ticamente en formato circular.</p>
            <div class="acciones mt-3">
              <label class="btn btn-suave" for="foto">
                <Upload :size="15" /> Elegir archivo
                <input id="foto" type="file" accept="image/*" class="sr-only" @change="seleccionarFoto" />
              </label>
              <button v-if="archivoFoto" class="btn btn-primario" type="button" @click="guardarFoto">
                <Save :size="15" /> Guardar foto
              </button>
              <button v-if="fotoUrl && !archivoFoto" class="btn" type="button" @click="quitarFoto">
                <Trash2 :size="15" /> Quitar
              </button>
            </div>
            <p class="dato mt-2">
              {{ archivoFoto ? archivoFoto.name : fotoUrl ? 'Foto guardada en este dispositivo' : 'Sin fotograf?a' }}
            </p>
          </div>
        </div>
      </section>

      <section class="tarjeta perfil-card">
        <div class="card-head">
          <h2><User :size="17" /> Datos de la cuenta</h2>
          <p>Informaci?n b?sica asociada a tu usuario.</p>
        </div>
        <form @submit.prevent="guardarNombre">
          <div class="rejilla rejilla-2">
            <div class="campo">
              <label for="nombre">Nombre completo</label>
              <input id="nombre" v-model.trim="nombre" type="text" minlength="5" maxlength="150" required :disabled="cargando" />
            </div>
            <div class="campo">
              <label for="correo"><Mail :size="13" class="inline-icon" /> Correo institucional</label>
              <input id="correo" :value="perfil?.correo_institucional ?? '?'" type="email" disabled />
            </div>
            <template v-if="perfilInstructor">
              <div class="campo">
                <label for="centro">Centro de formaci?n</label>
                <input id="centro" :value="perfilInstructor.centro_formacion" type="text" disabled />
              </div>
              <div class="campo">
                <label for="especialidad">Especialidad</label>
                <input id="especialidad" :value="perfilInstructor.especialidad" type="text" disabled />
              </div>
            </template>
          </div>
          <p class="hint">El correo institucional es tu identificador de acceso y no se puede modificar.</p>
          <button class="btn btn-primario" type="submit" :disabled="guardandoNombre || cargando">
            <Save v-if="!guardandoNombre" :size="15" />
            {{ guardandoNombre ? 'Guardando?' : 'Guardar nombre' }}
          </button>
        </form>
      </section>

      <section class="tarjeta perfil-card full">
        <div class="card-head">
          <h2><ShieldCheck :size="17" /> Seguridad y contrase?a</h2>
          <p>Actualiza tu contrase?a para mantener tu cuenta protegida.</p>
        </div>
        <form @submit.prevent="cambiarClave">
          <div class="rejilla rejilla-3">
            <div class="campo">
              <label for="actual">Contrase?a actual</label>
              <input id="actual" v-model="clave.actual" type="password" required minlength="8" autocomplete="current-password" />
            </div>
            <div class="campo">
              <label for="nueva">Contrase?a nueva</label>
              <input id="nueva" v-model="clave.nueva" type="password" required minlength="8" autocomplete="new-password" />
            </div>
            <div class="campo">
              <label for="confirmar">Confirmar contrase?a nueva</label>
              <input id="confirmar" v-model="clave.confirmar" type="password" required minlength="8" autocomplete="new-password" />
            </div>
          </div>
          <p class="hint">M?nimo 8 caracteres. Al cambiarla, los dem?s dispositivos deber?n iniciar sesi?n de nuevo.</p>
          <button class="btn btn-primario" type="submit" :disabled="guardandoClave">
            <KeyRound v-if="!guardandoClave" :size="15" />
            {{ guardandoClave ? 'Actualizando?' : 'Cambiar contrase?a' }}
          </button>
        </form>
      </section>
    </div>
  </div>
</template>

<style scoped>
.perfil-view { display: grid; gap: 0; }
.hero { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; flex-wrap:wrap; margin-bottom:1.25rem; padding-bottom:1rem; border-bottom:1px solid var(--borde); }
.hero h1 { margin:.1rem 0 .2rem; font-size:1.55rem; }
.hero-sub { margin:0; color:var(--texto-suave); font-size:.9rem; }
.hero-chip { display:inline-flex; align-items:center; gap:.4rem; padding:.4rem .7rem; border-radius:999px; border:1px solid #a7f3d0; background:#ecfdf5; color:#047857; font-size:.78rem; font-weight:700; }
.perfil-grid { display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:1rem; }
.perfil-card.full { grid-column: 1 / -1; }
.card-head { margin-bottom: .9rem; }
.card-head h2 { display:flex; align-items:center; gap:.45rem; margin:0 0 .2rem; font-size:1rem; }
.card-head p { margin:0; color:var(--texto-suave); font-size:.85rem; }
.foto-wrap { display:flex; align-items:center; gap:1rem; flex-wrap:wrap; }
.avatar-preview { width:96px; height:96px; flex:none; }
.avatar-img, .avatar-fallback { width:96px; height:96px; border-radius:999px; border:1px solid #e2e8f0; object-fit:cover; }
.avatar-fallback { display:flex; align-items:center; justify-content:center; background:#e2e8f0; color:#334155; font-size:1.7rem; font-weight:700; }
.foto-info { flex:1; min-width:240px; }
.hint { margin:.1rem 0 .8rem; font-size:.8rem; color:var(--texto-suave); }
.inline-icon { vertical-align:-2px; margin-right:2px; }
.mt-3 { margin-top: .75rem; }
@media (max-width: 900px) { .perfil-grid { grid-template-columns: 1fr; } .perfil-card.full { grid-column: auto; } }
</style>
