/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        cream: {
          50: '#fcfbfa',
          100: '#f8f6f0',
          200: '#f3efe6',
          300: '#eae4d6',
          400: '#d7cebe',
        },
        ink: {
          950: '#090c13',
          900: '#0e121d',
          850: '#131825',
          800: '#181f30',
          700: '#232c44',
          600: '#344161',
        },
        cubist: {
          blue: '#1d63d8',
          ochre: '#e59a18',
          yellow: '#f4b82d',
          crimson: '#e12b38',
          coral: '#f05d43',
          green: '#10b981',
          teal: '#0d9488',
        }
      }
    },
  },
  plugins: [],
}

