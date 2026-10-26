import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type CleaningTask } from '../lib/api'
import { pendingCount, queuePhoto } from '../lib/photoQueue'

const REQUIRED = 3

export default function CleaningOps() {
  const qc = useQueryClient()
  const { data = [] } = useQuery({ queryKey: ['tasks'], queryFn: () => api<CleaningTask[]>('/cleaning/tasks'), refetchInterval: 15_000 })
  const refresh = () => qc.invalidateQueries({ queryKey: ['tasks'] })

  return (
    <div className="space-y-3">
      <h2 className="text-xl font-bold">Limpiezas de hoy</h2>
      {data.length === 0 && <p>No hay limpiezas hoy.</p>}
      {data.map((t) => <Task key={t.id} t={t} onChange={refresh} />)}
    </div>
  )
}

function Task({ t, onChange }: { t: CleaningTask; onChange: () => void }) {
  const pending = useQuery({ queryKey: ['pending', t.id, t.photo_urls.length], queryFn: () => pendingCount(t.id) })
  const complete = useMutation({
    mutationFn: () => api(`/cleaning/tasks/${t.id}/complete`, { method: 'POST' }),
    onSuccess: onChange,
  })
  const total = t.photo_urls.length + (pending.data ?? 0)

  async function onFiles(files: FileList | null) {
    for (const f of Array.from(files ?? [])) await queuePhoto(t.id, f)
    onChange()
    pending.refetch()
  }

  return (
    <div className="card space-y-3">
      <div className="flex justify-between">
        <p className="text-lg font-bold">Limpieza</p>
        <span className={`rounded-full px-3 py-1 text-sm text-white ${t.status === 'done' ? 'bg-sage' : 'bg-terracotta'}`}>
          {t.status === 'done' ? 'Hecha' : 'Pendiente'}
        </span>
      </div>
      <p>Fotos de control: {total}/{REQUIRED} {(pending.data ?? 0) > 0 && '(pendientes de subir)'}</p>
      {t.status !== 'done' && (
        <>
          <label className="btn-primary block w-full cursor-pointer py-4 text-center text-lg">
            📷 Añadir fotos
            <input type="file" accept="image/*" capture="environment" multiple hidden onChange={(e) => onFiles(e.target.files)} />
          </label>
          <button className="btn-accent w-full py-4 text-lg" disabled={t.photo_urls.length < REQUIRED || complete.isPending} onClick={() => complete.mutate()}>
            Marcar como hecha
          </button>
          {complete.error && <p className="text-terracotta">{(complete.error as Error).message}</p>}
        </>
      )}
    </div>
  )
}
