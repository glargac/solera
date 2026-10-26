import { useEffect, useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import type { Session } from '@supabase/supabase-js'
import { supabase } from './lib/supabase'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Properties from './pages/Properties'
import Bookings from './pages/Bookings'
import CleaningOps from './pages/CleaningOps'
import GuestGuide from './pages/GuestGuide'

const queryClient = new QueryClient()

export default function App() {
  const [session, setSession] = useState<Session | null | undefined>(undefined)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session))
    const { data } = supabase.auth.onAuthStateChange((_e, s) => setSession(s))
    return () => data.subscription.unsubscribe()
  }, [])

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/guide/:token" element={<GuestGuide />} />
          {session === undefined ? (
            <Route path="*" element={<p className="p-4">Cargando…</p>} />
          ) : session === null ? (
            <Route path="*" element={<Login />} />
          ) : (
            <Route element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="properties" element={<Properties />} />
              <Route path="bookings" element={<Bookings />} />
              <Route path="cleaning" element={<CleaningOps />} />
              <Route path="*" element={<Navigate to="/" />} />
            </Route>
          )}
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
