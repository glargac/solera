import { del, get, keys, set } from 'idb-keyval'
import { api, type CleaningTask } from './api'

// Cola offline: las fotos se guardan en IndexedDB hasta que hay conexión.
const key = (taskId: string, n: number) => `photo:${taskId}:${n}:${Date.now()}`

export async function queuePhoto(taskId: string, file: File) {
  await set(key(taskId, 0), { taskId, file })
  await flushQueue()
}

export async function flushQueue() {
  if (!navigator.onLine) return
  for (const k of await keys()) {
    if (typeof k !== 'string' || !k.startsWith('photo:')) continue
    const item = await get<{ taskId: string; file: File }>(k)
    if (!item) continue
    const body = new FormData()
    body.append('files', item.file)
    try {
      await api<CleaningTask>(`/cleaning/tasks/${item.taskId}/photos`, { method: 'POST', body })
      await del(k)
    } catch {
      return // se reintenta al volver la conexión
    }
  }
}

export async function pendingCount(taskId: string) {
  return (await keys()).filter((k) => typeof k === 'string' && k.startsWith(`photo:${taskId}:`)).length
}

window.addEventListener('online', () => void flushQueue())
