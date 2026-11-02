// frontend/tests/componentes.spec.ts
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import EstadoBadge from '../src/components/EstadoBadge.vue'
import KpiTarjeta from '../src/components/KpiTarjeta.vue'
import PaginacionBar from '../src/components/PaginacionBar.vue'
import VacioEstado from '../src/components/VacioEstado.vue'
import type { Component } from 'vue'

/** EXPLICACIÓN: icono falso liviano (lucide no aporta nada a la lógica testeada). */
const IconoFalso: Component = { name: 'IconoFalso', template: '<svg class="ico-falso" />' }

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
