import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import * as apiModule from '../lib/api'
import Bookings from './Bookings'
import { renderWithProviders } from '../test/utils'

const props = [{ id: 'p1', name: 'Casa Mar' }, { id: 'p2', name: 'Ático' }] as apiModule.Property[]
const booking = (o: Partial<apiModule.Booking>) =>
  ({ id: 'b1', property_id: 'p1', source: 'manual', guest_name: 'Ana', check_in: '2026-11-01',
     check_out: '2026-11-05', total_price: 0, guide_token: 'tok123', ...o }) as apiModule.Booking

function mockApi(bookings: apiModule.Booking[]) {
  return vi.spyOn(apiModule, 'api').mockImplementation(async (path: string) =>
    (path === '/properties' ? props : path === '/bookings' ? bookings : {}) as never)
}

describe('Bookings', () => {
  afterEach(() => vi.restoreAllMocks())

  it('lista reservas con el nombre de su propiedad', async () => {
    mockApi([booking({})])
    renderWithProviders(<Bookings />)
    expect(await screen.findByText('Ana · Casa Mar')).toBeInTheDocument()
  })

  it('los bloqueos personales no ofrecen guía', async () => {
    mockApi([booking({ source: 'personal' })])
    renderWithProviders(<Bookings />)
    await screen.findByText('Ana · Casa Mar')
    expect(screen.queryByText('Copiar guía')).not.toBeInTheDocument()
  })

  it('copia el enlace de la guía', async () => {
    mockApi([booking({})])
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })
    renderWithProviders(<Bookings />)
    await userEvent.click(await screen.findByText('Copiar guía'))
    expect(writeText).toHaveBeenCalledWith(`${location.origin}/guide/tok123`)
  })

  it('crea una reserva usando la primera propiedad por defecto', async () => {
    const spy = mockApi([])
    renderWithProviders(<Bookings />)
    const add = await screen.findByRole('button', { name: 'Añadir' })
    expect(add).toBeDisabled()
    const [inDate, outDate] = Array.from(document.querySelectorAll('input[type=date]')) as HTMLInputElement[]
    await userEvent.type(inDate, '2026-11-01')
    await userEvent.type(outDate, '2026-11-05')
    await userEvent.click(add)
    await waitFor(() => expect(spy).toHaveBeenCalledWith('/bookings', expect.objectContaining({ method: 'POST' })))
    const body = JSON.parse(spy.mock.calls.find((c) => c[1]?.method === 'POST')![1]!.body as string)
    expect(body).toMatchObject({ property_id: 'p1', check_in: '2026-11-01', check_out: '2026-11-05', source: 'manual' })
  })

  it('muestra el error del backend', async () => {
    vi.spyOn(apiModule, 'api').mockImplementation(async (path: string, init?: RequestInit) => {
      if (init?.method === 'POST') throw new Error('check_out debe ser posterior a check_in')
      return (path === '/properties' ? props : []) as never
    })
    renderWithProviders(<Bookings />)
    const [inDate, outDate] = Array.from((await screen.findByRole('button', { name: 'Añadir' }), document.querySelectorAll('input[type=date]'))) as HTMLInputElement[]
    await userEvent.type(inDate, '2026-11-05')
    await userEvent.type(outDate, '2026-11-01')
    await userEvent.click(screen.getByRole('button', { name: 'Añadir' }))
    expect(await screen.findByText('check_out debe ser posterior a check_in')).toBeInTheDocument()
  })
})
