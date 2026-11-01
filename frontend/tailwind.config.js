/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Themeable surfaces: values live in src/index.css (:root and .dark).
        paper: 'rgb(var(--paper) / <alpha-value>)',
        surface: 'rgb(var(--surface) / <alpha-value>)',
        ink: {
          DEFAULT: 'rgb(var(--ink) / <alpha-value>)',
          soft: 'rgb(var(--ink-soft) / <alpha-value>)',
          muted: 'rgb(var(--ink-muted) / <alpha-value>)',
        },
        pine: {
          50: 'rgb(var(--pine-50) / <alpha-value>)',
          100: 'rgb(var(--pine-100) / <alpha-value>)',
          200: 'rgb(var(--pine-200) / <alpha-value>)',
          300: 'rgb(var(--pine-300) / <alpha-value>)',
          400: 'rgb(var(--pine-400) / <alpha-value>)',
          500: 'rgb(var(--pine-500) / <alpha-value>)',
          600: 'rgb(var(--pine-600) / <alpha-value>)',
          700: 'rgb(var(--pine-700) / <alpha-value>)',
          800: 'rgb(var(--pine-800) / <alpha-value>)',
          900: 'rgb(var(--pine-900) / <alpha-value>)',
          950: 'rgb(var(--pine-950) / <alpha-value>)',
        },
        line: 'rgb(var(--line) / <alpha-value>)',
        // Warm neutral scale stays fixed: it is used on permanently dark panels.
        slate: {
          50: '#F7F3EA',
          100: '#F0EBDF',
          200: '#E2DACB',
          300: '#D0C7B6',
          400: '#AFA694',
          500: '#8B8372',
          600: '#6A6559',
          700: '#4E4B43',
          800: '#33332E',
          900: '#1E2723',
        },
        // Repoint indigo to the pine accent so legacy utility classes stay coherent.
        indigo: {
          50: '#EEF4F0',
          100: '#DCE9E2',
          200: '#BCD4C8',
          300: '#93B8A7',
          400: '#669982',
          500: '#447D68',
          600: '#2E6353',
          700: '#234F43',
          800: '#1C3F36',
          900: '#16332C',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'Segoe UI', 'sans-serif'],
        display: ['"Instrument Serif"', 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', 'Georgia', 'serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'Consolas', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '4px',
        sm: '3px',
        md: '5px',
        lg: '7px',
        xl: '10px',
      },
    },
  },
  plugins: [],
}
