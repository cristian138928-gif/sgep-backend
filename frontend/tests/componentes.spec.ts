// frontend/tests/componentes.spec.ts
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import EstadoBadge from '../src/components/EstadoBadge.vue'
import AuthPanel from '../src/components/AuthPanel.vue'
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
  it('Aprobada usa la clase verde', () => {
    const wrapper = mount(EstadoBadge, { props: { estado: 'Aprobada' } })

    expect(wrapper.classes()).toContain('badge-aprobada')
    expect(wrapper.text()).toBe('Aprobada')
  })

  it('Ajuste Requerido usa la clase roja', () => {
    const wrapper = mount(EstadoBadge, { props: { estado: 'Ajuste Requerido' } })

    expect(wrapper.classes()).toContain('badge-ajuste')
    expect(wrapper.text()).toBe('Ajuste Requerido')
  })

  it('Pendiente usa la clase ámbar', () => {
    const wrapper = mount(EstadoBadge, { props: { estado: 'Pendiente' } })

    expect(wrapper.classes()).toContain('badge-pendiente')
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

describe('AvatarNombre', () => {
  it('muestra iniciales y nombre completo', () => {
    const wrapper = mount(AvatarNombre, { props: { nombre: 'Juan David Pérez' } })

    // EXPLICACIÓN: 2 primeras palabras => JD (nombre + primer apellido)
    expect(wrapper.find('.avatar').text()).toBe('JD')
    expect(wrapper.text()).toContain('Juan David Pérez')
  })

  it('nombre vacío usa marcador ??', () => {
    const wrapper = mount(AvatarNombre, { props: { nombre: '   ' } })

    expect(wrapper.find('.avatar').text()).toBe('??')
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
