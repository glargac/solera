import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import * as apiModule from '../lib/api'
import Properties from './Properties'
import { renderWithProviders } from '../test/utils'

const prop = (o: Partial<apiModule.Property> = {}) =>
  ({ id: 'p1', name: 'Casa Mar', city: 'Málaga', nightly_price: 120, ical_url: null, wifi_name: '',
     wifi_password: '', checkin_instructions: '', house_rules: '', ...o }) as apiModule.Property

function mockApi(props: apiModule.Property[]) {
  return vi.spyOn(apiModule, 'api').mockImplementation(async (path: string) =>
    (path === '/properties' ? props : {}) as never)
}

describe('Properties', () => {
  afterEach(() => vi.restoreAllMocks())

  it('lista las propiedades y solo ofrece sincronizar si hay iCal', async () => {
    mockApi([prop(), prop({ id: 'p2', name: 'Con iCal', ical_url: 'http://x' })])
    renderWithProviders(<Properties />)
    expect(await screen.findByText('Casa Mar')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Sincronizar' })).toHaveLength(1)
  })

  it('"Añadir" está deshabilitado sin nombre', async () => {
    mockApi([])
    renderWithProviders(<Properties />)
    expect(await screen.findByRole('button', { name: 'Añadir' })).toBeDisabled()
  })

  it('crea una propiedad y envía ical_url null si está vacío', async () => {
    const spy = mockApi([])
    renderWithProviders(<Properties />)
    await userEvent.type(await screen.findByPlaceholderText('Nombre'), 'Ático')
    await userEvent.click(screen.getByRole('button', { name: 'Añadir' }))
    await waitFor(() => expect(spy).toHaveBeenCalledWith('/properties', expect.objectContaining({ method: 'POST' })))
    const body = JSON.parse((spy.mock.calls.find((c) => c[1]?.method === 'POST')![1]!.body) as string)
    expect(body).toMatchObject({ name: 'Ático', city: 'Málaga', ical_url: null })
  })

  it('sincroniza llamando a /sync', async () => {
    const spy = mockApi([prop({ ical_url: 'http://x' })])
    renderWithProviders(<Properties />)
    await userEvent.click(await screen.findByRole('button', { name: 'Sincronizar' }))
    await waitFor(() => expect(spy).toHaveBeenCalledWith('/properties/p1/sync', { method: 'POST' }))
  })
})
