import { clear } from 'idb-keyval'
import * as apiModule from './api'
import { flushQueue, pendingCount, queuePhoto } from './photoQueue'

const file = (name = 'a.jpg') => new File(['x'], name, { type: 'image/jpeg' })
const setOnline = (v: boolean) => vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(v)

describe('photoQueue', () => {
  beforeEach(async () => { await clear() })
  afterEach(() => vi.restoreAllMocks())

  it('sube la foto inmediatamente si hay conexión', async () => {
    setOnline(true)
    const spy = vi.spyOn(apiModule, 'api').mockResolvedValue({} as never)
    await queuePhoto('t1', file())
    expect(spy).toHaveBeenCalledTimes(1)
    expect(spy.mock.calls[0][0]).toBe('/cleaning/tasks/t1/photos')
    expect(await pendingCount('t1')).toBe(0)
  })

  it('guarda sin conexión y sube al volver', async () => {
    setOnline(false)
    const spy = vi.spyOn(apiModule, 'api').mockResolvedValue({} as never)
    await queuePhoto('t1', file())
    expect(spy).not.toHaveBeenCalled()
    expect(await pendingCount('t1')).toBe(1)
    setOnline(true)
    await flushQueue()
    expect(spy).toHaveBeenCalledTimes(1)
    expect(await pendingCount('t1')).toBe(0)
  })

  it('conserva las fotos si la subida falla', async () => {
    setOnline(true)
    vi.spyOn(apiModule, 'api').mockRejectedValue(new Error('red caída'))
    await queuePhoto('t1', file())
    expect(await pendingCount('t1')).toBe(1)
  })

  it('no pierde fotos añadidas seguidas sin conexión', async () => {
    setOnline(false)
    await Promise.all([queuePhoto('t1', file('1.jpg')), queuePhoto('t1', file('2.jpg')), queuePhoto('t1', file('3.jpg'))])
    expect(await pendingCount('t1')).toBe(3)
  })

  it('cuenta las pendientes por tarea', async () => {
    setOnline(false)
    await queuePhoto('t1', file())
    await queuePhoto('t2', file())
    expect(await pendingCount('t1')).toBe(1)
  })
})
