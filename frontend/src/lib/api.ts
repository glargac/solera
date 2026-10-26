import { supabase } from './supabase'

const API = import.meta.env.VITE_API_URL as string

export interface Property {
  id: string; name: string; city: string; address: string
  nightly_price: number; cleaning_fee: number; ical_url: string | null
  wifi_name: string; wifi_password: string
  checkin_instructions: string; house_rules: string
}
export interface Booking {
  id: string; property_id: string; source: string; guest_name: string
  check_in: string; check_out: string; total_price: number; guide_token: string
}
export interface CleaningTask {
  id: string; property_id: string; date: string
  status: 'pending' | 'in_progress' | 'done'; photo_urls: string[]
}
export interface Guide {
  property_name: string; city: string; address: string; guest_name: string
  check_in: string; check_out: string; wifi_name: string; wifi_password: string
  checkin_instructions: string; house_rules: string
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { data } = await supabase.auth.getSession()
  const headers = new Headers(init.headers)
  if (data.session) headers.set('Authorization', `Bearer ${data.session.access_token}`)
  if (typeof init.body === 'string') headers.set('Content-Type', 'application/json')
  const res = await fetch(`${API}${path}`, { ...init, headers })
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? res.statusText)
  return res.status === 204 ? (undefined as T) : res.json()
}

export const json = (method: string, body: unknown): RequestInit => ({
  method, body: JSON.stringify(body),
})
