<script setup lang="ts">
// src/views/instructor/EvaluarView.vue
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { CheckCircle2, ClipboardCheck, FileText, RotateCcw, Send, X } from 'lucide-vue-next'

import { api, ApiError } from '../../api/client'
import type { Evidencia, Retroalimentacion } from '../../api/types'

const props = defineProps<{ id: string }>()
const router = useRouter()

const estado = ref<'Aprobada' | 'Ajuste Requerido'>('Aprobada')
const observaciones = ref('')
const error = ref('')
const enviando = ref(false)

const meta = ref<Pick<Evidencia, 'titulo' | 'tipo_formato' | 'fecha_deadline'> | null>(
  (history.state as { evidencia?: Pick<Evidencia, 'titulo' | 'tipo_formato' | 'fecha_deadline'> })
    .evidencia ?? null,
)

const chars = computed(() => observaciones.value.trim().length)
const valido = computed(() => chars.value >= 10 && chars.value <= 1000)

onMounted(async () => {
  if (meta.value) return
  try {
    meta.value = await api<Evidencia>(`/api/v1/evidencias/${props.id}`)
  } catch {
    // sin metadatos aún se puede evaluar
  }
})

async function enviar(): Promise<void> {
  error.value = ''
  if (!valido.value) {
    error.value = 'Las observaciones deben tener al menos 10 caracteres (máximo 1000).'
    return
  }
  enviando.value = true
  try {
    await api<Retroalimentacion>(`/api/v1/instructor/evaluar/${props.id}`, {
      method: 'PUT',
      body: JSON.stringify({ estado: estado.value, observaciones: observaciones.value.trim() }),
    })
    await router.push({ name: 'pendientes' })
  } catch (e) {
    if (e instanceof ApiError && e.status === 409) {
      error.value = 'Esta evidencia ya fue evaluada.'
      setTimeout(() => void router.push({ name: 'pendientes' }), 1500)
    } else if (e instanceof ApiError) {
      error.value = e.detail
    } else {
      error.value = 'No se pudo registrar la evaluación.'
    }
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <div>
    <header class="hero">
      <div>
        <div class="migas">Instructor · Evaluación</div>
        <h1>Evaluar evidencia #{{ id }}</h1>
        <p class="hero-sub">Registra una decisión clara y retroalimentación útil para el aprendiz.</p>
      </div>
      <div class="hero-chip"><ClipboardCheck :size="14" /> Requisito RF03</div>
    </header>

    <div v-if="error" class="alerta-error" role="alert">{{ error }}</div>

    <section class="grid-eval">
      <article class="tarjeta">
        <div class="panel-head">
          <div>
            <div class="migas">Detalle</div>
            <h2 class="m-0">{{ meta?.titulo || `Evidencia #${id}` }}</h2>
          </div>
          <span class="tipo-badge"><FileText :size="14" /> {{ meta?.tipo_formato || 'Evidencia' }}</span>
        </div>
        <div class="meta-grid">
          <div class="meta-item"><span>Identificador</span><strong>#{{ id }}</strong></div>
          <div class="meta-item"><span>Tipo</span><strong>{{ meta?.tipo_formato || '—' }}</strong></div>
          <div class="meta-item"><span>Fecha límite</span><strong>{{ meta?.fecha_deadline ? meta.fecha_deadline.slice(0,10) : '—' }}</strong></div>
        </div>
        <p v-if="!meta" class="texto-suave mt-4">Cargando metadatos adicionales…</p>
      </article>

      <article class="tarjeta">
        <div class="migas">Decisión</div>
        <h2>Registrar evaluación</h2>
        <form @submit.prevent="enviar" class="form-eval">
          <div class="decision-grid">
            <label class="decision" :class="{ activa: estado === 'Aprobada' }">
              <input v-model="estado" type="radio" value="Aprobada" required />
              <span class="decision-icon ok"><CheckCircle2 :size="18" /></span>
              <span class="decision-body"><strong>Aprobada</strong><small>Cumple los criterios establecidos.</small></span>
            </label>
            <label class="decision" :class="{ activa: estado === 'Ajuste Requerido' }">
              <input v-model="estado" type="radio" value="Ajuste Requerido" required />
              <span class="decision-icon warn"><RotateCcw :size="18" /></span>
              <span class="decision-body"><strong>Ajuste requerido</strong><small>Debe corregirse antes de aprobar.</small></span>
            </label>
          </div>

          <div class="campo">
            <div class="label-row">
              <label for="observaciones">Observaciones</label>
              <span class="contador" :class="{ ok: valido, bad: chars > 0 && !valido }">{{ chars }}/1000</span>
            </div>
            <textarea
              id="observaciones"
              v-model="observaciones"
              rows="6"
              minlength="10"
              maxlength="1000"
              required
              placeholder="Describe claramente qué está correcto y, si aplica, qué debe ajustar el aprendiz…"
            />
            <p class="ayuda">Mínimo 10 caracteres. Sé específico y constructivo.</p>
          </div>

          <div class="fila">
            <button class="btn btn-primario" type="submit" :disabled="enviando || !valido">
              <Send v-if="!enviando" :size="15" />
              {{ enviando ? 'Guardando…' : 'Registrar evaluación' }}
            </button>
            <button class="btn" type="button" @click="router.push({ name: 'pendientes' })">
              <X :size="15" />
              Cancelar
            </button>
          </div>
        </form>
      </article>
    </section>
  </div>
</template>

<style scoped>
.hero { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; flex-wrap:wrap; margin-bottom:1.25rem; padding-bottom:1rem; border-bottom:1px solid var(--borde); }
.hero h1 { margin:.1rem 0 .2rem; font-size:1.55rem; }
.hero-sub { margin:0; color:var(--texto-suave); font-size:.9rem; }
.hero-chip { display:inline-flex; align-items:center; gap:.4rem; padding:.35rem .65rem; border-radius:999px; border:1px solid #bfdbfe; background:#eff6ff; color:#1d4ed8; font-size:.75rem; font-weight:700; }
.grid-eval { display:grid; grid-template-columns: minmax(260px,.9fr) minmax(0,1.4fr); gap:1rem; align-items:start; }
.panel-head { display:flex; align-items:flex-start; justify-content:space-between; gap:.8rem; margin-bottom:.8rem; }
.tipo-badge { display:inline-flex; align-items:center; gap:.35rem; padding:.25rem .55rem; border-radius:999px; border:1px solid var(--borde); background:#f8fafc; color:var(--texto-suave); font-size:.75rem; font-weight:600; }
.meta-grid { display:grid; gap:.5rem; }
.meta-item { display:flex; justify-content:space-between; gap:1rem; padding:.55rem .65rem; border:1px solid #e2e8f0; border-radius:10px; background:#f8fafc; font-size:.86rem; }
.meta-item span { color:var(--texto-suave); }
.meta-item strong { font-family:var(--fuente-mono); color:var(--texto); }
.form-eval { display:grid; gap:1rem; }
.decision-grid { display:grid; grid-template-columns:1fr 1fr; gap:.7rem; }
.decision { position:relative; display:grid; grid-template-columns:36px 1fr; gap:.6rem; align-items:start; padding:.75rem; border:1px solid #e2e8f0; border-radius:12px; background:#fff; cursor:pointer; transition:.15s ease; }
.decision input { position:absolute; opacity:0; pointer-events:none; }
.decision:hover { border-color:#cbd5e1; background:#f8fafc; }
.decision.activa { border-color:#6ee7b7; background:#ecfdf5; box-shadow:0 0 0 2px rgba(16,185,129,.08); }
.decision-icon { width:36px; height:36px; border-radius:10px; display:grid; place-items:center; border:1px solid; }
.decision-icon.ok { color:#059669; background:#ecfdf5; border-color:#a7f3d0; }
.decision-icon.warn { color:#d97706; background:#fffbeb; border-color:#fde68a; }
.decision-body { display:grid; gap:.15rem; }
.decision-body small { color:var(--texto-suave); }
.label-row { display:flex; align-items:center; justify-content:space-between; gap:.5rem; }
.contador { font-family:var(--fuente-mono); font-size:.75rem; color:var(--texto-suave); }
.contador.ok { color:#047857; }
.contador.bad { color:#be123c; }
.ayuda { margin:.35rem 0 0; font-size:.78rem; color:var(--texto-suave); }
@media (max-width: 900px) { .grid-eval, .decision-grid { grid-template-columns:1fr; } }
</style>
