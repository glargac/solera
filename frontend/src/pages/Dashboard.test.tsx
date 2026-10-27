import { screen } from '@testing-library/react'
import * as apiModule from '../lib/api'
import Dashboard from './Dashboard'
import { renderWithProviders } from '../test/utils'

const prop = (id: string, nightly_price = 100) => ({ id, nightly_price }) as apiModule.Property
const booking = (o: Partial<apiModule.Booking>) =>
  ({ id: Math.random().toString(), property_id: 'p1', source: 'manual', total_price: 0, ...o }) as apiModule.Booking

function mockApi(props: apiModule.Property[], bookings: apiModule.Booking[]) {
  vi.spyOn(apiModule, 'api').mockImplementation(async (path: string) =>
    (path === '/properties' ? props : bookings) as never)
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date(2026, 10, 15)) // noviembre 2026: 30 días
  })
  afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks() })

  it('calcula ocupación e ingresos con el precio por noche', async () => {
    mockApi([prop('p1', 100)], [booking({ check_in: '2026-11-01', check_out: '2026-11-11' })])
    renderWithProviders(<Dashboard />)
    expect(await screen.findByText('33%')).toBeInTheDocument() // 10/30
    expect(screen.getByText('1000 €')).toBeInTheDocument()
  })

  it('prefiere total_price y excluye los bloqueos personales', async () => {
    mockApi([prop('p1', 100)], [
      booking({ check_in: '2026-11-01', check_out: '2026-11-04', total_price: 500 }),
      booking({ check_in: '2026-11-10', check_out: '2026-11-20', source: 'personal' }),
    ])
    renderWithProviders(<Dashboard />)
    expect(await screen.findByText('500 €')).toBeInTheDocument()
    expect(screen.getByText('10%')).toBeInTheDocument() // 3/30
  })

  it('solo cuenta las noches que caen dentro del mes', async () => {
    mockApi([prop('p1')], [booking({ check_in: '2026-10-25', check_out: '2026-11-04' })])
    renderWithProviders(<Dashboard />)
    expect(await screen.findByText('10%')).toBeInTheDocument() // 3 noches de noviembre
  })

  it('sin propiedades muestra 0% y no divide entre cero', async () => {
    mockApi([], [])
    renderWithProviders(<Dashboard />)
    expect(await screen.findByText('0%')).toBeInTheDocument()
    expect(screen.getByText('0 €')).toBeInTheDocument()
  })
})
