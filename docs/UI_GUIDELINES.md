# Directrices de Diseño UI - SGEP (referencia)

> **Fuente normativa:** `AGENTS.md`. Implementación canónica: `frontend/src/styles/ui-classes.ts`, `frontend/src/styles/main.css`, `frontend/src/styles/tailwind.css`.

## 1. Filosofía Visual

- **Estilo:** Enterprise Moderno / Clean Dashboard. Evitar diseños recargados, sombras excesivas o colores saturados estilo "juguete".
- **Enfoque:** Jerarquía clara, legibilidad alta, uso inteligente de espacios en blanco (padding/margin generosos) y alineación estricta.

## 2. Paleta de Colores

- **Fondo General (Background):** `bg-slate-50` (`#f8fafc`) para dar una sensación de espacio limpio.
- **Contenedores / Tarjetas:** `bg-white` con bordes sutiles `border border-slate-200` y esquinas redondeadas (`rounded-xl` o `rounded-lg`).
- **Textos:**
  - Títulos principales: `text-slate-900` (Negro suave / gris muy oscuro).
  - Textos secundarios / descripciones: `text-slate-500` o `text-slate-600`.
- **Color Primario (Acento institucional / SENA):** Verde esmeralda corporativo (`emerald-600` para botones principales, `emerald-700` en hover).
- **Colores de Estado (Badges):**
  - _Aprobado / Entregado:_ Fondo `bg-emerald-50`, texto `text-emerald-700`, borde `border-emerald-200`.
  - _Por revisar / Pendiente:_ Fondo `bg-amber-50`, texto `text-amber-700`, borde `border-amber-200`.
  - _Observaciones / Rechazado:_ Fondo `bg-rose-50`, texto `text-rose-700`, borde `border-rose-200`.

## 3. Componentes Base

- **Sidebar (Navegación lateral):** Fondo oscuro sólido (`slate-900` o `slate-950`), textos en `slate-300`, estados activos con acento en verde suave o fondo `slate-800` con texto blanco.
- **Tablas de Datos:**
  - Cabeceras con fondo gris muy suave (`bg-slate-50/75`), texto en mayúsculas pequeñas, negrita y color `text-slate-500`.
  - Filas con separadores delgados (`divide-y divide-slate-100`) y efecto hover sutil (`hover:bg-slate-50/50`).
- **Botones:**
  - Primarios: `bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg px-4 py-2 shadow-sm transition-all`.
  - Secundarios: `bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-medium rounded-lg px-4 py-2 transition-all`.
