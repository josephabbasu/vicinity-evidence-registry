/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#0F172A',
        paper: '#F8F7F2',
        verified: '#0E9F6E',
        signal: '#F59E0B',
        claret: '#B91C1C',
      },
    },
  },
  plugins: [],
}
