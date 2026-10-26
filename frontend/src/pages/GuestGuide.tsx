import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { api, type Guide } from '../lib/api'

export default function GuestGuide() {
  const { token } = useParams()
  const { data, isLoading, error } = useQuery({ queryKey: ['guide', token], queryFn: () => api<Guide>(`/guests/guide/${token}`) })

  if (isLoading) return <p className="p-4">Cargando…</p>
  if (error || !data) return <p className="p-4">Guía no encontrada.</p>

  const sections: [string, string | false][] = [
    ['Check-in', data.checkin_instructions],
    ['WiFi', data.wifi_name && `${data.wifi_name} · ${data.wifi_password}`],
    ['Normas de la casa', data.house_rules],
  ]

  return (
    <div className="mx-auto max-w-md space-y-3 p-4">
      <div className="rounded-2xl bg-navy p-5 text-white">
        <p className="text-sm opacity-80">Bienvenido{data.guest_name && `, ${data.guest_name}`}</p>
        <h1 className="text-2xl font-bold">{data.property_name}</h1>
        <p className="text-sm">{data.address || data.city} · {data.check_in} → {data.check_out}</p>
      </div>
      {sections.map(([title, body]) => body && (
        <div key={title} className="card"><h2 className="font-bold">{title}</h2><p className="whitespace-pre-line">{body}</p></div>
      ))}
    </div>
  )
}
