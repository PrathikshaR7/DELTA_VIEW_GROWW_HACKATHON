/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        teal: {
          950: '#0b1329', // Neutral dark slate base
          900: '#111c38',
          800: '#1b2a4a', // Dark slate border/card
          700: '#273b61',
          600: '#0284c7', // Cool sky/cyan accent (doesn't clash with green)
          400: '#38bdf8', // Bright blue-cyan highlight
          200: '#bae6fd', // Soft text accent
          50: '#f0f9ff',
        },
        // Dedicated gain/loss colors that pop on dark slate
        gain: {
          500: '#22c55e', // Vibrant Green
          400: '#4ade80',
        },
        loss: {
          500: '#ef4444', // Crisp Red
          400: '#f87171',
        },
        surface: {
          950: '#090d16', // Main App Background
          900: '#0f172a', // Table & Card Containers
          800: '#1e293b', // Row Hover / Dividers
          700: '#334155', // Borders & Active states
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}