/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: { DEFAULT: '#0B3C5D', light: '#1D5F8A' },
        sand: { DEFAULT: '#F5EFE6', dark: '#E6DAC6' },
        sage: { DEFAULT: '#5B8C5A', dark: '#3F6B3E' },
        terracotta: '#D1603D',
      },
    },
  },
  plugins: [],
}
