import { NavLink, Outlet } from 'react-router-dom'
import { supabase } from '../lib/supabase'

const links = [
  ['/', 'Panel'],
  ['/properties', 'Propiedades'],
  ['/bookings', 'Reservas'],
  ['/cleaning', 'Limpieza'],
]

export default function Layout() {
  return (
    <div className="mx-auto max-w-4xl p-4">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">SOLORA</h1>
        <button className="text-sm underline" onClick={() => supabase.auth.signOut()}>Salir</button>
      </header>
      <nav className="mb-4 flex gap-2 overflow-x-auto">
        {links.map(([to, label]) => (
          <NavLink key={to} to={to} end={to === '/'}
            className={({ isActive }) => `btn whitespace-nowrap ${isActive ? 'bg-navy text-white' : 'bg-sand-dark'}`}>
            {label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  )
}
