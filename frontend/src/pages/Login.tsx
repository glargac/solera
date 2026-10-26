import { useState } from 'react'
import { supabase } from '../lib/supabase'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function submit(mode: 'in' | 'up') {
    if (!email.trim() || !password) {
      setError('Escribe tu email y contraseña')
      return
    }
    const { error } = mode === 'in'
      ? await supabase.auth.signInWithPassword({ email, password })
      : await supabase.auth.signUp({ email, password })
    setError(error?.message ?? '')
  }

  return (
    <div className="mx-auto mt-24 max-w-sm space-y-3 p-4">
      <h1 className="text-3xl font-bold">SOLORA</h1>
      <input className="input" type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input className="input" type="password" placeholder="Contraseña" value={password} onChange={(e) => setPassword(e.target.value)} />
      {error && <p className="text-terracotta">{error}</p>}
      <button className="btn-primary w-full" onClick={() => submit('in')}>Entrar</button>
      <button className="w-full text-sm underline" onClick={() => submit('up')}>Crear cuenta</button>
    </div>
  )
}
