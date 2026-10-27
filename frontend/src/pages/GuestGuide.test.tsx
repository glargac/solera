import { screen } from '@testing-library/react'
import * as apiModule from '../lib/api'
import GuestGuide from './GuestGuide'
import { renderWithProviders } from '../test/utils'

const guide = (o: Partial<apiModule.Guide> = {}): apiModule.Guide => ({
  property_name: 'Casa Mar', city: 'Málaga', address: 'Calle Sol 1', guest_name: 'Ana',
  check_in: '2026-11-01', check_out: '2026-11-05', wifi_name: '', wifi_password: '',
  checkin_instructions: '', house_rules: '', ...o,
})
const render = () => renderWithProviders(<GuestGuide />, { route: '/guide/tok', path: '/guide/:token' })

describe('GuestGuide', () => {
  afterEach(() => vi.restoreAllMocks())

  it('muestra cabecera y solo las secciones con contenido', async () => {
    const spy = vi.spyOn(apiModule, 'api').mockResolvedValue(guide({ wifi_name: 'Net', wifi_password: 'pw', house_rules: 'Silencio' }))
    render()
    expect(await screen.findByText('Casa Mar')).toBeInTheDocument()
    expect(spy).toHaveBeenCalledWith('/guests/guide/tok')
    expect(screen.getByText('Net · pw')).toBeInTheDocument()
    expect(screen.getByText('Normas de la casa')).toBeInTheDocument()
    expect(screen.queryByText('Check-in')).not.toBeInTheDocument()
  })

  it('saluda por el nombre del huésped', async () => {
    vi.spyOn(apiModule, 'api').mockResolvedValue(guide())
    render()
    expect(await screen.findByText('Bienvenido, Ana')).toBeInTheDocument()
  })

  it('muestra un mensaje si la guía no existe', async () => {
    vi.spyOn(apiModule, 'api').mockRejectedValue(new Error('Guía no encontrada'))
    render()
    expect(await screen.findByText('Guía no encontrada.')).toBeInTheDocument()
  })
})
