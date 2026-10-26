import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, json, type Booking, type Property } from '../lib/api'

export default function Bookings() {
  const qc = useQueryClient()
  const props = useQuery({ queryKey: ['properties'], queryFn: () => api<Property[]>('/properties') })
  const { data = [] } = useQuery({ queryKey: ['bookings'], queryFn: () => api<Booking[]>('/bookings') })
  const [f, setF] = useState({ property_id: '', guest_name: '', check_in: '', check_out: '', source: 'manual' })

  const create = useMutation({
    mutationFn: () => api('/bookings', json('POST', { ...f, property_id: f.property_id || props.data?.[0]?.id })),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['bookings'] }),
  })
  const name = (id: string) => props.data?.find((p) => p.id === id)?.name ?? ''
  const guideUrl = (t: string) => `${location.origin}/guide/${t}`

  return (
    <div className="space-y-3">
      <div className="card space-y-2">
        <h2 className="font-bold">Nueva reserva / bloqueo</h2>
        <select className="input" value={f.property_id} onChange={(e) => setF({ ...f, property_id: e.target.value })}>
          {props.data?.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
        <input className="input" placeholder="Huésped" value={f.guest_name} onChange={(e) => setF({ ...f, guest_name: e.target.value })} />
        <div className="flex gap-2">
          <input className="input" type="date" value={f.check_in} onChange={(e) => setF({ ...f, check_in: e.target.value })} />
          <input className="input" type="date" value={f.check_out} onChange={(e) => setF({ ...f, check_out: e.target.value })} />
        </div>
        <select className="input" value={f.source} onChange={(e) => setF({ ...f, source: e.target.value })}>
          <option value="manual">Reserva manual</option>
          <option value="personal">Uso personal (bloqueo)</option>
        </select>
        <button className="btn-primary" disabled={!f.check_in || !f.check_out} onClick={() => create.mutate()}>Añadir</button>
        {create.error && <p className="text-terracotta">{(create.error as Error).message}</p>}
      </div>
      {data.map((b) => (
        <div key={b.id} className="card flex items-center justify-between">
          <div>
            <p className="font-bold">{b.guest_name || 'Sin nombre'} · {name(b.property_id)}</p>
            <p className="text-sm">{b.check_in} → {b.check_out} · {b.source}</p>
          </div>
          {b.source !== 'personal' && (
            <button className="text-sm underline" onClick={() => navigator.clipboard.writeText(guideUrl(b.guide_token))}>Copiar guía</button>
          )}
        </div>
      ))}
    </div>
  )
}
