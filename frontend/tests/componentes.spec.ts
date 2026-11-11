// frontend/tests/componentes.spec.ts
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import EstadoBadge from '../src/components/EstadoBadge.vue'
import AuthPanel from '../src/components/AuthPanel.vue'
import AvatarCirculo from '../src/components/AvatarCirculo.vue'
import AvatarNombre from '../src/components/AvatarNombre.vue'
import Esqueleto from '../src/components/Esqueleto.vue'
import KpiTarjeta from '../src/components/KpiTarjeta.vue'
import PaginacionBar from '../src/components/PaginacionBar.vue'
import VacioEstado from '../src/components/VacioEstado.vue'
import type { Component } from 'vue'

/** EXPLICACIÓN: icono falso liviano (lucide no aporta nada a la lógica testeada). */
const IconoFalso: Component = { name: 'IconoFalso', template: '<svg class="ico-falso" />' }

describe('AuthPanel', () => {
  it('renderiza lema, features y el hero SVG', () => {
    const wrapper = mount(AuthPanel, {
      props: {
        lema: 'Sistema de gestión',
        resaltado: 'de evidencias',
        features: [{ icono: IconoFalso, texto: 'Feature 1' }],
      },
      slots: { default: '<form />' },
    })

    expect(wrapper.text()).toContain('Sistema de gestión')
    expect(wrapper.text()).toContain('Feature 1')
    const hero = wrapper.find('img.auth-hero')
    expect(hero.exists()).toBe(true)
    // EXPLICACIÓN: Vite inlines SVGs pequeños como data-URL en el bundle de test
    expect(hero.attributes('src')).toMatch(/^data:image\/svg\+xml/)
  })
})

describe('EstadoBadge', () => {
  it('Aprobada usa la píldora esmeralda', () => {
    const wrapper = mount(EstadoBadge, { props: { estado: 'Aprobada' } })

    expect(wrapper.classes()).toContain('bg-emerald-50')
    expect(wrapper.classes()).toContain('border-emerald-200')
    expect(wrapper.text()).toBe('Aprobada')
  })

  it('Ajuste Requerido usa la píldora rosa', () => {
    const wrapper = mount(EstadoBadge, { props: { estado: 'Ajuste Requerido' } })

    expect(wrapper.classes()).toContain('bg-rose-50')
    expect(wrapper.classes()).toContain('border-rose-200')
    expect(wrapper.text()).toBe('Ajuste Requerido')
  })

  it('Pendiente usa la píldora ámbar', () => {
    const wrapper = mount(EstadoBadge, { props: { estado: 'Pendiente' } })

    expect(wrapper.classes()).toContain('bg-amber-50')
    expect(wrapper.classes()).toContain('border-amber-200')
  })
})

describe('KpiTarjeta', () => {
  it('muestra valor y etiqueta', () => {
    const wrapper = mount(KpiTarjeta, {
      props: { etiqueta: 'Evidencias', valor: 42, icono: IconoFalso },
    })

    expect(wrapper.text()).toContain('42')
    expect(wrapper.text()).toContain('Evidencias')
  })

  it('el tono por defecto es verde', () => {
    const wrapper = mount(KpiTarjeta, {
      props: { etiqueta: 'Aprobadas', valor: 10, icono: IconoFalso },
    })

    expect(wrapper.classes()).toContain('verde')
  })

  it('respeta el tono pasado por props', () => {
    const wrapper = mount(KpiTarjeta, {
      props: { etiqueta: 'Vencidas', valor: 3, icono: IconoFalso, tono: 'rojo' },
    })

    expect(wrapper.classes()).toContain('rojo')
    expect(wrapper.classes()).not.toContain('verde')
  })
})

describe('VacioEstado', () => {
  it('renderiza título y texto', () => {
    const wrapper = mount(VacioEstado, {
      props: { titulo: 'Sin evidencias', texto: 'Sube tu primera evidencia', icono: IconoFalso },
    })

    expect(wrapper.find('h3').text()).toBe('Sin evidencias')
    expect(wrapper.find('p').text()).toBe('Sube tu primera evidencia')
  })

  it('cargando=false no gira el icono', () => {
    const wrapper = mount(VacioEstado, {
      props: { titulo: 'T', texto: 'X', icono: IconoFalso },
    })

    expect(wrapper.find('.vacio-ico').classes()).not.toContain('girando')
  })

  it('cargando=true añade la clase girando', () => {
    const wrapper = mount(VacioEstado, {
      props: { titulo: 'T', texto: 'X', icono: IconoFalso, cargando: true },
    })

    expect(wrapper.find('.vacio-ico').classes()).toContain('girando')
  })

  // EXPLICACIÓN: si llega ilustracion, el SVG sustituye al círculo de icono
  it('con ilustracion renderiza <img> y oculta el icono', () => {
    const wrapper = mount(VacioEstado, {
      props: {
        titulo: 'T',
        texto: 'X',
        icono: IconoFalso,
        ilustracion: '/assets/vacio-documentos.svg',
      },
    })

    const img = wrapper.find('img.vacio-img')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toBe('/assets/vacio-documentos.svg')
    expect(wrapper.find('.vacio-ico').exists()).toBe(false)
  })

  it('sin ilustracion conserva el icono circular', () => {
    const wrapper = mount(VacioEstado, {
      props: { titulo: 'T', texto: 'X', icono: IconoFalso },
    })

    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('.vacio-ico').exists()).toBe(true)
  })
})

describe('Esqueleto', () => {
  // EXPLICACIÓN: skeleton de carga => N líneas shimmer sin depender de la red
  it('renderiza la cantidad de filas indicada', () => {
    const wrapper = mount(Esqueleto, { props: { filas: 6 } })

    expect(wrapper.findAll('.esqueleto-linea')).toHaveLength(6)
    expect(wrapper.attributes('aria-hidden')).toBe('true')
  })

  it('por defecto pinta 4 líneas', () => {
    const wrapper = mount(Esqueleto)

    expect(wrapper.findAll('.esqueleto-linea')).toHaveLength(4)
  })
})

describe('AvatarCirculo', () => {
  it('sin foto => iniciales en círculo neutro (slate)', () => {
    const wrapper = mount(AvatarCirculo, { props: { nombre: 'Ana Gómez' } })

    const iniciales = wrapper.find('.avatar-iniciales')
    expect(iniciales.text()).toBe('AG')
    expect(iniciales.classes()).toContain('bg-slate-200')
    expect(iniciales.classes()).toContain('text-slate-700')
    expect(iniciales.classes()).toContain('font-semibold')
    expect(iniciales.classes()).toContain('rounded-full')
    expect(wrapper.find('img').exists()).toBe(false)
  })

  it('con foto => <img> circular con object-cover y borde suave', () => {
    const wrapper = mount(AvatarCirculo, {
      props: { nombre: 'Ana Gómez', foto: '/fotos/ana.jpg' },
    })

    const img = wrapper.find('img.avatar-foto')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toBe('/fotos/ana.jpg')
    expect(img.classes()).toContain('w-9')
    expect(img.classes()).toContain('h-9')
    expect(img.classes()).toContain('object-cover')
    expect(img.classes()).toContain('border-slate-200')
    expect(wrapper.find('.avatar-iniciales').exists()).toBe(false)
  })

  it('pinta el punto verde de sesión activa por defecto', () => {
    const wrapper = mount(AvatarCirculo, { props: { nombre: 'Ana' } })

    const punto = wrapper.find('.avatar-estado')
    expect(punto.exists()).toBe(true)
    expect(punto.classes()).toContain('bg-emerald-500')
    // EXPLICACIÓN: inset >= 6px => el punto queda DENTRO del arco, no flotando afuera
    expect(punto.classes()).toContain('bottom-1.5')
    expect(punto.classes()).toContain('right-1.5')
  })

  it('enLinea=false oculta el punto', () => {
    const wrapper = mount(AvatarCirculo, { props: { nombre: 'Ana', enLinea: false } })

    expect(wrapper.find('.avatar-estado').exists()).toBe(false)
  })

  it('foto rota (error de carga) cae al respaldo de iniciales', async () => {
    const wrapper = mount(AvatarCirculo, {
      props: { nombre: 'Ana Gómez', foto: '/fotos/rota.jpg' },
    })

    await wrapper.find('img').trigger('error')

    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('.avatar-iniciales').text()).toBe('AG')
  })
})

describe('AvatarNombre', () => {
  it('muestra iniciales y nombre completo', () => {
    const wrapper = mount(AvatarNombre, { props: { nombre: 'Juan David Pérez' } })

    // EXPLICACIÓN: 2 primeras palabras => JD (nombre + primer apellido)
    expect(wrapper.find('.avatar-iniciales').text()).toBe('JD')
    expect(wrapper.text()).toContain('Juan David Pérez')
  })

  it('nombre vacío usa marcador ??', () => {
    const wrapper = mount(AvatarNombre, { props: { nombre: '   ' } })

    expect(wrapper.find('.avatar-iniciales').text()).toBe('??')
  })

  it('propaga foto y enLinea al círculo', () => {
    const wrapper = mount(AvatarNombre, {
      props: { nombre: 'Ana Gómez', foto: '/f.jpg', enLinea: false },
    })

    expect(wrapper.find('img.avatar-foto').exists()).toBe(true)
    expect(wrapper.find('.avatar-estado').exists()).toBe(false)
  })
})

describe('PaginacionBar', () => {
  it('muestra "Página X de Y"', () => {
    const wrapper = mount(PaginacionBar, {
      props: { pagina: 2, totalPaginas: 5, paginaActual: 2 },
    })

    expect(wrapper.text()).toContain('Página 2 de 5')
  })

  it('totalPaginas=0 se muestra como 1 (colección vacía)', () => {
    const wrapper = mount(PaginacionBar, {
      props: { pagina: 1, totalPaginas: 0, paginaActual: 1 },
    })

    expect(wrapper.text()).toContain('Página 1 de 1')
  })

  it('en la primera página Anterior queda deshabilitado', async () => {
    const wrapper = mount(PaginacionBar, {
      props: { pagina: 1, totalPaginas: 3, paginaActual: 1 },
    })

    const [anterior, siguiente] = wrapper.findAll('button')
    expect(anterior!.attributes('disabled')).toBeDefined()
    expect(siguiente!.attributes('disabled')).toBeUndefined()

    await siguiente!.trigger('click')
    expect(wrapper.emitted('cambiar')).toEqual([[1]])
  })

  it('en la última página Siguiente queda deshabilitado', async () => {
    const wrapper = mount(PaginacionBar, {
      props: { pagina: 3, totalPaginas: 3, paginaActual: 3 },
    })

    const [anterior, siguiente] = wrapper.findAll('button')
    expect(siguiente!.attributes('disabled')).toBeDefined()

    await anterior!.trigger('click')
    expect(wrapper.emitted('cambiar')).toEqual([[-1]])
  })
})
