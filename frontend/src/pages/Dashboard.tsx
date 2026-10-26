import { useQuery } from '@tanstack/react-query'
import { api, type Booking, type Property } from '../lib/api'

const nights = (b: Booking) => (+new Date(b.check_out) - +new Date(b.check_in)) / 86_400_000

export default function Dashboard() {
  const props = useQuery({ queryKey: ['properties'], queryFn: () => api<Property[]>('/properties') })
  const bookings = useQuery({ queryKey: ['bookings'], queryFn: () => api<Booking[]>('/bookings') })

  const now = new Date()
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1)
  const monthEnd = new Date(now.getFullYear(), now.getMonth() + 1, 1)
  const daysInMonth = (+monthEnd - +monthStart) / 86_400_000

  const monthBookings = (bookings.data ?? []).filter(
    (b) => b.source !== 'personal' && new Date(b.check_in) < monthEnd && new Date(b.check_out) > monthStart,
  )
  const occupiedNights = monthBookings.reduce((sum, b) => {
    const s = Math.max(+new Date(b.check_in), +monthStart)
    const e = Math.min(+new Date(b.check_out), +monthEnd)
    return sum + (e - s) / 86_400_000
  }, 0)
  const propCount = props.data?.length ?? 0
  const occupancy = propCount ? Math.round((occupiedNights / (daysInMonth * propCount)) * 100) : 0
  // Aproximación: precio/noche de la propiedad × noches, salvo que la reserva traiga total.
  const revenue = monthBookings.reduce((sum, b) => {
    const p = props.data?.find((x) => x.id === b.property_id)
    return sum + (b.total_price || nights(b) * (p?.nightly_price ?? 0))
  }, 0)

  return (
    <div className="grid gap-3 sm:grid-cols-3">
      <div className="card"><p className="text-sm">Ocupación del mes</p><p className="text-3xl font-bold text-sage">{occupancy}%</p></div>
      <div className="card"><p className="text-sm">Ingresos estimados</p><p className="text-3xl font-bold">{revenue.toFixed(0)} €</p></div>
      <div className="card"><p className="text-sm">Propiedades</p><p className="text-3xl font-bold">{propCount}</p></div>
    </div>
  )
}
