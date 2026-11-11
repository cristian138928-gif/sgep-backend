// src/api/foto.ts
/**
 * EXPLICACIÓN: el backend aún no expone endpoint de avatar => la fotografía de
 * perfil se valida, se recorta y se persiste en localStorage (100% cliente),
 * con una versión reactiva para que el navbar la refresque al instante.
 */
import { ref } from 'vue'

/** EXPLICACIÓN: contador reactivo => el navbar repinta la foto sin recargar la ruta */
export const versionFoto = ref(0)

const clave = (id: number): string => `sgep.foto.${id}`

/**
 * EXPLICACIÓN: recorte cuadrado centrado + reescalado a 256px => avatar nítido
 * en el navbar (36px) y dataURL de ~15 KB en lugar de varios MB.
 */
export async function recortarAvatar(archivo: File, lado = 256): Promise<string> {
  const url = URL.createObjectURL(archivo)
  try {
    const img = await new Promise<HTMLImageElement>((resolver, rechazar) => {
      const elemento = new Image()
      elemento.onload = () => resolver(elemento)
      elemento.onerror = () => rechazar(new Error('No se pudo leer la imagen.'))
      elemento.src = url
    })
    const lienzo = document.createElement('canvas')
    lienzo.width = lado
    lienzo.height = lado
    const ctx = lienzo.getContext('2d')
    if (!ctx) throw new Error('Canvas no disponible.')
    const recorte = Math.min(img.naturalWidth, img.naturalHeight)
    ctx.drawImage(
      img,
      (img.naturalWidth - recorte) / 2,
      (img.naturalHeight - recorte) / 2,
      recorte,
      recorte,
      0,
      0,
      lado,
      lado,
    )
    return lienzo.toDataURL('image/jpeg', 0.85)
  } finally {
    URL.revokeObjectURL(url)
  }
}

/** EXPLICACIÓN: lectura tolerante => modo privado o cuota llena nunca rompen la UI */
export function leerFoto(id: number | null | undefined): string {
  if (!id) return ''
  try {
    return localStorage.getItem(clave(id)) ?? ''
  } catch {
    return ''
  }
}

/** EXPLICACIÓN: false = almacenamiento local no disponible (la vista lo reporta) */
export function escribirFoto(id: number, dataUrl: string): boolean {
  try {
    localStorage.setItem(clave(id), dataUrl)
    versionFoto.value += 1
    return true
  } catch {
    return false
  }
}

export function borrarFoto(id: number): void {
  try {
    localStorage.removeItem(clave(id))
    versionFoto.value += 1
  } catch {
    /* EXPLICACIÓN: sin storage no hay nada que borrar */
  }
}
