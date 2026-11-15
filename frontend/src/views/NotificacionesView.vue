<script setup lang="ts">
// src/views/NotificacionesView.vue
import { onMounted, ref } from 'vue'
import { Bell, BellOff, Check, CheckCheck } from 'lucide-vue-next'

import type { Notificacion } from '../api/types'
import VacioEstado from '../components/VacioEstado.vue'
import { useNotificacionesStore } from '../stores/notificaciones'
import { btnSecundario, pillBase } from '../styles/ui-classes'

const store = useNotificacionesStore()
const marcando = ref<number | null>(null)

onMounted(() => { void store.refrescar() })

async function marcar(id: number): Promise<void> {
  marcando.value = id
  try { await store.marcarLeida(id) } finally { marcando.value = null }
}

function fechaCorta(n: Notificacion): string {
  return new Date(n.fecha_creacion).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })
}

const clasesTipo: Record<string, string> = {
  evaluacion: 'border-amber-200 bg-amber-50 text-amber-700',
  vencimiento: 'border-rose-200 bg-rose-50 text-rose-700',
  sistema: 'border-emerald-200 bg-emerald-50 text-emerald-700',
}
const tipoDesconocido = 'border-slate-200 bg-slate-50 text-slate-600'
</script>

<template>
  <div class="min-h-full bg-slate-50 font-sans text-slate-900">
    <header class="hero">
      <div class="hero-left">
        <span class="hero-icon" aria-hidden="true"><Bell :size="20" /></span>
        <div>
          <div class="migas">Central de avisos</div>
          <h1>Notificaciones</h1>
          <p class="hero-sub">Resultados de evaluaciones, vencimientos y avisos del sistema.</p>
        </div>
      </div>
      <div class="hero-actions">
        <span class="hero-chip"><Bell :size="13" /> {{ store.noLeidas }} sin leer</span>
        <button :class="btnSecundario" type="button" :disabled="store.noLeidas === 0" @click="store.marcarTodas()">
          <CheckCheck :size="15" /> Marcar todas como leídas
        </button>
      </div>
    </header>

    <section v-if="store.items.length === 0" class="rounded-xl border border-slate-200 bg-white shadow-sm">
      <VacioEstado :icono="BellOff" titulo="No tienes notificaciones" texto="Aqu? aparecer?n los resultados de tus evaluaciones y avisos de vencimiento." />
    </section>

    <section v-else class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div class="divide-y divide-slate-100">
        <article
          v-for="n in store.items"
          :key="n.id_notificacion"
          class="notif-item"
          :class="{ unread: !n.leida }"
        >
          <div class="notif-main">
            <div class="notif-dot" :class="n.leida ? 'dot-read' : 'dot-unread'" aria-hidden="true"></div>
            <div class="min-w-0">
              <p class="notif-msg">{{ n.mensaje }}</p>
              <p class="notif-date">{{ fechaCorta(n) }}</p>
            </div>
          </div>
          <div class="notif-actions">
            <span :class="[pillBase, clasesTipo[n.tipo] ?? tipoDesconocido]">{{ n.tipo }}</span>
            <button v-if="!n.leida" :class="btnSecundario" type="button" :disabled="marcando === n.id_notificacion" @click="marcar(n.id_notificacion)">
              <Check :size="15" /> Marcar leída
            </button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; flex-wrap:wrap; margin-bottom:1.25rem; padding-bottom:1rem; border-bottom:1px solid #e2e8f0; }
.hero-left { display:flex; align-items:center; gap:.75rem; }
.hero-icon { width:40px; height:40px; border-radius:10px; display:grid; place-items:center; background:#ecfdf5; color:#059669; border:1px solid #a7f3d0; }
.hero h1 { margin:.1rem 0 .2rem; font-size:1.55rem; color:#0f172a; }
.hero-sub { margin:0; color:#64748b; font-size:.9rem; }
.hero-actions { display:flex; align-items:center; gap:.5rem; flex-wrap:wrap; }
.hero-chip { display:inline-flex; align-items:center; gap:.4rem; padding:.35rem .65rem; border-radius:999px; border:1px solid #e2e8f0; background:#fff; color:#475569; font-size:.78rem; font-weight:600; box-shadow:0 1px 2px rgba(15,23,42,.04); }
.notif-item { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding: .9rem 1rem; transition: background .15s; }
.notif-item:hover { background:#f8fafc; }
.notif-item.unread { background:#f0fdf4; }
.notif-main { display:flex; align-items:flex-start; gap:.7rem; min-width:0; flex:1; }
.notif-dot { width:9px; height:9px; border-radius:999px; margin-top:.35rem; flex:none; }
.dot-unread { background:#10b981; box-shadow:0 0 0 4px rgba(16,185,129,.15); }
.dot-read { background:#cbd5e1; }
.notif-msg { margin:0; font-size:.9rem; font-weight:600; color:#0f172a; }
.notif-date { margin:.2rem 0 0; font-size:.78rem; color:#64748b; }
.notif-actions { display:flex; align-items:center; gap:.5rem; flex:none; flex-wrap:wrap; justify-content:flex-end; }
@media (max-width: 700px) { .notif-item { flex-direction:column; align-items:stretch; } .notif-actions { justify-content:flex-start; } }
</style>
