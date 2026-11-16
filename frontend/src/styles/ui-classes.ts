// src/styles/ui-classes.ts
// EXPLICACIÓN: cadenas de clase Tailwind de UI_GUIDELINES.md concentradas en un
// solo módulo => las vistas no duplican botones/píldoras y no pueden divergir.
import type { EstadoEvidencia } from '../api/types'

/** EXPLICACIÓN: primario sólido esmeralda (sin gradiente, como exige la guía) */
export const btnPrimario =
  'inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 font-sans text-sm font-medium text-white shadow-sm transition-all hover:bg-emerald-700 focus-visible:ring-2 focus-visible:ring-emerald-600/40 disabled:cursor-not-allowed disabled:opacity-60'

/** EXPLICACIÓN: secundario blanco con borde delgado => acción de bajo peso visual */
export const btnSecundario =
  'inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 font-sans text-sm font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-50 focus-visible:ring-2 focus-visible:ring-slate-400/40 disabled:cursor-not-allowed disabled:opacity-50'

/** EXPLICACIÓN: acento suave emerald-50 => acciones positivas no destructivas (exportar) */
export const btnSuave =
  'inline-flex items-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-1.5 font-sans text-sm font-medium text-emerald-700 transition-all hover:bg-emerald-100 focus-visible:ring-2 focus-visible:ring-emerald-600/40 disabled:cursor-not-allowed disabled:opacity-50'

/** EXPLICACIÓN: base de toda píldora de estado => borde suave + punto de color */
export const pillBase =
  'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold'

/** EXPLICACIÓN: paleta exacta de la guía: emerald (ok) / amber (pendiente) / rose (ajuste) */
export const clasesEstado: Record<EstadoEvidencia, string> = {
  Aprobada: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  Pendiente: 'border-amber-200 bg-amber-50 text-amber-700',
  'Ajuste Requerido': 'border-rose-200 bg-rose-50 text-rose-700',
}

/** EXPLICACIÓN: campo sin ancho fijo => selects en línea (asignaciones) heredan el mismo estilo */
export const inputBase =
  'rounded-lg border border-slate-300 bg-white px-3 py-2 font-sans text-sm text-slate-900 shadow-sm transition-colors outline-none focus:border-emerald-600 focus:ring-2 focus:ring-emerald-600/20'

/** EXPLICACIÓN: input unificado a ancho completo (blanco, borde slate-300, focus esmeralda) */
export const inputCampo = `w-full ${inputBase}`

/** EXPLICACIÓN: etiqueta en versalitas pequeñas slate-500 (cabeceras de tabla de la guía) */
export const etiquetaCampo =
  'mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-500'

/** EXPLICACIÓN: cabecera de tabla de la guía (una sola línea para no divergir) */
export const thTabla =
  'bg-slate-50/75 px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500'

/** EXPLICACIÓN: fila de tabla con hover sutil y transición suave */
export const trTabla = 'transition-colors hover:bg-slate-50/50'

/** EXPLICACI�N: contenedor de p�gina claro y tipograf�a base unificada */
export const paginaWrap = 'min-h-full bg-slate-50 font-sans text-slate-900'

/** EXPLICACI�N: cabecera de vista con separador inferior consistente */
export const cabeceraPagina =
  'mb-5 flex flex-wrap items-end justify-between gap-3 border-b border-slate-200 pb-4'

/** EXPLICACI�N: caja de icono de cabecera (tono emerald corporativo) */
export const iconoCaja =
  'flex h-10 w-10 flex-none items-center justify-center rounded-lg border border-emerald-200 bg-emerald-50 text-emerald-700'

/** EXPLICACI�N: chip contador/estado neutro reutilizable */
export const chipNeutro =
  'inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-600 shadow-sm'

/** EXPLICACI�N: banners de feedback sem�nticos (rose error, emerald info/�xito) */
export const alertaError =
  'mb-4 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm font-medium text-rose-700'
export const alertaInfo =
  'mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm font-medium text-emerald-700'

/** EXPLICACI�N: tarjeta/panel blanco est�ndar de la gu�a */
export const tarjeta = 'rounded-xl border border-slate-200 bg-white p-4 shadow-sm'
