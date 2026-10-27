import { api, json } from './api'

const fetchMock = vi.fn()
vi.stubGlobal('fetch', fetchMock)

const response = (status: number, body?: unknown) =>
  ({ ok: status < 400, status, statusText: 'Err', json: async () => body }) as Response

describe('api()', () => {
  it('añade el token de la sesión y devuelve el JSON', async () => {
    fetchMock.mockResolvedValue(response(200, { ok: 1 }))
    expect(await api('/x')).toEqual({ ok: 1 })
    const headers = fetchMock.mock.calls[0][1].headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer tok')
  })

  it('pone Content-Type JSON solo cuando el body es un string', async () => {
    fetchMock.mockResolvedValue(response(200, {}))
    await api('/x', json('POST', { a: 1 }))
    expect((fetchMock.mock.calls[0][1].headers as Headers).get('Content-Type')).toBe('application/json')
    await api('/x', { method: 'POST', body: new FormData() })
    expect((fetchMock.mock.calls[1][1].headers as Headers).has('Content-Type')).toBe(false)
  })

  it('lanza el detail del backend cuando hay error', async () => {
    fetchMock.mockResolvedValue(response(422, { detail: 'Fechas inválidas' }))
    await expect(api('/x')).rejects.toThrow('Fechas inválidas')
  })

  it('usa statusText si el error no trae JSON', async () => {
    fetchMock.mockResolvedValue({ ok: false, status: 500, statusText: 'Boom', json: async () => { throw new Error() } })
    await expect(api('/x')).rejects.toThrow('Boom')
  })

  it('devuelve undefined en 204', async () => {
    fetchMock.mockResolvedValue(response(204))
    expect(await api('/x', { method: 'DELETE' })).toBeUndefined()
  })
})
