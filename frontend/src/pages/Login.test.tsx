import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { supabase } from '../lib/supabase'
import Login from './Login'
import { renderWithProviders } from '../test/utils'

describe('Login', () => {
  it('no llama a Supabase con campos vacíos', async () => {
    renderWithProviders(<Login />)
    await userEvent.click(screen.getByText('Crear cuenta'))
    expect(screen.getByText('Escribe tu email y contraseña')).toBeInTheDocument()
    expect(supabase.auth.signUp).not.toHaveBeenCalled()
    await userEvent.click(screen.getByText('Entrar'))
    expect(supabase.auth.signInWithPassword).not.toHaveBeenCalled()
  })

  it('inicia sesión con email y contraseña', async () => {
    renderWithProviders(<Login />)
    await userEvent.type(screen.getByPlaceholderText('Email'), 'a@b.com')
    await userEvent.type(screen.getByPlaceholderText('Contraseña'), 'secreto1')
    await userEvent.click(screen.getByText('Entrar'))
    expect(supabase.auth.signInWithPassword).toHaveBeenCalledWith({ email: 'a@b.com', password: 'secreto1' })
  })

  it('muestra el error que devuelve Supabase', async () => {
    vi.mocked(supabase.auth.signInWithPassword).mockResolvedValueOnce({ error: { message: 'Email not confirmed' } } as never)
    renderWithProviders(<Login />)
    await userEvent.type(screen.getByPlaceholderText('Email'), 'a@b.com')
    await userEvent.type(screen.getByPlaceholderText('Contraseña'), 'x')
    await userEvent.click(screen.getByText('Entrar'))
    expect(await screen.findByText('Email not confirmed')).toBeInTheDocument()
  })

  it('crea cuenta con signUp', async () => {
    renderWithProviders(<Login />)
    await userEvent.type(screen.getByPlaceholderText('Email'), 'a@b.com')
    await userEvent.type(screen.getByPlaceholderText('Contraseña'), 'secreto1')
    await userEvent.click(screen.getByText('Crear cuenta'))
    expect(supabase.auth.signUp).toHaveBeenCalledWith({ email: 'a@b.com', password: 'secreto1' })
  })
})
