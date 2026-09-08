/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ayurveda: {
          50: '#f2f9f6',
          100: '#e1f2eb',
          200: '#c5e5d7',
          500: '#2c8a68',
          700: '#1a644b',
          800: '#14503c',
          900: '#0f382c', // Deep Emerald Primary
        },
        gold: {
          400: '#e6c86e',
          500: '#d4af37', // Herbal Gold Accent
          600: '#b89324',
        }
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
