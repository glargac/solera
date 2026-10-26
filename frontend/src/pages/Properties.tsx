import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, json, type Property } from '../lib/api'

export default function Properties() {
  const qc = useQueryClient()
  const { data = [] } = useQuery({ queryKey: ['properties'], queryFn: () => api<Property[]>('/properties') })
  const [form, setForm] = useState({ name: '', city: 'Málaga', nightly_price: 100, ical_url: '' })
  const refresh = () => qc.invalidateQueries({ queryKey: ['properties'] })

  const create = useMutation({
    mutationFn: () => api('/properties', json('POST', { ...form, ical_url: form.ical_url || null })),
    onSuccess: () => { setForm({ ...form, name: '', ical_url: '' }); refresh() },
  })
  const sync = useMutation({
    mutationFn: (id: string) => api(`/properties/${id}/sync`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['bookings'] }),
  })
  const save = useMutation({
    mutationFn: (p: Property) => api(`/properties/${p.id}`, json('PUT', p)),
    onSuccess: refresh,
  })

  return (
    <div className="space-y-3">
      <div className="card space-y-2">
        <h2 className="font-bold">Nueva propiedad</h2>
        <input className="input" placeholder="Nombre" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <input className="input" placeholder="Ciudad" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
        <input className="input" type="number" placeholder="Precio/noche" value={form.nightly_price} onChange={(e) => setForm({ ...form, nightly_price: +e.target.value })} />
        <input className="input" placeholder="URL iCal (Airbnb/Booking)" value={form.ical_url} onChange={(e) => setForm({ ...form, ical_url: e.target.value })} />
        <button className="btn-primary" disabled={!form.name} onClick={() => create.mutate()}>Añadir</button>
      </div>
      {data.map((p) => (
        <div key={p.id} className="card space-y-2">
          <div className="flex items-center justify-between">
            <div><p className="font-bold">{p.name}</p><p className="text-sm">{p.city} · {p.nightly_price} €/noche</p></div>
            {p.ical_url && <button className="btn-accent" onClick={() => sync.mutate(p.id)}>{sync.isPending ? '…' : 'Sincronizar'}</button>}
          </div>
          <details>
            <summary className="cursor-pointer text-sm underline">Guía del huésped</summary>
            <GuideForm p={p} onSave={(np) => save.mutate(np)} />
          </details>
        </div>
      ))}
    </div>
  )
}

function GuideForm({ p, onSave }: { p: Property; onSave: (p: Property) => void }) {
  const [v, setV] = useState(p)
  return (
    <div className="mt-2 space-y-2">
      <input className="input" placeholder="WiFi (nombre)" value={v.wifi_name} onChange={(e) => setV({ ...v, wifi_name: e.target.value })} />
      <input className="input" placeholder="WiFi (contraseña)" value={v.wifi_password} onChange={(e) => setV({ ...v, wifi_password: e.target.value })} />
      <textarea className="input" placeholder="Instrucciones de check-in" value={v.checkin_instructions} onChange={(e) => setV({ ...v, checkin_instructions: e.target.value })} />
      <textarea className="input" placeholder="Normas de la casa" value={v.house_rules} onChange={(e) => setV({ ...v, house_rules: e.target.value })} />
      <button className="btn-primary" onClick={() => onSave(v)}>Guardar</button>
    </div>
  )
}
