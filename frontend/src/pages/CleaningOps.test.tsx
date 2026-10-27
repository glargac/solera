import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { clear } from 'idb-keyval'
import * as apiModule from '../lib/api'
import CleaningOps from './CleaningOps'
import { renderWithProviders } from '../test/utils'

const task = (o: Partial<apiModule.CleaningTask> = {}): apiModule.CleaningTask =>
  ({ id: 't1', property_id: 'p1', date: '2026-11-05', status: 'pending', photo_urls: [], ...o })

function mockApi(tasks: apiModule.CleaningTask[]) {
  return vi.spyOn(apiModule, 'api').mockImplementation(async (path: string) =>
    (path === '/cleaning/tasks' ? tasks : {}) as never)
}

describe('CleaningOps', () => {
  beforeEach(async () => { await clear() })
  afterEach(() => vi.restoreAllMocks())

  it('avisa cuando no hay limpiezas', async () => {
    mockApi([])
    renderWithProviders(<CleaningOps />)
    expect(await screen.findByText('No hay limpiezas hoy.')).toBeInTheDocument()
  })

  it('deshabilita "Marcar como hecha" con menos de 3 fotos', async () => {
    mockApi([task({ photo_urls: ['a', 'b'] })])
    renderWithProviders(<CleaningOps />)
    expect(await screen.findByText(/Fotos de control: 2\/3/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Marcar como hecha' })).toBeDisabled()
  })

  it('con 3 fotos permite completar la limpieza', async () => {
    const spy = mockApi([task({ photo_urls: ['a', 'b', 'c'] })])
    renderWithProviders(<CleaningOps />)
    const btn = await screen.findByRole('button', { name: 'Marcar como hecha' })
    expect(btn).toBeEnabled()
    await userEvent.click(btn)
    await waitFor(() => expect(spy).toHaveBeenCalledWith('/cleaning/tasks/t1/complete', { method: 'POST' }))
  })

  it('una limpieza hecha no muestra acciones', async () => {
    mockApi([task({ status: 'done', photo_urls: ['a', 'b', 'c'] })])
    renderWithProviders(<CleaningOps />)
    expect(await screen.findByText('Hecha')).toBeInTheDocument()
    expect(screen.queryByText(/Añadir fotos/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Marcar como hecha' })).not.toBeInTheDocument()
  })

  it('muestra el error del backend al completar', async () => {
    vi.spyOn(apiModule, 'api').mockImplementation(async (path: string) => {
      if (path === '/cleaning/tasks') return [task({ photo_urls: ['a', 'b', 'c'] })] as never
      throw new Error('Se necesitan 3 fotos de control')
    })
    renderWithProviders(<CleaningOps />)
    await userEvent.click(await screen.findByRole('button', { name: 'Marcar como hecha' }))
    expect(await screen.findByText('Se necesitan 3 fotos de control')).toBeInTheDocument()
  })
})
