// src/api/types.ts
/**
 * EXPLICACIÓN: Espejo tipado de los schemas Pydantic del backend;
 * si la API cambia, TypeScript señala dónde.
 */

export type Rol = 'aprendiz' | 'instructor' | 'coordinador'

export type EstadoEvidencia = 'Pendiente' | 'Aprobada' | 'Ajuste Requerido'

export interface ParTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface Perfil {
  id_usuario: number
  nombre_completo: string
  correo_institucional: string
  rol: Rol
}

export interface RegistroAprendiz {
  nombre_completo: string
  correo_institucional: string
  contraseña: string
  numero_documento: string
  numero_ficha: string
  programa: string
}

export interface RegistroInstructor {
  nombre_completo: string
  correo_institucional: string
  contraseña: string
  numero_documento: string
  centro_formacion: string
  especialidad: string
}

export interface RegistroCoordinador {
  nombre_completo: string
  correo_institucional: string
  contraseña: string
  numero_documento: string
  departamento: string
}

export interface Evidencia {
  id_evidencia: number
  titulo: string
  tipo_formato: string
  ruta_archivo_pdf: string
  estado: EstadoEvidencia
  fecha_carga: string
  fecha_deadline: string | null
}

export interface AvanceAprendiz {
  id_usuario: number
  nombre_completo: string
  numero_ficha: string
  programa: string
  total_evidencias: number
  aprobadas: number
  porcentaje_avance: number
}

export interface Alerta {
  id_evidencia: number
  titulo: string
  fecha_deadline: string
  dias_restantes: number
  estado_alerta: 'Vencida' | 'Por vencer'
}

export interface AlertaRol extends Alerta {
  nombre_aprendiz: string
}

export interface Notificacion {
  id_notificacion: number
  mensaje: string
  tipo: string
  id_evidencia: number | null
  leida: boolean
  fecha_creacion: string
}

export interface Retroalimentacion {
  id_retroalimentacion: number
  id_evidencia: number
  id_instructor: number
  observaciones: string
  estado_evaluacion: string
  fecha_revision: string
}

export interface Pagina<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface Estadisticas {
  total_evidencias: number
  aprobadas: number
  pendientes: number
  ajustes_requeridos: number
  total_aprendices: number
  total_instructores: number
  porcentaje_aprobacion: number
}

export interface EstadisticasInstructor {
  total_evaluadas: number
  aprobadas: number
  ajustes_requeridos: number
  pendientes_por_evaluar: number
}
